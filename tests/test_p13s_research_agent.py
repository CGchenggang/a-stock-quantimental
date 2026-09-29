"""P13-S research report layer invariants (18 required checks)."""
from __future__ import annotations

import json

import pytest

from scripts.run_p13s_report import (
    EVIDENCE_MAP,
    KNOWN_POLICIES,
    REQUIRED_FIELDS,
    SCHEMA_VERSION,
    build_report,
    freshness_of,
    process_packets,
    render_markdown,
    run_golden,
    validate_packet,
)


def _packet(**overrides):
    packet = {
        "symbol": "000001",
        "decision_time": "2025-03-18T16:00:00+08:00",
        "policy_id": "threshold_platt_p50",
        "calibration_method": "platt",
        "raw_probability": 0.7397,
        "calibrated_probability": 0.5128,
        "expected_return": 0.0008,
        "risk_score": 0.0086,
        "cost_scenario": "low",
        "cost_adjusted_expected_return": -0.0002,
        "market_regime": "BULL",
        "selection_reason": "platt_probability_ge_0.50",
        "risk_flags": ["P13R_HIGH_TURNOVER"],
        "data_available_time": "2025-03-18T16:00:00+08:00",
    }
    packet.update(overrides)
    return packet


# 1. normal packet -> report
def test_normal_packet_generates_report():
    report = build_report(_packet())
    assert report["report_id"] and report["schema_version"] == SCHEMA_VERSION
    assert report["uncertainty"] == []
    assert report["data_freshness_status"] == "fresh"


# 2. schema correctness
def test_report_schema_fields():
    report = build_report(_packet())
    for field in (
        "report_id", "schema_version", "symbol", "decision_time", "policy_id",
        "raw_probability", "calibrated_probability", "calibration_method",
        "expected_return", "cost_adjusted_expected_return", "risk_score",
        "risk_flags", "market_regime", "selection_reason",
        "data_available_time", "data_freshness_status", "uncertainty",
        "evidence_refs", "research_only",
    ):
        assert field in report, field
    assert report["schema_version"] == SCHEMA_VERSION


# 3. core fields pass through verbatim
def test_core_fields_pass_through():
    packet = _packet()
    report = build_report(packet)
    for field in ("symbol", "decision_time", "policy_id", "calibration_method",
                  "raw_probability", "calibrated_probability",
                  "expected_return", "cost_adjusted_expected_return",
                  "risk_score", "market_regime", "selection_reason",
                  "data_available_time"):
        assert report[field] == packet[field], field


# 4. calibration method and probability correspondence
def test_calibration_method_and_probability_correspond():
    variants = [
        ("raw", "threshold_raw_p50", "raw_probability_ge_0.50"),
        ("platt", "threshold_platt_p50", "platt_probability_ge_0.50"),
        ("isotonic", "threshold_iso_p50", "isotonic_probability_ge_0.50"),
        ("none", "threshold_raw_p50", "raw_probability_ge_0.50"),
    ]
    for method, policy, reason in variants:
        packet = _packet(calibration_method=method, policy_id=policy,
                         calibrated_probability=0.61, selection_reason=reason)
        report = build_report(packet)
        assert report["calibration_method"] == method
        assert report["calibrated_probability"] == 0.61
        assert report["policy_id"] == policy
        assert report["selection_reason"] == reason
    # unknown calibration must not be guessed into a known one
    weird = _packet(calibration_method="unknown_calibration")
    assert build_report(weird)["calibration_method"] == "unknown_calibration"


# 5. expected_return vs cost_adjusted_expected_return not conflated
def test_expected_return_fields_distinct():
    packet = _packet(expected_return=0.008, cost_adjusted_expected_return=-0.0002)
    report = build_report(packet)
    assert report["expected_return"] == 0.008
    assert report["cost_adjusted_expected_return"] == -0.0002
    assert report["expected_return"] != report["cost_adjusted_expected_return"]
    rendered = render_markdown(report)
    assert "Expected Return: 0.8000%" in rendered
    assert "Cost-adjusted Expected Return: -0.0200%" in rendered


# 6. policy_id preserved
def test_policy_id_preserved():
    assert build_report(_packet(policy_id="topk_platt_k3"))["policy_id"] == "topk_platt_k3"


