"""R4-A tests: the first evidence-backed Research Agent Loop.

High-value coverage only (tmp_path-built fixtures, CI-offline):

A. End-to-end: historical adapter -> P14-B -> P14-D -> P14-E -> packet
   -> research result -> ledger.
B. PIT: post-availability data is invisible and carried as exclusions;
   the inclusive boundary holds.
C. Evidence: every factor input traces to a P14-E evidence record and the
   recommendation carries the evidence identity.
D. Replay: identical (symbol, as_of, store) -> byte-identical run.
E. Symbol isolation: one run cannot see another symbol's rows.
F. Honest labeling: probability NOT_AVAILABLE, regime UNKNOWN, action
   never BUY/SELL; virgin-zone as_of fails fast.
"""
from __future__ import annotations

import json

import pytest

from astock_v2.agent.research_run import append_to_ledger, run_research
from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.ledger import RecommendationLedger
from astock_v2.research_boundary import VIRGIN_START

INGESTED_AT = "2026-03-01T00:00:00+08:00"

# 25 consecutive trading days so the default 20-lookback factors compute
_DAYS = [
    "2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08",
    "2020-01-09", "2020-01-10", "2020-01-13", "2020-01-14", "2020-01-15",
    "2020-01-16", "2020-01-17", "2020-01-20", "2020-01-21", "2020-01-22",
    "2020-01-23", "2020-02-03", "2020-02-04", "2020-02-05", "2020-02-06",
    "2020-02-07", "2020-02-10", "2020-02-11", "2020-02-12", "2020-02-13",
]


def _rows(symbol="000001", base=16.0, step=0.05):
    return [
        HistoricalRecord(
            symbol=symbol,
            event_time=f"{day}T15:00:00+08:00",
            available_time=f"{day}T16:00:00+08:00",
            source="akshare:stock_zh_a_hist_tx",
            source_type="historical_vendor",
            value={"date": day, "open": base + i * step - 0.05,
                   "close": base + i * step, "high": base + i * step + 0.1,
                   "low": base + i * step - 0.1, "volume": 1_000_000.0 + i,
                   "amount": None, "adjust": ""},
            layer=DataLayer.CLEAN,
            asset_scope=AssetScope.CN_STOCK,
            revision=0,
            raw_ref="b" * 64,
            quality="SOURCE_RETURNED",
        )
        for i, day in enumerate(_DAYS)
    ]


def _environment(tmp_path, rows):
    historical = LocalHistoricalStore(root=tmp_path / "data")
    historical.append_records("cn_stock_daily", rows)
    from astock_v2.information.raw_store import RawStore
    raw = RawStore(tmp_path / "raw_records.jsonl")
    return historical, raw


AS_OF = "2020-02-13T16:00:00+08:00"  # last day's declared availability


# ------------------------------------------------------------------- A. E2E

