"""R4-B tests: deterministic Research Agent Batch Runner.

tmp_path-built fixtures (CI-offline). Locks the batch invariants:

A. multi-symbol batch -> independent results;
B. symbol isolation inside a batch;
C. PIT isolation across as_ofs (later data never enters an earlier run);
D. deterministic replay (byte-identical batch);
E. stable ordering (input order and duplicates cannot change the batch);
F. failure isolation (one FAILED target recorded with its error, the rest
   of the batch proceeds — the honest virgin-zone fail-fast as trigger);
G. evidence/ledger continuity (each OK result keeps the R4-A chain into
   the existing ledger).
"""
from __future__ import annotations

import json

from astock_v2.agent.research_batch import (
    append_batch_to_ledger,
    run_research_batch,
)
from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.information.raw_store import RawStore
from astock_v2.ledger import RecommendationLedger
from astock_v2.research_boundary import VIRGIN_START

INGESTED_AT = "2026-03-01T00:00:00+08:00"

_SYMBOLS = ("000001", "000333", "600519")

# 8 trading days per symbol is enough for lookback=3 factor computation
_DAYS = [
    "2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07",
    "2020-01-08", "2020-01-09", "2020-01-10", "2020-01-13",
]

AS_OF = "2020-01-13T16:00:00+08:00"


def _rows(symbol: str, base: float):
    return [
        HistoricalRecord(
            symbol=symbol,
            event_time=f"{day}T15:00:00+08:00",
            available_time=f"{day}T16:00:00+08:00",
            source="akshare:stock_zh_a_hist_tx",
            source_type="historical_vendor",
            value={"date": day, "open": base + i * 0.02,
                   "close": base + i * 0.05, "high": base + i * 0.05 + 0.1,
                   "low": base + i * 0.05 - 0.1,
                   "volume": 1_000_000.0 + i, "amount": None, "adjust": ""},
            layer=DataLayer.CLEAN,
            asset_scope=AssetScope.CN_STOCK,
            revision=0,
            raw_ref="c" * 64,
            quality="SOURCE_RETURNED",
        )
        for i, day in enumerate(_DAYS)
    ]


def _environment(tmp_path, bases: dict[str, float]):
    historical = LocalHistoricalStore(root=tmp_path / "data")
    rows = []
    for symbol, base in bases.items():
        rows.extend(_rows(symbol, base))
    historical.append_records("cn_stock_daily", rows)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    return historical, raw


def _bases() -> dict[str, float]:
    return {"000001": 16.0, "000333": 21.0, "600519": 51.0}


# ------------------------------------------------------------------- A. batch

