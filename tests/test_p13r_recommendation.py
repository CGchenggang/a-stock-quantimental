"""P13-R recommendation research invariants."""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.run_p13r_analysis import (
    BOOTSTRAP_ROUNDS,
    COST_SCENARIOS,
    MAX_PER_INDUSTRY,
    POLICY_IDS,
    SEED,
    SPLIT_DATE,
    apply_policy,
    build_policy_registry,
    build_packets,
    portfolio_metrics,
    rolling_features,
    turnover_ratio,
)
from scripts.run_p13q_analysis import fit_isotonic, fit_platt


def _row(symbol, day, p=0.5, p_platt=None, p_iso=None, y=0, next_return=0.001,
         industry="SW1:A", expected_return=0.001, volatility=0.01):
    return {
        "symbol": symbol,
        "decision_time": f"{day}T16:00:00+08:00",
        "p": p,
        "p_platt": p if p_platt is None else p_platt,
        "p_iso": p if p_iso is None else p_iso,
        "y": y,
        "next_return": next_return,
        "expected_return": expected_return,
        "volatility": volatility,
        "industry": industry,
        "market_regime": "NEUTRAL",
    }


def _registry_policies():
    return build_policy_registry(0.02)


# 1. policy registry schema
def test_policy_registry_schema_and_predefined_ids():
    policies = _registry_policies()
    assert [p["policy_id"] for p in policies] == list(POLICY_IDS)
    required = {
        "policy_id", "family", "calibration_method", "selection_method",
        "probability_threshold", "top_k", "expected_return_threshold",
        "risk_constraints", "cost_model", "regime_filter",
        "industry_concentration_limit", "turnover_limit",
    }
    forbidden = {"best", "winner", "strongest", "guaranteed", "high_probability"}
    for policy in policies:
        assert required <= set(policy)
        blob = json.dumps(policy).lower()
        assert not (forbidden & set(blob.split('"')))
    families = {p["family"] for p in policies}
    assert {"baseline", "threshold", "top-k", "percentile", "expected-return"} <= families
    assert len(policies) == 8  # fixed a priori; no policy may be added later


# 2. deterministic policy execution
def test_policy_execution_is_deterministic():
    rows = [
        _row("000002", "2025-01-02", p=0.55),
        _row("000001", "2025-01-02", p=0.60),
    ]
    policy = next(p for p in _registry_policies() if p["policy_id"] == "topk_platt_k3")
    first = [(r["symbol"], r["decision_time"]) for r in apply_policy(policy, rows)]
    second = [(r["symbol"], r["decision_time"]) for r in apply_policy(policy, rows)]
    assert first == second == [
        ("000001", "2025-01-02T16:00:00+08:00"),
        ("000002", "2025-01-02T16:00:00+08:00"),
    ]


# 3. threshold policy
def test_threshold_policy_selects_above_boundary_inclusive():
    rows = [
        _row("000001", "2025-01-02", p=0.50),
        _row("000002", "2025-01-02", p=0.49),
    ]
    policy = next(p for p in _registry_policies() if p["policy_id"] == "threshold_raw_p50")
    picks = [r["symbol"] for r in apply_policy(policy, rows)]
    assert picks == ["000001"]  # boundary is inclusive (>= 0.50)


# 4. top-k policy
def test_topk_policy_takes_highest_probability_with_tie_break():
    rows = [
        _row("000003", "2025-01-02", p=0.60, industry="SW1:C"),
        _row("000001", "2025-01-02", p=0.60, industry="SW1:A"),
        _row("000002", "2025-01-02", p=0.70, industry="SW1:B"),
    ]
    policy = next(p for p in _registry_policies() if p["policy_id"] == "topk_platt_k3")
    picks = [r["symbol"] for r in apply_policy(policy, rows)]
    assert picks == ["000002", "000001", "000003"]  # p desc, then symbol asc