def test_end_to_end_research_run(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    result = run_research("000001", AS_OF, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    # the full chain produced accepted identities
    assert result["counts"]["visible"] == 25
    assert result["counts"]["excluded"] == 0
    assert len(result["evidence"]) == 25
    assert result["bundle_id"] and result["result_id"]
    # factors computed from the visible window
    assert result["factors"]["momentum"]["value"] is not None
    assert result["factors"]["volatility"]["value"] is not None
    assert result["factors"]["momentum"]["observation_count"] == 25
    # honest upstream labeling
    assert result["probability"]["status"] == "NOT_AVAILABLE"
    assert result["regime"]["regime"] == "UNKNOWN"
    # the conservative decision rule: uncalibrated -> RESEARCH, no BUY/SELL
    assert result["research_state"]["decision_class"] == "RESEARCH"
    assert result["recommendation"]["action"] == "NO_ACTION"
    assert result["recommendation"]["action"] not in {"BUY", "SELL"}


def test_ledger_integration_and_replay_hook(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    result = run_research("000001", AS_OF, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    event = append_to_ledger(result, ledger, INGESTED_AT)
    assert event["record_id"] == result["recommendation"]["record_id"]
    loaded = ledger.load()
    assert len(loaded) == 1
    row = loaded[0]
    assert row["symbol"] == "000001"
    assert row["decision_time"] == AS_OF
    # evidence identity is preserved in the ledger for later replay/review
    assert row["input_snapshot"]["bundle_id"] == result["bundle_id"]
    assert row["input_snapshot"]["result_id"] == result["result_id"]
    assert len(row["input_snapshot"]["evidence_ids"]) == 25


# ------------------------------------------------------------------- B. PIT

def test_pit_future_data_is_excluded_and_recorded(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    # as_of one day earlier: the last day must be invisible AND recorded
    as_of = "2020-02-12T16:00:00+08:00"
    result = run_research("000001", as_of, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    assert result["counts"]["visible"] == 24
    visible_ids = set(result["factor_input_source_ids"])
    future_id = "000001:2020-02-13T15:00:00+08:00"
    assert future_id not in visible_ids
    excluded = [(e["source_id"], e["reason"]) for e in result["exclusions"]]
    assert ("000001:2020-02-13T15:00:00+08:00", "NOT_YET_AVAILABLE") in excluded


def test_pit_inclusive_boundary_and_pre_availability(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    # available at 16:00 sharp -> visible at exactly 16:00
    result = run_research("000001", "2020-01-02T16:00:00+08:00",
                          historical_store=historical, raw_store=raw,
                          ingested_at=INGESTED_AT, lookback=3)
    assert result["counts"]["visible"] == 1
    # 15:30 same day: the bar exists (event 15:00) but is NOT yet available
    result = run_research("000001", "2020-01-02T15:30:00+08:00",
                          historical_store=historical, raw_store=raw,
                          ingested_at=INGESTED_AT, lookback=3)
    assert result["counts"]["visible"] == 0
    assert result["recommendation"]["action"] == "NO_ACTION"


# -------------------------------------------------------------- C. Evidence

def test_evidence_traceability(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    result = run_research("000001", AS_OF, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    evidence_ids = {e["evidence_id"] for e in result["evidence"]}
    # every factor input IS an evidence record
    assert set(result["factor_input_source_ids"]) <= {
        e["source_id"] for e in result["evidence"]}
    assert len(result["evidence_ids"]) == len(evidence_ids)
    # each evidence carries the full provenance chain
    for e in result["evidence"]:
        assert e["source"] == "cn_stock_quote"
        assert e["raw_payload_hash"] and e["ingestion_id"]
        assert e["available_time"] <= AS_OF
    # the recommendation carries the evidence identity (ledger-ready)
    provenance = result["recommendation"]["provenance"]
    assert f"bundle_id:{result['bundle_id']}" in provenance
    assert f"result_id:{result['result_id']}" in provenance


# ---------------------------------------------------------------- D. Replay

def test_replay_same_store_is_byte_identical(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    first = run_research("000001", AS_OF, historical_store=historical,
                         raw_store=raw, ingested_at=INGESTED_AT)
    # second run: ingestion replays as DUPLICATE, research identity identical
    second = run_research("000001", AS_OF, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_replay_across_independent_stores(tmp_path):
    rows = _rows()
    historical_a, raw_a = _environment(tmp_path / "a", rows)
    historical_b, raw_b = _environment(tmp_path / "b", rows)
    first = run_research("000001", AS_OF, historical_store=historical_a,
                         raw_store=raw_a, ingested_at=INGESTED_AT)
    second = run_research("000001", AS_OF, historical_store=historical_b,
                          raw_store=raw_b, ingested_at=INGESTED_AT)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ------------------------------------------------------- E. Symbol isolation

def test_symbol_isolation(tmp_path):
    rows = _rows() + _rows(symbol="000002", base=11.0)
    historical, raw = _environment(tmp_path, rows)
    from astock_v2.information.adapters import CNStockQuoteHistoricalAdapter
    # BOTH symbols are ingested into P14-B; the 000001 run must still
    # isolate against the other symbol's data
    CNStockQuoteHistoricalAdapter(
        historical, symbols=["000002"],
        ingested_at=INGESTED_AT).ingest(raw, INGESTED_AT)
    result = run_research("000001", AS_OF, historical_store=historical,
                          raw_store=raw, ingested_at=INGESTED_AT)
    assert result["counts"]["examined"] == 50
    assert result["counts"]["visible"] == 25
    assert all(e["source_id"].startswith("000001:")
               for e in result["evidence"])
    assert all(sid.startswith("000001:")
               for sid in result["factor_input_source_ids"])
    # the other symbol is examined and honestly excluded as out-of-scope
    # (P14-D exclusion accounting) — it never reaches evidence or inputs
    reasons: dict[str, list[str]] = {}
    for x in result["exclusions"]:
        reasons.setdefault(x["reason"], []).append(x["source_id"])
    assert set(reasons) == {"OUTSIDE_AS_OF"}
    assert all(sid.startswith("000002:") for sid in reasons["OUTSIDE_AS_OF"])


# ------------------------------------------------------- boundary + honesty

def test_virgin_zone_as_of_fails_fast(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    with pytest.raises(ValueError, match="virgin|VIRGIN|research zone"):
        run_research("000001", f"{VIRGIN_START}T16:00:00+08:00",
                     historical_store=historical, raw_store=raw,
                     ingested_at=INGESTED_AT)


def test_empty_visible_window_is_honest_no_action(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    result = run_research("000001", "2019-12-31T16:00:00+08:00",
                          historical_store=historical, raw_store=raw,
                          ingested_at=INGESTED_AT)
    assert result["counts"]["visible"] == 0
    assert result["counts"]["excluded"] == 25
    assert result["evidence"] == []
    assert result["factors"]["momentum"]["value"] is None
    assert result["research_state"]["decision_class"] == "NO_ACTION"


def test_ingested_at_required_for_ingestion(tmp_path):
    historical, raw = _environment(tmp_path, _rows())
    with pytest.raises(ValueError, match="ingested_at"):
        run_research("000001", AS_OF, historical_store=historical,
                     raw_store=raw, ingested_at=None)


def test_run_against_pre_ingested_store(tmp_path):
    # the raw store may already contain the data (ingestion done earlier);
    # the loop must work without a historical store and stay deterministic
    historical, raw = _environment(tmp_path, _rows())
    run_research("000001", AS_OF, historical_store=historical,
                 raw_store=raw, ingested_at=INGESTED_AT)
    result = run_research("000001", AS_OF, raw_store=raw)
    expected = run_research("000001", AS_OF, historical_store=historical,
                            raw_store=raw, ingested_at=INGESTED_AT)
    assert result["run_id"] == expected["run_id"]
    assert result["recommendation"] == expected["recommendation"]
