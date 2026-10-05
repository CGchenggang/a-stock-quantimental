"""R4-C tests: deterministic 76-stock research validation loop.

tmp_path-built fixtures (CI-offline). Locks the validation invariants:

A. frozen-universe loading (BOM-safe, order-insensitive identity);
B/I. completeness: missing symbols are REPORTED (DATA_INCOMPLETE), never
   silently skipped;
C. batch integration: R4-C calls the accepted run_research_batch;
D. stable ordering (normal / reversed / shuffled input -> identical);
E. deterministic replay (two runs -> identical results and manifest);
F. PIT boundary (later records never enter an earlier as_of run);
G. virgin protection (as_of >= VIRGIN_START fails fast per-target);
H. failure isolation (one FAILED target, the rest proceed);
J. no registry mutation (P13-Q/P13-R registries byte-identical).
"""
from __future__ import annotations

import hashlib
import json
import random

from astock_v2.agent.research_validation import (
    DEFAULT_UNIVERSE_FILE,
    load_universe,
    run_validation,
)
from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.information.raw_store import RawStore
from astock_v2.research_boundary import VIRGIN_START

INGESTED_AT = "2026-03-01T00:00:00+08:00"

_SYMBOLS = ("000001", "000333", "600519")
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
            raw_ref="d" * 64,
            quality="SOURCE_RETURNED",
        )
        for i, day in enumerate(_DAYS)
    ]


def _bases():
    return {"000001": 16.0, "000333": 21.0, "600519": 51.0}


def _environment(tmp_path, bases: dict):
    historical = LocalHistoricalStore(root=tmp_path / "data")
    rows = []
    for symbol, base in bases.items():
        rows.extend(_rows(symbol, base))
    historical.append_records("cn_stock_daily", rows)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    return historical, raw


# ------------------------------------------------------- A. universe loading

def test_universe_loading_bom_safe_and_order_insensitive(tmp_path):
    raw_file = tmp_path / "universe.txt"
    payload = "\ufeff600519\n000001\n\n000333\n600519\n"  # BOM + blank + dup
    raw_file.write_bytes(payload.encode("utf-8"))
    universe = load_universe(raw_file)
    assert universe["symbols"] == ["000001", "000333", "600519"]
    assert universe["universe_id"].startswith("universe-")
    # order-insensitive identity
    other = tmp_path / "reordered.txt"
    other.write_bytes("000333\n600519\n000001\n".encode("utf-8"))
    assert load_universe(other)["universe_id"] == universe["universe_id"]
    # the canonical frozen-universe path is declared (not read in CI)
    assert DEFAULT_UNIVERSE_FILE.as_posix() == \
        "data/industry/validation_universe_76.txt"


# --------------------------------------------- B + I. explicit completeness

def test_missing_symbols_reported_not_skipped(tmp_path):
    historical, raw = _environment(tmp_path, _bases())  # NO data for 000004
    result = run_validation(["000001", "000333", "600519", "000004"],
                            [AS_OF], historical_store=historical,
                            raw_store=raw, ingested_at=INGESTED_AT,
                            lookback=3)
    assert result["status"] == "DATA_INCOMPLETE"
    assert result["summary"]["expected"] == 4
    assert result["summary"]["observed"] == 3
    assert result["summary"]["missing_data"] == 1
    manifest = result["manifest"]
    assert manifest["completeness"]["missing"] == ["000004"]
    assert manifest["completeness"]["coverage"] == 0.75
    # the missing symbol still appears in the per-result identity as a
    # FAILED/empty target — never silently dropped from the record
    identities = manifest["per_result_identity"]
    assert {i["symbol"] for i in identities} == \
        {"000001", "000333", "600519", "000004"}


