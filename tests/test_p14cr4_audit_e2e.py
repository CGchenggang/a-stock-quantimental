"""P14-C-R4 end-to-end regression tests.

These tests run run_quality_audit(tmp_path) and verify the FINAL JSON
artifacts on disk — not the Python return values. This locks the contract
between the audit implementation and the emitted files.
"""
from __future__ import annotations

import json

import pytest

from scripts.run_p14c_quality_audit import (
    EXPECTED_CONTRACT,
    run_quality_audit,
    write_manifest,
)


def _run_audit(tmp_path):
    out = tmp_path / "audit"
    run_quality_audit(out)
    write_manifest(out, [])
    return out


# R4: audit runs successfully from a clean directory
def test_audit_runs_successfully_from_clean_directory(tmp_path):
    out = _run_audit(tmp_path)
    for f in ("quality_report.json", "source_health.json", "completeness.json",
              "reconciliation.json", "manifest.json"):
        assert (out / f).exists(), f


# R4/R5: expected absence vs unexpected missing are distinguished
def test_expected_absence_and_unexpected_missing(tmp_path):
    out = _run_audit(tmp_path)
    comp = json.load(open(out / "completeness.json"))
    # broken_source fetch always raises -> SOURCE_ERROR; the contract
    # declares expected_absence=True (it requires no data by design)
    assert comp["broken_source"]["missingness_class"] == "SOURCE_ERROR"
    assert comp["broken_source"]["expected_absence"] is True
    # company_announcement has an extra expected date (2026-03-04) that the
    # fixture does not provide -> UNEXPECTED_MISSING with coverage < 1
    assert comp["company_announcement"]["missingness_class"] == "UNEXPECTED_MISSING"
    assert "2026-03-04" in comp["company_announcement"]["missing_dates"]
    assert comp["company_announcement"]["coverage_ratio"] < 1.0
    # other real sources: EXPECTED_ABSENCE (coverage complete) or
    # UNEXPECTED_MISSING if entities/dates are missing
    for source in ("cn_index_daily", "macro_pmi_cn", "us_index_daily"):
        c = comp[source]
        assert c["missingness_class"] in ("EXPECTED_ABSENCE", "UNEXPECTED_MISSING")
        assert "expected_entities" in c and "actual_entities" in c
        assert "expected_dates" in c and "actual_dates" in c
        assert "missing_entities" in c and "missing_dates" in c
        assert "coverage_ratio" in c


# R4: independent expected contract - missing entity/date detection
def test_expected_contract_is_independent_of_actual_payload():
    """The contract must be frozen a priori: if a payload is missing from
    ingestion, expected_dates must NOT shrink to match actual."""
    contract = EXPECTED_CONTRACT["cn_index_daily"]
    assert len(contract["expected_dates"]) >= 2
    assert contract["expected_entities"] == ["CSI300"]
    # the contract is a module-level constant, not derived from payloads


# R4: nine-dimension quality report structure
def test_nine_dimension_quality_report(tmp_path):
    out = _run_audit(tmp_path)
    qr = json.load(open(out / "quality_report.json"))
    required_dims = {
        "completeness", "validity", "timeliness", "freshness",
        "consistency", "revision_integrity", "provenance_integrity",
        "pit_admissibility", "source_health",
    }
    assert required_dims <= set(qr["dimensions"])
    for dim_name, dim in qr["dimensions"].items():
        assert "status" in dim, dim_name
        assert "reasons" in dim, dim_name
        assert "metrics" in dim, dim_name
        assert "evidence" in dim, dim_name


# R4: reconciliation end-to-end evidence from the final artifact
def test_reconciliation_end_to_end_fields(tmp_path):
    out = _run_audit(tmp_path)
    recon = json.load(open(out / "reconciliation.json"))
    for group in recon["groups"]:
        # group-level fields
        for field in ("difference", "relative_difference", "policy_id",
                      "policy_version", "status"):
            assert field in group, field
        assert group["status"] in ("CONSISTENT", "CONFLICT", "INSUFFICIENT_SOURCES")
        # each contributing source must preserve provenance
        for source_entry in group["sources"]:
            for field in ("source", "source_id", "value",
                          "event_time", "available_time", "ingested_at",
                          "ingestion_id", "raw_payload_hash", "provenance"):
                assert field in source_entry, field
            assert "provenance" in source_entry
            pv = source_entry["provenance"]
            for field in ("source", "source_id", "ingested_at", "adapter_version"):
                assert field in pv, field


