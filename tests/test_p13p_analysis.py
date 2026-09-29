"""P13-P analysis invariants: alignment, split boundaries, reproducibility."""
from __future__ import annotations

import json

import pytest

from scripts.run_p13p_analysis import (
    BOOTSTRAP_ROUNDS,
    REGISTRY_STATUSES,
    SEED,
    SPLIT_DATE,
    AuditRow,
    _bootstrap_incremental,
    build_rows,
    quintile_edges,
    quintile_of,
    quintile_table,
    run_model,
    run_single_factor_audit,
    split_rows,
)
from scripts.run_local_industry_relative_oos import STOCK_FACTORS


def _decision_time(day_index: int) -> str:
    """Deterministic weekday-skipping decision timestamps from 2021-01-04."""
    from datetime import date, timedelta

    day = date(2021, 1, 4)
    added = 0
    while added < day_index:
        day += timedelta(days=1)
        if day.weekday() < 5:
            added += 1
    return f"{day.isoformat()}T16:00:00+08:00"


def _synth_rows(symbol: str, n_days: int = 310) -> list[tuple[AuditRow, dict]]:
    rows = []
    for i in range(n_days):
        dt = _decision_time(i)
        label = 1 if (i * 7 + len(symbol)) % 3 == 0 else 0
        factors = {
            "momentum": 0.01 * ((i % 11) - 5),
            "volatility": 0.1 + 0.02 * (i % 13),
            "trend": -0.05 + 0.01 * (i % 9),
            "volume_ratio": 0.2 * ((i % 5) - 2),
            "industry_relative_return_5": 0.001 * ((i % 7) - 3),
            "industry_relative_return_20": -0.002 * ((i % 6) - 3),
            "label": label,
            "next_return": 0.0005 * ((i % 4) - 2),
        }
        rows.append((AuditRow(decision_time=dt, label=label), factors))
    return rows


def _synth_rows_by_symbol(n_days: int = 310):
    return {
        "000001": _synth_rows("000001", n_days),
        "000002": _synth_rows("000002", n_days),
    }


def test_single_factor_models_share_identical_oos_rows():
    rows_by_symbol = _synth_rows_by_symbol()
    base = run_model(rows_by_symbol, STOCK_FACTORS)
    plus = run_model(rows_by_symbol, STOCK_FACTORS + ("volatility",))
    assert [(s, dt, y) for s, dt, _, y, _ in base] == [
        (s, dt, y) for s, dt, _, y, _ in plus
    ]
    # and the pooled row count matches the walk-forward arithmetic
    n_days = len(rows_by_symbol["000001"])
    expected_windows = (n_days - 252 - 1) // 20
    assert len(base) == 2 * expected_windows * 20


def test_quintile_edges_and_tables_are_reproducible():
    values = [((i * 37) % 101) / 101.0 for i in range(500)]
    edges_a = quintile_edges(values)
    edges_b = quintile_edges(values)
    assert edges_a == edges_b
    enriched = [(v, i % 2, 0.001 * i) for i, v in enumerate(values)]
    table_a = quintile_table(enriched, edges_a)
    table_b = quintile_table(enriched, edges_b)
    assert table_a == table_b
    # equal-frequency edges put ~100 rows per bucket and every row in range
    assert sum(q["n"] for q in table_a) == len(enriched)
    assert all(90 <= q["n"] <= 110 for q in table_a)
    assert quintile_of(values[0], edges_a) == quintile_of(values[0], edges_a)


def test_temporal_split_is_deterministic_and_boundary_goes_to_validation():
    rows = _synth_rows("000001", 310)
    # an explicit boundary row: 2025-01-01 belongs to validation
    boundary = AuditRow(decision_time=f"{SPLIT_DATE}T16:00:00+08:00", label=0)
    boundary_entry = {"volatility": 0.3, "label": 0, "next_return": 0.0}
    rows.append((boundary, boundary_entry))
    discovery, validation = split_rows(rows)
    assert all(r[0].decision_time[:10] < SPLIT_DATE for r in discovery)
    assert all(r[0].decision_time[:10] >= SPLIT_DATE for r in validation)
    assert any(r[0].decision_time[:10] == SPLIT_DATE for r in validation)
    discovery2, validation2 = split_rows(rows)
    assert discovery == discovery2 and validation == validation2
    # no overlap and full coverage
    assert len(discovery) + len(validation) == len(rows)


def test_bootstrap_incremental_is_seed_reproducible():
    rows_by_symbol = _synth_rows_by_symbol()
    preds_a = run_model(rows_by_symbol, STOCK_FACTORS)
    preds_b = run_model(rows_by_symbol, STOCK_FACTORS + ("volatility",))
    first = _bootstrap_incremental(rows_by_symbol, {"A_baseline": preds_a,
                                                    "B_baseline_plus_volatility": preds_b})
    second = _bootstrap_incremental(rows_by_symbol, {"A_baseline": preds_a,
                                                     "B_baseline_plus_volatility": preds_b})
    assert first == second
    assert first["seed"] == SEED and first["rounds"] == BOOTSTRAP_ROUNDS
    # the point estimate must be the exact deterministic delta, not a sample
    for metric in ("delta_accuracy", "delta_brier", "delta_log_loss"):
        point = first[metric]["point"]
        assert first[metric]["ci95_low"] <= point <= first[metric]["ci95_high"]