# 7. selection_reason preserved
def test_selection_reason_preserved():
    packet = _packet(selection_reason="expected_return_gt_0_and_volatility_le_daily_median")
    report = build_report(packet)
    assert report["selection_reason"] == "expected_return_gt_0_and_volatility_le_daily_median"
    assert packet["selection_reason"] == report["selection_reason"]


# 8. risk_flags never lost
def test_risk_flags_pass_through_and_separate_from_p13s_flags():
    report = build_report(_packet(risk_flags=["P13R_HIGH_TURNOVER", "LEGACY"]))
    assert report["risk_flags"] == ["P13R_HIGH_TURNOVER", "LEGACY"]
    # P13-S validation conclusions live in their own field
    report_uncal = build_report(_packet(calibration_method="none"))
    assert report_uncal["p13s_validation_flags"] == ["low_confidence"]
    # P13-R risk flags still pass through untouched on the same packet
    assert report_uncal["risk_flags"] == ["P13R_HIGH_TURNOVER"]


# 9. data_available_time not fabricated
def test_data_available_time_not_fabricated():
    packet = _packet(data_available_time="2025-03-17T16:00:00+08:00")
    report = build_report(packet)
    assert report["data_available_time"] == "2025-03-17T16:00:00+08:00"
    missing = build_report({k: v for k, v in packet.items()
                            if k != "data_available_time"})
    assert missing["data_available_time"] is None
    assert missing["data_freshness_status"] == "missing"
    assert "MISSING (insufficient_evidence)" in render_markdown(missing)


# 10. missing data explicitly flagged
def test_missing_data_flagged():
    packet = _packet()
    del packet["market_regime"]
    packet["risk_score"] = None
    report = build_report(packet)
    assert "missing_data" in report["uncertainty"]
    assert "market_regime" in report["missing_fields"]
    assert report["market_regime"] is None


# 11. stale data explicitly flagged
def test_stale_data_flagged():
    report = build_report(_packet(
        data_available_time="2025-03-20T16:00:00+08:00"))
    assert report["data_freshness_status"] == "stale"
    assert "stale_data" in report["uncertainty"]


# 12. unknown policy explicitly flagged
def test_unknown_policy_flagged():
    report = build_report(_packet(policy_id="mystery_policy_v9"))
    assert "unknown_policy" in report["uncertainty"]
    assert report["known_policy"] is False
    rendered = render_markdown(report)
    assert "no confident recommendation conclusion" in rendered


# 13. contradictory evidence not silently resolved
def test_contradictory_evidence_flagged_not_resolved():
    report = build_report(_packet(raw_probability=0.55,
                                  calibrated_probability=0.42))
    assert "contradictory_evidence" in report["uncertainty"]
    assert report["raw_probability"] == 0.55  # both values kept verbatim
    assert report["calibrated_probability"] == 0.42
    rendered = render_markdown(report)
    assert "no resolution is applied by P13-S" in rendered


# 14. calibration variants render distinctly
def test_calibration_variants_render(tmp_path):
    golden_dir = tmp_path / "golden_reports"
    run_golden(tmp_path)
    names = {p.stem for p in golden_dir.glob("*.json")}
    assert {"normal", "missing_data", "stale_data", "low_confidence",
            "contradictory_evidence", "unknown_policy", "risk_flags_present",
            "calibration_raw", "calibration_none",
            "calibration_isotonic"} <= names
    for name in ("calibration_raw", "calibration_none", "calibration_isotonic"):
        entry = json.loads((golden_dir / f"{name}.json").read_text(encoding="utf-8"))
        assert entry["report"]["calibration_method"] == name.split("_")[1]
        assert entry["packet"]["calibration_method"] == entry["report"]["calibration_method"]
        assert f"Calibration Method: {entry['report']['calibration_method']}" in entry["rendered"]


# 15. same input -> byte-identical report
def test_reports_are_byte_identical_for_same_input():
    packet = _packet()
    first = json.dumps(build_report(packet), sort_keys=True)
    second = json.dumps(build_report(packet), sort_keys=True)
    assert first == second
    assert render_markdown(build_report(packet)) == render_markdown(build_report(packet))


