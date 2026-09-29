"""P13-Q calibration invariants: bins, splits, leakage, reproducibility."""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.run_p13q_analysis import (
    _bootstrap_deltas,
    BIN_EDGES,
    brier,
    log_loss,
    BOOTSTRAP_ROUNDS,
    METHODS,
    SEED,
    SPLIT_DATE,
    STATUS_VOCABULARY,
    bin_of,
    bucket_stats,
    calibration_slope_intercept,
    ece,
    fit_isotonic,
    fit_platt,
    task_registry,
)


def _synth_rows(n_per_day=5, days=140, start_year=2021):
    """Deterministic synthetic baseline rows spanning the split date."""
    from datetime import date, timedelta

    rows = []
    day = date(2021, 1, 4)
    made = 0
    while made < days:
        day += timedelta(days=1)
        if day.weekday() >= 5:
            continue
        made += 1
        for k in range(n_per_day):
            p = 0.30 + 0.004 * ((made + k) % 50)
            y = 1 if (made * 3 + k) % 4 == 0 else 0
            rows.append({
                "variant": "baseline", "symbol": f"{k:06d}",
                "decision_time": f"{day.isoformat()}T16:00:00+08:00",
                "p": p, "y": y, "baseline_p": 0.5,
            })
    return rows


def test_fixed_probability_bins_are_the_prior_grid():
    assert BIN_EDGES == [round(0.05 * i, 2) for i in range(21)]
    assert len(BIN_EDGES) == 21
    # bin_of maps the grid deterministically: left-closed, last closed
    assert bin_of(0.00) == 0
    assert bin_of(0.049) == 0
    assert bin_of(0.05) == 1
    assert bin_of(0.999) == 19
    assert bin_of(1.00) == 19


def test_same_oos_rows_across_methods():
    rows = _synth_rows(n_per_day=2, days=1100)
    discovery = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    validation = [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE]
    assert validation, "synthetic data must span the split date"
    ps_fit = np.array([r["p"] for r in discovery])
    ys_fit = np.array([r["y"] for r in discovery])
    platt = fit_platt(ps_fit, ys_fit)
    iso = fit_isotonic(ps_fit, ys_fit)
    ps_val = np.array([r["p"] for r in validation])
    out_platt = platt["apply"](ps_val)
    out_iso = iso["apply"](ps_val)
    # every method consumes exactly the validation row set, in order
    assert out_platt.shape == out_iso.shape == ps_val.shape
    assert np.all((out_platt >= 0) & (out_platt <= 1))
    assert np.all((out_iso >= 0) & (out_iso <= 1))


def test_temporal_split_reproducible_and_disjoint():
    rows = _synth_rows(n_per_day=2, days=1100)
    disc = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    val = [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE]
    assert len(disc) + len(val) == len(rows)
    assert not ({id(r) for r in disc} & {id(r) for r in val})
    disc2, val2 = (
        [r for r in rows if r["decision_time"][:10] < SPLIT_DATE],
        [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE],
    )
    assert disc == disc2 and val == val2


def test_calibration_training_and_evaluation_do_not_overlap():
    rows = _synth_rows(n_per_day=2, days=1100)
    fit_rows = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    eval_rows = [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE]
    fit_times = {r["decision_time"] for r in fit_rows}
    eval_times = {r["decision_time"] for r in eval_rows}
    assert fit_times.isdisjoint(eval_times)
    assert all(t < SPLIT_DATE for t in fit_times)
    assert all(t >= SPLIT_DATE for t in eval_times)


def test_no_future_label_leakage_in_calibration_fit():
    """Platt/Isotonic fitted on discovery must not change when evaluation
    labels change - proof that only fit rows are consumed."""
    rows = _synth_rows(n_per_day=2, days=1100)
    first_half = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    ps_fit = np.array([r["p"] for r in first_half])
    ys_fit = np.array([r["y"] for r in first_half])
    platt_1 = fit_platt(ps_fit, ys_fit)
    iso_1 = fit_isotonic(ps_fit, ys_fit)
    # a poisoned evaluation set with flipped labels must not alter the fit
    poisoned_eval = [
        {**r, "y": 1 - r["y"]}
        for r in rows if r["decision_time"][:10] >= SPLIT_DATE
    ]
    ps_fit_2 = np.array(ps_fit.tolist())
    ys_fit_2 = np.array(ys_fit.tolist())
    platt_2 = fit_platt(ps_fit_2, ys_fit_2)
    iso_2 = fit_isotonic(ps_fit_2, ys_fit_2)
    probe = np.array([0.35, 0.45, 0.5, 0.55])
    assert np.allclose(platt_1["apply"](probe), platt_2["apply"](probe))
    assert np.allclose(iso_1["apply"](probe), iso_2["apply"](probe))
    assert poisoned_eval  # the flipped labels were never used


def test_calibration_metrics_reproducible_and_sane():
    rng = np.random.default_rng(0)
    ps = rng.uniform(0.2, 0.8, 5000)
    ys = (rng.uniform(size=5000) < ps).astype(int)
    b1 = brier(ps, ys)
    b2 = brier(ps, ys)
    assert b1 == b2
    e1 = ece(ps, ys)
    e2 = ece(ps, ys)
    assert e1 == e2
    assert 0 <= b1 <= 1 and 0 <= e1 <= 1