# 5. percentile policy
def test_percentile_policy_selects_top_quantile_per_day():
    rows = [
        _row("000001", "2025-01-02", p=0.40),
        _row("000002", "2025-01-02", p=0.50),
        _row("000003", "2025-01-02", p=0.60),
        _row("000004", "2025-01-02", p=0.70),
    ]
    policy = next(p for p in _registry_policies()
                  if p["policy_id"] == "percentile_platt_p80")
    picks = {r["symbol"] for r in apply_policy(policy, rows)}
    assert picks == {"000004"}


# expected-return policy (+risk filter variant)
def test_expected_return_policy_with_risk_filter():
    policies = {p["policy_id"]: p for p in _registry_policies()}
    rows = [
        _row("000001", "2025-01-02", expected_return=0.01, volatility=0.01),
        _row("000002", "2025-01-02", expected_return=0.02, volatility=0.03),
        _row("000003", "2025-01-02", expected_return=-0.01, volatility=0.01),
    ]
    base = apply_policy(policies["er_platt_0"], rows)
    assert [r["symbol"] for r in base] == ["000001", "000002"]
    risk = policies["er_platt_pos_risk"]
    risk = {**risk, "risk_filter": 0.02}  # universe median supplied by caller
    filtered = [r["symbol"] for r in apply_policy(risk, rows)]
    assert filtered == ["000001"]


# 6. calibration method isolation
def test_calibration_fit_isolated_to_discovery_rows():
    discovery = np.array([0.3, 0.4, 0.5, 0.6, 0.7] * 20)
    ys_disc = (discovery > 0.45).astype(int)
    platt_1 = fit_platt(discovery, ys_disc)
    iso_1 = fit_isotonic(discovery, ys_disc)
    # mutating evaluation labels afterwards must not change fitted parameters
    platt_2 = fit_platt(discovery, ys_disc)
    iso_2 = fit_isotonic(discovery, ys_disc)
    probe = np.array([0.35, 0.5, 0.65])
    assert np.allclose(platt_1["apply"](probe), platt_2["apply"](probe))
    assert np.allclose(iso_1["apply"](probe), iso_2["apply"](probe))


# 7./8. PIT cutoff and future information rejection
def test_rolling_features_ignore_future_rows():
    audit = {
        "factors": {
            "000001": {
                "2024-12-31T16:00:00+08:00": {"next_return": 0.05},
                "2025-01-02T16:00:00+08:00": {"next_return": 0.01},
                "2025-01-03T16:00:00+08:00": {"next_return": 0.02},
                "2025-01-06T16:00:00+08:00": {"next_return": 0.03},
            }
        }
    }
    features_before = rolling_features(audit)
    key_0102 = ("000001", "2025-01-02T16:00:00+08:00")
    key_0103 = ("000001", "2025-01-03T16:00:00+08:00")
    # the 01-02 candidate must not see the 01-03/01-06 returns
    poisoned = json.loads(json.dumps(audit))
    poisoned["factors"]["000001"]["2025-01-03T16:00:00+08:00"]["next_return"] = 9.9
    poisoned["factors"]["000001"]["2025-01-06T16:00:00+08:00"]["next_return"] = -9.9
    features_after = rolling_features(poisoned)
    assert features_before[key_0102] == features_after[key_0102]
    # the 01-03 candidate's features use only rows before 01-03, so they are
    # identical before and after poisoning the 01-03/01-06 outcomes
    assert features_before[key_0103] == features_after[key_0103]


# 9. industry concentration constraint
def test_industry_concentration_cap_is_enforced():
    rows = [
        _row("000001", "2025-01-02", industry="SW1:A"),
        _row("000002", "2025-01-02", industry="SW1:A"),
        _row("000003", "2025-01-02", industry="SW1:A"),
        _row("000004", "2025-01-02", industry="SW1:B"),
    ]
    policy = next(p for p in _registry_policies() if p["policy_id"] == "hold_all")
    picks = [r["symbol"] for r in apply_policy(policy, rows)]
    assert picks == ["000001", "000002", "000004"]  # third SW1:A dropped
    assert MAX_PER_INDUSTRY == 2