def test_complete_universe_is_ok(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    result = run_validation(_SYMBOLS, [AS_OF], historical_store=historical,
                            raw_store=raw, ingested_at=INGESTED_AT,
                            lookback=3)
    assert result["status"] == "OK"
    assert result["summary"] == {
        "expected": 3, "observed": 3, "total": 3, "ok": 3, "failed": 0,
        "missing_data": 0, "no_action": 3, "research": 0, "hold": 0}


# ------------------------------------------------- C. batch integration

def test_validation_calls_accepted_batch_runner(tmp_path, monkeypatch):
    import astock_v2.agent.research_validation as rv
    historical, raw = _environment(tmp_path, _bases())
    calls = []
    real = rv.run_research_batch

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(rv, "run_research_batch", spy)
    run_validation(list(_SYMBOLS), [AS_OF], historical_store=historical,
                   raw_store=raw, ingested_at=INGESTED_AT, lookback=3)
    assert len(calls) == 1
    assert calls[0][0][0] == sorted(_SYMBOLS)  # one call, sorted universe


# --------------------------------------------------- D. stable ordering

def test_ordering_normal_reversed_shuffled_identical(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    as_ofs = [AS_OF, "2020-01-09T16:00:00+08:00"]
    forward = run_validation(list(_SYMBOLS), as_ofs,
                             historical_store=historical, raw_store=raw,
                             ingested_at=INGESTED_AT, lookback=3)
    reversed_input = run_validation(list(reversed(_SYMBOLS)),
                                    list(reversed(as_ofs)),
                                    historical_store=historical,
                                    raw_store=raw,
                                    ingested_at=INGESTED_AT, lookback=3)
    shuffled = list(_SYMBOLS)
    random.Random(42).shuffle(shuffled)
    shuffled_input = run_validation(shuffled, as_ofs,
                                    historical_store=historical,
                                    raw_store=raw,
                                    ingested_at=INGESTED_AT, lookback=3)
    a = json.dumps(forward, sort_keys=True)
    assert a == json.dumps(reversed_input, sort_keys=True)
    assert a == json.dumps(shuffled_input, sort_keys=True)


# ---------------------------------------------- E. deterministic replay

def test_replay_identical_results_and_manifest(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    first = run_validation(list(_SYMBOLS) + ["000004"], [AS_OF],
                           historical_store=historical, raw_store=raw,
                           ingested_at=INGESTED_AT, lookback=3)
    second = run_validation(list(_SYMBOLS) + ["000004"], [AS_OF],
                            historical_store=historical, raw_store=raw,
                            ingested_at=INGESTED_AT, lookback=3)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["manifest"]["content_digest"] == \
        second["manifest"]["content_digest"]


# ------------------------------------------------------ F. PIT boundary

def test_pit_boundary_inside_validation(tmp_path):
    historical, raw = _environment(tmp_path, {"000001": 16.0})
    result = run_validation(["000001"],
                            ["2020-01-09T16:00:00+08:00", AS_OF],
                            historical_store=historical, raw_store=raw,
                            ingested_at=INGESTED_AT, lookback=3)
    by_as_of = {r["as_of"]: r for r in result["results"]}
    early = by_as_of["2020-01-09T16:00:00+08:00"]
    late = by_as_of[AS_OF]
    early_ids = set(early["evidence_ids"])
    late_ids = set(late["evidence_ids"])
    assert len(early_ids) == 6 and len(late_ids) == 8
    assert early_ids < late_ids  # strictly earlier horizon
    # the early run's manifest identity differs from the late one
    assert early["result_id"] != late["result_id"]


# ------------------------------------------------- G. virgin protection

def test_virgin_as_of_fails_fast_per_target(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    result = run_validation(_SYMBOLS, [f"{VIRGIN_START}T16:00:00+08:00"],
                            historical_store=historical, raw_store=raw,
                            ingested_at=INGESTED_AT, lookback=3)
    assert result["summary"]["failed"] == 3
    assert result["summary"]["ok"] == 0
    assert all(r["status"] == "FAILED" and r["error"]
               and ("virgin" in r["error"].lower()
                    or "research zone" in r["error"].lower())
               for r in result["results"])


# ------------------------------------------------- H. failure isolation

def test_failure_isolation_inside_validation(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    result = run_validation(_SYMBOLS,
                            [AS_OF, f"{VIRGIN_START}T16:00:00+08:00"],
                            historical_store=historical, raw_store=raw,
                            ingested_at=INGESTED_AT, lookback=3)
    assert result["summary"]["ok"] == 3
    assert result["summary"]["failed"] == 3
    ok_runs = [r for r in result["results"] if r["status"] == "OK"]
    failed = [r for r in result["results"] if r["status"] == "FAILED"]
    assert len(ok_runs) == 3 and len(failed) == 3
    assert all(r["bundle_id"] and r["record_id"] for r in ok_runs)


# ------------------------------------------------- J. no registry mutation

def _digest(path) -> str | None:
    path.is_file()
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_no_p13_registry_mutation(tmp_path):
    historical, raw = _environment(tmp_path, _bases())
    registry_files = [
        DEFAULT_UNIVERSE_FILE.parent / "p13q" / "calibration_registry.json",
        DEFAULT_UNIVERSE_FILE.parent / "p13r" / "decision_policy_registry.json",
    ]
    before = {str(p): _digest(p) for p in registry_files}
    run_validation(_SYMBOLS, [AS_OF], historical_store=historical,
                   raw_store=raw, ingested_at=INGESTED_AT, lookback=3)
    after = {str(p): _digest(p) for p in registry_files}
    assert before == after
    # and the validation surface never references the registries at all
    source = (DEFAULT_UNIVERSE_FILE.parent.parent.parent
              / "src" / "astock_v2" / "agent" / "research_validation.py")
    if source.is_file():  # present in the repo checkout; tmp fixtures only on CI
        text = source.read_text(encoding="utf-8")
        assert "calibration_registry" not in text
        assert "decision_policy_registry" not in text