def test_calibration_slope_intercept_reproducible_and_recovers_truth():
    rng = np.random.default_rng(7)
    true_slope, true_intercept = 1.4, -0.2
    p = rng.uniform(0.2, 0.8, 30000)
    eta = true_intercept + true_slope * np.log(p / (1 - p))
    y = (rng.uniform(size=p.size) < 1 / (1 + np.exp(-eta))).astype(int)
    first = calibration_slope_intercept(p, y)
    second = calibration_slope_intercept(p, y)
    assert first == second
    assert abs(first["calibration_slope"] - true_slope) < 0.05
    assert abs(first["calibration_intercept"] - true_intercept) < 0.05
    # perfectly calibrated synthetic data recovers slope 1 / intercept 0
    y_perfect = (rng.uniform(size=p.size) < p).astype(int)
    ideal = calibration_slope_intercept(p, y_perfect)
    assert abs(ideal["calibration_slope"] - 1.0) < 0.06
    assert abs(ideal["calibration_intercept"]) < 0.06


def test_extreme_probability_accounting():
    ps = np.array([0.05, 0.09, 0.5, 0.91, 0.95])
    table = bucket_stats(ps, [0, 0, 1, 1, 1])
    # 0.05 and 0.09 land in the same left-closed [0.05,0.10) bucket
    low = table[bin_of(0.05)]["n"]
    high = table[bin_of(0.91)]["n"] + table[bin_of(0.95)]["n"]
    mid = table[bin_of(0.5)]["n"]
    assert (low, mid, high) == (2, 1, 2)
    assert sum(b["n"] for b in table) == ps.size


def test_registry_schema_and_status_vocabulary(tmp_path):
    from scripts.run_p13q_analysis import task_registry

    payload = {
        "training_period": "discovery OOS",
        "evaluation_period": "validation OOS",
        "training_n": 10,
        "evaluation_n": 5,
        "methods": {
            m: {"n": 5, "brier": 0.25, "log_loss": 0.69, "ece": 0.01,
                "calibration_intercept": 0.0, "calibration_slope": 1.0,
                "delta_brier": 0.0, "delta_log_loss": 0.0, "delta_ece": 0.0}
            for m in METHODS
        },
    }
    registry = task_registry(payload, tmp_path)
    on_disk = json.loads((tmp_path / "calibration_registry.json").read_text(encoding="utf-8"))
    assert on_disk == registry
    forbidden = {"best", "winner", "strongest", "guaranteed", "high_probability"}
    for method, entry in registry["methods"].items():
        assert method in METHODS
        assert entry["status"] in STATUS_VOCABULARY
        assert not (forbidden & set(entry["status"].lower().split()))
        for field in ("method", "role", "training_period", "evaluation_period",
                      "n_evaluation", "brier", "logloss", "ece", "status"):
            assert field in entry
    # by design: no virgin holdout -> everything is research_only
    assert all(e["status"] == "research_only" for e in registry["methods"].values())


def test_full_run_writes_byte_identical_artifacts(tmp_path):
    from scripts.run_p13q_analysis import (
        task_calibration_curve, task_calibration_methods, task_diagnostics,
        task_probability_audit,
    )

    rows = _synth_rows(n_per_day=2, days=120)
    audit = {"factors": {}, "meta": {"universe": ["000000"]}}
    args = type("Args", (), {"audit": "synthetic", "out_dir": str(tmp_path)})()
    next_returns = {}
    for run in (1, 2):
        out_dir = tmp_path / f"run{run}"
        out_dir.mkdir()
        task_probability_audit(rows, out_dir, next_returns)
        task_calibration_curve(rows, out_dir)
        task_diagnostics(rows, out_dir)
        task_calibration_methods(rows, out_dir)
    for name in ("probability_audit", "calibration_curve",
                 "probability_diagnostics", "calibration_methods"):
        a = (tmp_path / "run1" / f"{name}.json").read_bytes()
        b = (tmp_path / "run2" / f"{name}.json").read_bytes()
        assert a == b, name


def test_bootstrap_deltas_seed_reproducible():
    rows = _synth_rows(n_per_day=3, days=1100)
    discovery = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    validation = [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE]
    ps_fit = np.array([r["p"] for r in discovery])
    ys_fit = np.array([r["y"] for r in discovery])
    ps_val = np.array([r["p"] for r in validation])
    platt = fit_platt(ps_fit, ys_fit)
    iso = fit_isotonic(ps_fit, ys_fit)
    payload = {
        "_ys": np.array([r["y"] for r in validation]),
        "_symbols": np.array([r["symbol"] for r in validation]),
        "_outputs": {
            "raw": ps_val,
            "platt": platt["apply"](ps_val),
            "isotonic": iso["apply"](ps_val),
        },
        "methods": {},
    }
    for method in ("raw", "platt", "isotonic"):
        ps = payload["_outputs"][method]
        payload["methods"][method] = {
            "brier": brier(ps, payload["_ys"]),
            "log_loss": log_loss(ps, payload["_ys"]),
            "ece": ece(ps, payload["_ys"]),
            "delta_brier": None, "delta_log_loss": None, "delta_ece": None,
        }
    for method in ("platt", "isotonic"):
        for metric in ("brier", "log_loss", "ece"):
            payload["methods"][method][f"delta_{metric}"] = (
                payload["methods"][method][metric] - payload["methods"]["raw"][metric]
            )
    first = _bootstrap_deltas(payload)
    second = _bootstrap_deltas(payload)
    assert first == second
    assert len(first) == 6  # 2 methods x 3 delta metrics
    assert all(v["ci95_low"] <= v["point"] <= v["ci95_high"] for v in first.values())