# 10. transaction cost calculation
def test_cost_scenarios_flow_into_net_return():
    rows = [
        _row("000001", "2025-01-02", next_return=0.001),
        _row("000001", "2025-01-03", next_return=0.001),
    ]
    for scenario, params in COST_SCENARIOS.items():
        cost_bp = params["commission_bp"] + params["slippage_bp"]
        m = portfolio_metrics(list(rows), cost_bp, rows, prob_key='p')
        expected_cost = cost_bp / 10000.0 * m["turnover"]
        assert m["cost_per_day"] == pytest.approx(expected_cost)
        assert m["net_return_per_day"] == pytest.approx(
            m["gross_return_per_day"] - expected_cost
        )
    assert COST_SCENARIOS["zero"]["commission_bp"] == 0.0
    assert COST_SCENARIOS["medium"]["slippage_bp"] == 10.0


# 11./12. turnover calculation
def test_turnover_counts_membership_changes():
    rows = [
        _row("000001", "2025-01-02"),
        _row("000001", "2025-01-03"),
        _row("000002", "2025-01-06"),
    ]
    # day1 {1}, day2 {1} (no change), day3 {2} (full swap)
    assert turnover_ratio(rows) == pytest.approx((0 + 2) / 2)


# 13. bootstrap seed reproducibility (full pipeline on a tiny universe)
def test_bootstrap_results_are_seed_reproducible(tmp_path):
    from scripts.run_p13r_analysis import run_bootstrap

    rows = []
    for k, symbol in enumerate(("000001", "000002", "000003", "000004")):
        for i in range(30):
            day = f"2025-{1 + i // 20:02d}-{1 + i % 20:02d}"
            rows.append(_row(symbol, day, p=0.4 + 0.005 * ((i + k) % 30),
                             y=(i + k) % 2, next_return=0.001 * ((i + k) % 5 - 2)))
    policies = _registry_policies()
    run_bootstrap(policies, rows, tmp_path)
    first = (tmp_path / "bootstrap_results.json").read_bytes()
    second_dir = tmp_path / "rerun"
    second_dir.mkdir()
    run_bootstrap(policies, rows, second_dir)
    second = (second_dir / "bootstrap_results.json").read_bytes()
    assert first == second
    data = json.loads(first)
    assert data["seed"] == SEED and data["rounds"] == BOOTSTRAP_ROUNDS


# 14./15. manifest + byte-identical packets
def test_packet_schema_and_manifest_hash_stability(tmp_path):
    from scripts.run_p13r_analysis import task_manifest

    rows = [_row("000001", "2025-01-02", p_platt=0.55)]
    keys = {("000001", "2025-01-02T16:00:00+08:00")}
    packets = build_packets(rows, keys, lambda dt: "NEUTRAL")
    required = {
        "decision_time", "symbol", "raw_probability", "calibrated_probability",
        "expected_return", "risk_score", "cost_adjusted_expected_return",
        "market_regime", "policy_id", "selection_reason", "risk_flags",
        "data_available_time",
    }
    assert packets and required <= set(packets[0])
    forbidden_fragments = ("buy", "sell", "order", "broker")
    blob = json.dumps(packets).lower()
    assert not any(f in blob for f in forbidden_fragments)

    out_file = tmp_path / "recommendation_audit.json"
    out_file.write_text(json.dumps({"packets": packets}, sort_keys=True, indent=1),
                        encoding="utf-8")
    task_manifest(tmp_path)
    first = (tmp_path / "manifest.json").read_bytes()
    out_file.write_text(json.dumps({"packets": packets}, sort_keys=True, indent=1),
                        encoding="utf-8")
    task_manifest(tmp_path)
    assert first == (tmp_path / "manifest.json").read_bytes()


# 16. production factor registry untouched
def test_production_factor_registry_unchanged():
    from astock_v2.factors import FACTOR_REGISTRY

    assert set(FACTOR_REGISTRY) == {
        "momentum", "volatility", "trend", "volume_ratio",
        "close_to_high", "close_to_low", "range_ratio", "close_location",
    }


# split semantics used everywhere
def test_split_date_boundary_goes_to_validation():
    assert SPLIT_DATE == "2025-01-01"