def test_quintile_edges_come_from_discovery_only():
    """Leakage control: validation values cannot move the bucket edges."""
    discovery = [(v, i % 2, None) for i, v in
                 enumerate([i / 1000.0 for i in range(1000)])]
    validation = [(10.0 + v, i % 2, None) for i, v in
                  enumerate([i / 1000.0 for i in range(200)])]
    edges = quintile_edges([v for v, _, _ in discovery])
    assert all(e < 2.0 for e in edges)  # strictly inside the discovery range
    val_table = quintile_table(validation, edges)
    assert val_table[4]["n"] == 200  # all validation rows land in Q5
    assert val_table[0]["n"] == 0


def test_build_rows_orders_by_decision_time_and_keeps_labels():
    audit = {
        "factors": {
            "000002": {_decision_time(i): {"label": i % 2, "volatility": 0.2}
                       for i in range(5)},
            "000001": {_decision_time(i): {"label": (i + 1) % 2, "volatility": 0.1}
                       for i in range(5)},
        },
        "predictions": [], "meta": {"universe": ["000001", "000002"]},
    }
    rows = build_rows(audit)
    assert set(rows) == {"000001", "000002"}
    for symbol, series in rows.items():
        times = [r[0].decision_time for r in series]
        assert times == sorted(times)
        assert all(r[0].label in (0, 1) for r in series)


def test_candidate_registry_schema_and_status_vocabulary(tmp_path):
    from scripts.run_p13p_analysis import run_candidate_registry

    audit = {"factors": {}, "predictions": [], "meta": {"universe": []}}
    # minimal prerequisite artifacts for the registry reader
    n = {"n": 0, "accuracy": 0.5, "brier": 0.25, "log_loss": 0.69,
         "mean_p": 0.5, "positive_rate": 0.5,
         "delta_accuracy": 0.0, "delta_brier": 0.0, "delta_log_loss": 0.0}
    (tmp_path / "single_factor_audit.json").write_text(json.dumps({
        "factors": {f: {"model_b_baseline_plus_factor": n} for f in (
            "momentum", "volatility", "trend", "volume_ratio",
            "industry_relative_return_5", "industry_relative_return_20",
        )}
    }), encoding="utf-8")
    (tmp_path / "volatility_stability.json").write_text(json.dumps({
        "bootstrap": {"rounds": BOOTSTRAP_ROUNDS, "seed": SEED},
        "slices": {}, "per_symbol_summary": {}, "regimes": {},
    }), encoding="utf-8")
    incremental = {"models": {"A_baseline": {"discovery": {"n": 1}, "validation": {"n": 1}}}}
    registry = run_candidate_registry(audit, tmp_path, None, incremental)

    required = {
        "factor_name", "role", "discovery_period", "validation_period",
        "n_discovery", "n_validation", "incremental_accuracy",
        "incremental_brier", "incremental_logloss", "bootstrap_ci",
        "time_stability", "symbol_stability", "regime_stability",
        "redundancy_notes", "validation_status",
    }
    forbidden = {"best", "strongest", "winner", "guaranteed", "high_probability"}
    on_disk = json.loads((tmp_path / "factor_candidates.json").read_text(encoding="utf-8"))
    assert on_disk == registry
    for factor, entry in registry["candidates"].items():
        assert required <= set(entry), f"{factor} missing schema fields"
        assert entry["validation_status"] in REGISTRY_STATUSES
        assert not (forbidden & set(entry["validation_status"].lower().split()))
    assert registry["candidates"]["volatility"]["validation_status"] == "candidate"
    for factor in ("industry_relative_return_5", "industry_relative_return_20"):
        assert registry["candidates"][factor]["validation_status"] == "rejected_for_alpha"


def test_repeated_analysis_writes_byte_identical_json(tmp_path):
    rows_by_symbol = _synth_rows_by_symbol()
    audit = {
        "factors": {
            symbol: {row[0].decision_time: dict(row[1]) for row in series}
            for symbol, series in rows_by_symbol.items()
        },
        "predictions": [
            {"variant": "baseline", "symbol": s, "decision_time": dt,
             "p": 0.5, "y": y, "baseline_p": 0.5}
            for s, series in rows_by_symbol.items()
            for _, dt, _, y, _ in run_model({s: series}, STOCK_FACTORS)
        ],
        "meta": {"universe": ["000001", "000002"],
                 "protocol": {"train_size": 252, "test_size": 20, "step": 20, "gap": 1}},
    }
    args = type("Args", (), {"root": ".", "membership": ""})()
    run_single_factor_audit(audit, tmp_path, args)
    first = (tmp_path / "single_factor_audit.json").read_bytes()
    second_dir = tmp_path / "rerun"
    second_dir.mkdir()
    run_single_factor_audit(audit, second_dir, args)
    second = (second_dir / "single_factor_audit.json").read_bytes()
    assert first == second