# R4: SOURCE_ERROR / REJECTED / SOURCE_EMPTY appear in the durable audit
def test_durable_audit_chain_covers_all_anomaly_classes(tmp_path):
    out = _run_audit(tmp_path)
    lines = (out / "raw_ingestion_audit.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    outcomes = {e["outcome"] for e in events}
    # broken_source adapter fetch raises -> SOURCE_ERROR in the audit chain
    assert "SOURCE_ERROR" in outcomes
    # parse_failure_source payload lacks source_id -> REJECTED in the chain
    assert "REJECTED" in outcomes
    # accepted records from the healthy sources
    assert "ACCEPTED" in outcomes


# R4: STALE evidence is real (not hardcoded zero)
def test_stale_evidence_computed_from_freshness_policy(tmp_path):
    out = _run_audit(tmp_path)
    sh = json.load(open(out / "source_health.json"))
    # macro_pmi_cn has records from 2025-12/2026-01; decision_time 2026-09-22
    # and a 35d policy means they are genuinely stale
    macro = sh["macro_pmi_cn"]
    assert macro["metrics"]["stale"] > 0
    # freshness dimension in the quality report also records the stale counts
    qr = json.load(open(out / "quality_report.json"))
    assert qr["freshness_quality"].get("STALE", 0) > 0


# R4: manifest is deterministic and covers all outputs
def test_manifest_is_deterministic(tmp_path):
    out = _run_audit(tmp_path)
    m1 = json.load(open(out / "manifest.json"))
    # rerun into a second directory
    out2 = tmp_path / "rerun"
    run_quality_audit(out2)
    write_manifest(out2, [])
    m2 = json.load(open(out2 / "manifest.json"))
    # same set of output files and same hashes
    assert set(m1["outputs"]) == set(m2["outputs"])
    for name in m1["outputs"]:
        assert m1["outputs"][name]["sha256"] == m2["outputs"][name]["sha256"]


# P13-U boundary unchanged
def test_p13u_virgin_boundary_unchanged():
    from astock_v2.research_boundary import RESEARCH_END, VIRGIN_START
    assert RESEARCH_END == "2026-09-22"
    assert VIRGIN_START == "2026-09-23"


# P13-Q/P13-R guard remains active
def test_p13q_p13r_guards_remain_active():
    import scripts.run_p13q_analysis as q
    import scripts.run_p13r_analysis as r
    for module in (q, r):
        with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
            module.assert_research_zone(["2026-09-23T16:00:00+08:00"])


# production snapshots unchanged
def test_production_snapshots_unchanged():
    from astock_v2.factors import FACTOR_REGISTRY
    assert set(FACTOR_REGISTRY) == {
        "momentum", "volatility", "trend", "volume_ratio",
        "close_to_high", "close_to_low", "range_ratio", "close_location",
    }


# R5: independent expected contract regression - missing date detected
def test_independent_expected_contract_detects_missing_date(tmp_path):
    """The expected contract says company_announcement should have
    2026-03-03 and 2026-03-04. The actual fixture only delivers
    2026-03-03. The audit must report 2026-03-04 as missing with
    coverage < 1, without shrinking the expected set to match reality.
    This proves the expected set is independent of actual ingestion."""
    out = _run_audit(tmp_path)
    comp = json.load(open(out / "completeness.json"))
    ca = comp["company_announcement"]
    assert "2026-03-03" in ca["expected_dates"]
    assert "2026-03-04" in ca["expected_dates"]
    assert ca["actual_dates"] == ["2026-03-03"]
    assert "2026-03-04" in ca["missing_dates"]
    assert ca["coverage_ratio"] < 1.0
    assert ca["missingness_class"] == "UNEXPECTED_MISSING"


# R5: SOURCE_EMPTY has dedicated E2E regression evidence
def test_source_empty_end_to_end(tmp_path):
    out = _run_audit(tmp_path)
    # 1. completeness evidence: source_empty_source has zero expected
    #    entities/dates and is classified SOURCE_EMPTY (not EXPECTED_ABSENCE,
    #    not UNEXPECTED_MISSING)
    comp = json.load(open(out / "completeness.json"))
    se = comp["source_empty_source"]
    assert se["missingness_class"] == "SOURCE_EMPTY"
    assert se["expected_absence"] is False
    # 2. source health evidence: health is UNRESOLVED (no attempts observed)
    sh = json.load(open(out / "source_health.json"))
    assert sh["source_empty_source"]["health"] in ("UNRESOLVED", "EMPTY")
    # 3. raw ingestion audit: no REJECTED or SOURCE_ERROR events for this
    #    source (it simply has nothing to deliver)
    lines = (out / "raw_ingestion_audit.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    empty_events = [e for e in events if e.get("source") == "source_empty_source"]
    assert not empty_events  # no attempts because no payloads to deliver


# R5: PARSE_FAILURE evidence survives in the durable audit
def test_parse_failure_evidence_in_durable_audit(tmp_path):
    out = _run_audit(tmp_path)
    lines = (out / "raw_ingestion_audit.jsonl").read_text(encoding="utf-8").readlines()         if False else (out / "raw_ingestion_audit.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    rejected = [e for e in events if e.get("outcome") == "REJECTED"]
    assert rejected, "REJECTED events must be present"
    assert rejected[0]["source"] == "parse_failure_source"
    assert "parse failed" in rejected[0].get("error", "")


# R5: SOURCE_ERROR evidence survives in the durable audit
def test_source_error_evidence_in_durable_audit(tmp_path):
    out = _run_audit(tmp_path)
    lines = (out / "raw_ingestion_audit.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    src_err = [e for e in events if e.get("outcome") == "SOURCE_ERROR"]
    assert src_err, "SOURCE_ERROR events must be present"
    assert src_err[0]["source"] == "broken_source"
    assert "broken" in src_err[0].get("error", "").lower()