# 16. future rows do not affect past reports
def test_future_row_immunity():
    past = _packet(decision_time="2025-01-02T16:00:00+08:00",
                   data_available_time="2025-01-02T16:00:00+08:00")
    report_a = build_report(past)
    # a "future" packet added to the same batch must not change the past report
    future = _packet(symbol="000009",
                     decision_time="2026-09-01T16:00:00+08:00",
                     data_available_time="2026-09-01T16:00:00+08:00",
                     raw_probability=0.99, calibrated_probability=0.99)
    import pathlib
    out = pathlib.Path(__file__).parent / "_p13s_immunity_tmp"
    result_a = process_packets([past], out / "a")
    result_b = process_packets([past, future], out / "b")
    report_a2 = [r for r in result_b["reports"] if r["symbol"] == "000001"][0]
    assert result_a["reports"][0] == report_a2 == report_a


# 17. no trading-execution intent in rendered reports
def test_no_trading_intent_vocabulary():
    for overrides in (
        {}, {"market_regime": "BEAR"}, {"policy_id": "hold_all",
        "calibration_method": "none", "selection_reason": "baseline_hold_all"},
    ):
        rendered = render_markdown(build_report(_packet(**overrides))).lower()
        for fragment in ("buy now", "sell now", "place order", "execute trade",
                         "submit order", "open position", "close position",
                         "broker"):
            assert fragment not in rendered, fragment
    assert "research_only = true" in render_markdown(build_report(_packet()))


# 18. renderer cannot mutate the packet
def test_renderer_does_not_modify_packet():
    packet = _packet()
    snapshot = json.dumps(packet, sort_keys=True)
    report = build_report(packet)
    rendered = render_markdown(report)
    assert json.dumps(packet, sort_keys=True) == snapshot
    # deep mutation attempt on the report must not leak into the packet
    report["risk_flags"].append("INJECTED")
    report["symbol"] = "999999"
    assert packet["risk_flags"] == ["P13R_HIGH_TURNOVER"]
    assert packet["symbol"] == "000001"
    assert rendered  # renderer output already produced before mutation


# freshness rule table
def test_freshness_rule_table():
    assert freshness_of(_packet()) == "fresh"
    assert freshness_of(_packet(data_available_time="2025-03-19T16:00:00+08:00")) == "stale"
    assert freshness_of({k: v for k, v in _packet().items()
                         if k != "data_available_time"}) == "missing"
    assert freshness_of(_packet(data_available_time="not-a-time")) == "unknown"


# evidence traceability map
def test_evidence_refs_cover_core_claims():
    report = build_report(_packet())
    claims = {ref["claim"] for ref in report["evidence_refs"]}
    assert {"raw_probability", "calibrated_probability", "expected_return",
            "market_regime", "selection_reason"} <= claims
    for ref in report["evidence_refs"]:
        assert ref["report_field"] == EVIDENCE_MAP[ref["claim"]][0]
        assert ref["source_stage"].startswith("p13")


# required-fields vocabulary is the real P13-R schema
def test_required_fields_match_p13r_schema():
    assert set(REQUIRED_FIELDS) == {
        "symbol", "decision_time", "policy_id", "calibration_method",
        "raw_probability", "calibrated_probability", "expected_return",
        "risk_score", "cost_scenario", "cost_adjusted_expected_return",
        "market_regime", "selection_reason", "risk_flags",
        "data_available_time",
    }
    assert set(KNOWN_POLICIES) == {
        "hold_all", "threshold_raw_p50", "threshold_platt_p50",
        "threshold_iso_p50", "topk_platt_k3", "percentile_platt_p80",
        "er_platt_0", "er_platt_pos_risk",
    }


# validate_packet surface
def test_validate_packet_reports_missing_and_known_policy():
    validation = validate_packet(_packet())
    assert validation["missing_fields"] == []
    assert validation["known_policy"] is True
    stripped = {k: v for k, v in _packet().items() if k not in
                ("risk_score", "market_regime")}
    v2 = validate_packet(stripped)
    assert sorted(v2["missing_fields"]) == ["market_regime", "risk_score"]
    assert "missing_data" in v2["uncertainty"]