def test_multi_symbol_batch(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    batch = run_research_batch(_SYMBOLS, [AS_OF], historical_store=historical,
                               raw_store=raw, ingested_at=INGESTED_AT,
                               lookback=3)
    assert batch["summary"]["targets"] == 3
    assert batch["summary"]["ok"] == 3
    assert batch["summary"]["failed"] == 0
    assert batch["batch_id"]
    assert [r["symbol"] for r in batch["results"]] == sorted(_SYMBOLS)
    for r in batch["results"]:
        assert r["status"] == "OK"
        assert r["run"]["counts"]["visible"] == 8
        assert len(r["run"]["evidence"]) == 8
        assert r["run"]["factors"]["momentum"]["value"] is not None
    # per-symbol research independence: different closes -> different runs
    run_ids = {r["run"]["run_id"] for r in batch["results"]}
    assert len(run_ids) == 3
    assert batch["summary"]["actions"] == {"NO_ACTION": 3}


# ---------------------------------------------------------- B. symbol isolation

def test_symbol_isolation_in_batch(tmp_path):
    bases = _bases()
    bases["000999"] = 99.0  # a fourth symbol that is NOT in the batch
    historical, raw = _environment(tmp_path, bases)
    batch = run_research_batch(_SYMBOLS, [AS_OF], historical_store=historical,
                               raw_store=raw, ingested_at=INGESTED_AT,
                               lookback=3)
    assert batch["summary"]["ok"] == 3
    for r in batch["results"]:
        symbol = r["symbol"]
        assert all(e["source_id"].startswith(f"{symbol}:")
                   for e in r["run"]["evidence"])
        assert all(sid.startswith(f"{symbol}:")
                   for sid in r["run"]["factor_input_source_ids"])


# --------------------------------------------------------------- C. PIT isolation

def test_pit_isolation_across_as_ofs(tmp_path):
    historical, raw = _environment(tmp_path, {"000001": 16.0})
    # two as_ofs: the later run sees two more bars; the earlier run must
    # not see any of them
    batch = run_research_batch(["000001"],
                               ["2020-01-09T16:00:00+08:00", AS_OF],
                               historical_store=historical, raw_store=raw,
                               ingested_at=INGESTED_AT, lookback=3)
    assert batch["summary"]["targets"] == 2
    by_as_of = {r["as_of"]: r["run"] for r in batch["results"]}
    early = by_as_of["2020-01-09T16:00:00+08:00"]
    late = by_as_of[AS_OF]
    assert early["counts"]["visible"] == 6
    assert late["counts"]["visible"] == 8
    # the decisive assertion: the early run's inputs end at its own horizon
    assert max(early["factor_input_source_ids"]) < max(
        late["factor_input_source_ids"])
    early_excluded = {e["source_id"] for e in early["exclusions"]
                      if e["reason"] == "NOT_YET_AVAILABLE"}
    assert early_excluded == {"000001:2020-01-10T15:00:00+08:00",
                              "000001:2020-01-13T15:00:00+08:00"}


# ------------------------------------------------------------------- D. replay

def test_batch_replay_is_byte_identical(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    first = run_research_batch(_SYMBOLS, [AS_OF], historical_store=historical,
                               raw_store=raw, ingested_at=INGESTED_AT,
                               lookback=3)
    second = run_research_batch(_SYMBOLS, [AS_OF], historical_store=historical,
                                raw_store=raw, ingested_at=INGESTED_AT,
                                lookback=3)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ----------------------------------------------------------- E. stable ordering

def test_batch_ordering_is_stable(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    forward = run_research_batch(_SYMBOLS, [AS_OF],
                                 historical_store=historical, raw_store=raw,
                                 ingested_at=INGESTED_AT, lookback=3)
    reversed_input = run_research_batch(list(reversed(_SYMBOLS)), [AS_OF],
                                        historical_store=historical,
                                        raw_store=raw,
                                        ingested_at=INGESTED_AT, lookback=3)
    assert json.dumps(forward, sort_keys=True) == json.dumps(
        reversed_input, sort_keys=True)
    assert [r["symbol"] for r in forward["results"]] == sorted(_SYMBOLS)
    # duplicated targets are deduplicated
    dup = run_research_batch(["000001", "000001"], [AS_OF, AS_OF],
                             historical_store=historical, raw_store=raw,
                             ingested_at=INGESTED_AT, lookback=3)
    assert dup["summary"]["targets"] == 1


# -------------------------------------------------------- F. failure isolation

def test_failure_isolation(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    # the middle target's as_of is inside the protected virgin zone —
    # the accepted guard fails that run fast; A and C must proceed
    targets_symbols = ["000001", "000333", "600519"]
    batch = run_research_batch(targets_symbols,
                               [AS_OF, f"{VIRGIN_START}T16:00:00+08:00"],
                               historical_store=historical, raw_store=raw,
                               ingested_at=INGESTED_AT, lookback=3)
    by_symbol = {}
    for r in batch["results"]:
        by_symbol.setdefault(r["symbol"], []).append(r)
    assert batch["summary"]["ok"] == 3
    assert batch["summary"]["failed"] == 3
    failed = [r for r in batch["results"] if r["status"] == "FAILED"]
    assert len(failed) == 3
    assert all("virgin" in r["error"].lower() or "research zone" in r["error"].lower()
               for r in failed)
    # the failed target is recorded explicitly — never silently dropped
    virgin_failed = [r for r in by_symbol["000333"]
                     if r["status"] == "FAILED"]
    assert len(virgin_failed) == 1
    assert virgin_failed[0]["run"] is None
    assert virgin_failed[0]["error"]
    # the valid targets are unaffected
    for r in batch["results"]:
        if r["status"] == "OK":
            assert r["run"]["counts"]["visible"] == 8


# ---------------------------------------------------------- G. ledger continuity

def test_batch_ledger_continuity(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    batch = run_research_batch(_SYMBOLS, [AS_OF], historical_store=historical,
                               raw_store=raw, ingested_at=INGESTED_AT,
                               lookback=3)
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    events = append_batch_to_ledger(batch, ledger, INGESTED_AT)
    assert len(events) == 3
    loaded = ledger.load()
    assert len(loaded) == 3
    by_record = {row["record_id"]: row for row in loaded}
    for r in batch["results"]:
        record_id = r["run"]["recommendation"]["record_id"]
        row = by_record[record_id]
        assert row["symbol"] == r["symbol"]
        assert row["decision_time"] == r["as_of"]
        assert (row["input_snapshot"]["bundle_id"]
                == r["run"]["bundle_id"])
        assert len(row["input_snapshot"]["evidence_ids"]) == 8
    # a FAILED target appends nothing: only 3 rows exist for 3 OK targets
    assert sum(1 for row in loaded) == batch["summary"]["ok"]


def test_empty_batch(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    batch = run_research_batch([], [AS_OF], historical_store=historical,
                               raw_store=raw, ingested_at=INGESTED_AT)
    assert batch["summary"]["targets"] == 0
    assert batch["results"] == []
    assert batch["batch_id"]
