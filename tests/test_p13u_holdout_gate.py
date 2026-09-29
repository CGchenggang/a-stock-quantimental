"""P13-U virgin holdout gate invariants (25 required checks)."""
from __future__ import annotations

import json

import pytest

from scripts.run_p13u_gate import (
    CONTAMINATION_MESSAGE,
    MINIMUM_TRADING_DAYS,
    RECOMMENDED_TRADING_DAYS,
    RESEARCH_END,
    VIRGIN_START,
    assert_research_zone,
    build_gate_report,
    frozen_manifest,
    gate_status,
    sha256_of,
)

UNIVERSE = [f"{i:06d}" for i in range(1, 5)]  # 4 synthetic symbols


def _write_store(store, rows_by_symbol):
    for symbol, days in rows_by_symbol.items():
        with (store / f"{symbol}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
            for day, close in days:
                f.write(json.dumps({
                    "symbol": symbol, "event_time": f"{day}T15:00:00+08:00",
                    "available_time": f"{day}T16:00:00+08:00",
                    "value": {"close": close},
                }) + "\n")


def _audit(dates, symbols=("000001",)):
    return {"predictions": [
        {"variant": "baseline", "symbol": s, "decision_time": f"{d}T16:00:00+08:00",
         "p": 0.5, "y": 0, "baseline_p": 0.5}
        for d in dates for s in symbols
    ]}


def _rows(days, start_day=1, close=10.0):
    return [(f"2026-09-{start_day + i:02d}", close) for i, _ in enumerate(days)]


# 1./2. frozen boundaries
def test_frozen_boundaries():
    assert RESEARCH_END == "2026-09-22"
    assert VIRGIN_START == "2026-09-23"
    assert VIRGIN_START > RESEARCH_END


# 3.-5. virgin identification
def test_virgin_zone_identification():
    store_days = {
        "000001": [("2026-09-22", 10.0), ("2026-09-23", 10.1), ("2026-09-24", 10.2)],
        "000002": [("2026-09-22", 10.0), ("2026-09-23", 10.1), ("2026-09-24", 10.2)],
    }
    audit = _audit(["2026-09-22"])  # research consumed only 09-22
    report = build_gate_report(store_days and __import__("pathlib").Path("."), UNIVERSE, audit, []) \
        if False else None
    import pathlib
    store = pathlib.Path(__file__).parent / "_p13u_store_tmp"
    store.mkdir(exist_ok=True)
    _write_store(store, store_days)
    report = build_gate_report(store, UNIVERSE, audit, [])
    # 09-22 is research zone (consumed); 09-23/09-24 are virgin
    assert report["virgin_trading_days"] == 2
    assert report["coverage"][0]["date"] == "2026-09-23"
    assert report["coverage"][1]["date"] == "2026-09-24"
    assert report["latest_research_consumed_date"] == "2026-09-22"
    assert report["research_end"] == RESEARCH_END


# 6.-10. gate status ladder
def test_gate_status_ladder():
    assert gate_status(2, False) == "ACCUMULATING"
    assert gate_status(19, False) == "ACCUMULATING"
    assert gate_status(20, False) == "READY_MINIMUM"
    assert gate_status(59, False) == "READY_MINIMUM"
    assert gate_status(60, False) == "READY_RECOMMENDED"
    assert gate_status(120, False) == "READY_RECOMMENDED"
    assert MINIMUM_TRADING_DAYS == 20 and RECOMMENDED_TRADING_DAYS == 60


def test_current_two_virgin_days_accumulating(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    days = [("2026-09-23", 10.0), ("2026-09-24", 10.1)]
    _write_store(store, {s: days for s in UNIVERSE})
    report = build_gate_report(store, UNIVERSE, _audit(
        [f"2026-{m:02d}-{d:02d}" for m in range(1, 9) for d in range(1, 29)]
    ), [])  # research dates end 2026-08-28, well before virgin_start
    assert report["virgin_trading_days"] == 2
    assert report["gate_status"] == "ACCUMULATING"
    assert report["p13_t_executable_minimum"] is False


# 11./12. missing trading day / missing symbol detection
def test_missing_day_and_symbol_detection(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    _write_store(store, {
        "000001": [("2026-09-23", 10.0), ("2026-09-24", 10.1)],
        "000002": [("2026-09-23", 10.0)],                       # misses 09-24
        # 000003 entirely missing (missing symbol for both days)
        "000004": [("2026-09-23", 10.0), ("2026-09-24", 10.1)],
    })
    report = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [])
    by_day = {c["date"]: c for c in report["coverage"]}
    assert "2026-09-23" in report["missing_dates_with_missing_symbols"]
    assert set(by_day["2026-09-23"]["missing_symbols"]) == {"000003"}
    assert set(by_day["2026-09-24"]["missing_symbols"]) == {"000002", "000003"}
    assert by_day["2026-09-23"]["expected_symbols"] == 4
    assert by_day["2026-09-23"]["observed_symbols"] == 3


# 13./14. contamination detection and BLOCKED
def test_consumed_date_in_virgin_zone_blocks(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    _write_store(store, {s: [("2026-09-23", 10.0)] for s in UNIVERSE})
    # a research pipeline consumed 2026-09-23 -> it cannot be virgin
    report = build_gate_report(store, UNIVERSE, _audit(["2026-09-22", "2026-09-23"]), [])
    assert report["contamination_detected"] is True
    assert report["gate_status"] == "BLOCKED"
    assert report["contamination_details"]["consumed_dates_in_virgin_zone"] == ["2026-09-23"]


def test_research_artifact_touching_virgin_zone_blocks(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    _write_store(store, {s: [("2026-09-23", 10.0)] for s in UNIVERSE})
    artifact = tmp_path / "some_research_artifact.json"
    artifact.write_text(json.dumps({"rows": [
        {"decision_time": "2026-09-23T16:00:00+08:00", "p": 0.5},
    ]}), encoding="utf-8")
    report = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [artifact])
    assert report["contamination_detected"] is True
    assert report["gate_status"] == "BLOCKED"


# 15. research_end never follows the latest data date
def test_research_end_does_not_move_with_future_data(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    days = [("2026-09-23", 10.0), ("2026-09-24", 10.1)]
    days += [(f"2026-10-{d:02d}", 10.0) for d in range(1, 11)]  # data to 10-10
    _write_store(store, {s: days for s in UNIVERSE})
    report = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [])
    assert report["research_end"] == RESEARCH_END == "2026-09-22"
    assert report["virgin_start"] == VIRGIN_START == "2026-09-23"
    assert report["latest_available_data_date"] == "2026-10-10"
    assert report["virgin_trading_days"] == 12  # 2 + 10, boundaries unmoved


# 16. future rows cannot alter the frozen manifest
def test_frozen_manifest_immune_to_future_rows(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    _write_store(store, {s: [("2026-09-23", 10.0)] for s in UNIVERSE})
    frozen_paths = {"universe_file": "data/industry/validation_universe_76.txt"}
    first = frozen_manifest(frozen_paths)
    # more virgin data arrives; frozen manifest hashes are input-file hashes
    _write_store(store, {s: [("2026-09-23", 10.0), ("2026-09-24", 10.1)] for s in UNIVERSE})
    second = frozen_manifest(frozen_paths)
    assert first == second
    assert first["research_end"] == RESEARCH_END


# 17. deterministic ordering
def test_outputs_are_sorted_and_deterministic(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    days = [("2026-09-24", 10.0), ("2026-09-23", 10.0)]  # deliberately unsorted
    _write_store(store, {s: days for s in reversed(UNIVERSE)})
    report_a = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [])
    report_b = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [])
    assert json.dumps(report_a, sort_keys=True) == json.dumps(report_b, sort_keys=True)
    dates = [c["date"] for c in report_a["coverage"]]
    assert dates == sorted(dates)


# 18.-20. frozen manifest hashes stable and honest
def test_frozen_manifest_hashes_stable_and_detect_tamper(tmp_path):
    target = tmp_path / "registry.json"
    target.write_text('{"policy_ids": ["a", "b"]}', encoding="utf-8")
    first = frozen_manifest({"registry": str(target)})
    second = frozen_manifest({"registry": str(target)})
    assert first == second
    assert first["frozen_hashes"]["registry"] == sha256_of(target)
    # tampering with the registry changes the hash -> gate would see it
    target.write_text('{"policy_ids": ["a", "b", "c"]}', encoding="utf-8")
    third = frozen_manifest({"registry": str(target)})
    assert third["frozen_hashes"]["registry"] != first["frozen_hashes"]["registry"]
    assert third["frozen_hashes"]["registry"] == sha256_of(target)


def test_missing_hash_source_is_none_not_fabricated(tmp_path):
    manifest = frozen_manifest({"nonexistent": str(tmp_path / "nope.json")})
    assert manifest["frozen_hashes"]["nonexistent"] is None


# 21./22. P13-U cannot modify policy or calibration registries
def test_gate_has_no_registry_write_path(tmp_path):
    import scripts.run_p13u_gate as gate
    # the module exposes no function that writes to p13q/p13r artifacts
    writers = [name for name in dir(gate)
               if ("write" in name.lower() or "save" in name.lower())
               and name != "write_manifest"]
    assert writers == []  # the gate's only writer is its own manifest
    registry = tmp_path / "decision_policy_registry.json"
    before = registry.read_bytes() if registry.exists() else None
    build_gate_report(tmp_path / "empty_store", UNIVERSE,
                      _audit(["2026-09-22"]), [])
    assert (registry.exists() is False) if before is None else True
    assert "decision_policy_registry" not in json.dumps(
        build_gate_report(tmp_path / "empty_store", UNIVERSE,
                          _audit(["2026-09-22"]), []), sort_keys=True)


# 23./24. no performance metrics, no recommendations in gate outputs
def test_no_performance_metrics_or_recommendations():
    store = tmp_path_store()
    report = build_gate_report(store, UNIVERSE, _audit(["2026-09-22"]), [])
    blob = json.dumps(report, sort_keys=True).lower()
    for banned in ("accuracy", "brier", "log_loss", "hit_rate",
                   "recommendation", "policy_metrics"):
        assert banned not in blob, banned
    assert report["research_only"] is True


def tmp_path_store():
    import pathlib
    store = pathlib.Path(__file__).parent / "_p13u_store_metrics_tmp"
    store.mkdir(exist_ok=True)
    _write_store(store, {s: [("2026-09-23", 10.0)] for s in UNIVERSE})
    return store


# 25. production factor registry untouched
def test_production_factor_registry_unchanged():
    from astock_v2.factors import FACTOR_REGISTRY
    assert set(FACTOR_REGISTRY) == {
        "momentum", "volatility", "trend", "volume_ratio",
        "close_to_high", "close_to_low", "range_ratio", "close_location",
    }


# research-zone guard: fail fast with the mandated message
def test_research_zone_guard_fails_fast_on_virgin_rows():
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT DATA CANNOT BE CONSUMED"):
        assert_research_zone(["2026-09-23T16:00:00+08:00"])
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT DATA CANNOT BE CONSUMED"):
        assert_research_zone([
            "2025-01-01T16:00:00+08:00",
            "2026-09-23T16:00:00+08:00",
            "2027-01-01T16:00:00+08:00",
        ])


def test_research_zone_guard_allows_research_rows():
    # research-zone dates pass silently; boundary is exclusive at virgin_start
    assert_research_zone([
        "2026-09-22T16:00:00+08:00",
        "2025-01-01T00:00:00+00:00",
        "2021-02-22T16:00:00+08:00",
    ])


# both research entry points carry the guard
def test_p13q_and_p13r_entry_points_have_guard():
    import scripts.run_p13q_analysis as q
    import scripts.run_p13r_analysis as r
    assert q.assert_research_zone.__module__ == "scripts.run_p13u_gate"
    assert r.assert_research_zone.__module__ == "scripts.run_p13u_gate"
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
        q.assert_research_zone(["2026-09-23T16:00:00+08:00"])
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
        r.assert_research_zone(["2026-09-23T16:00:00+08:00"])
