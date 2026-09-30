"""P14-C production implementation tests.

Proves that the PRODUCTION code (astock_v2.information.expected_contract
and the run_p14c_quality_audit execution path) satisfies the frozen
P14-C Contract semantics — including the frozen Golden fixtures' expected
answers, which are consumed here as read-only oracle data (the golden
layer itself is untouched).

Covered mandate cases:
  A normal complete            -> OBSERVED / NONE, coverage 1.0
  B EXPECTED_ABSENCE           -> declared pairs only, never in denominator
  C UNEXPECTED_MISSING         -> required pair absent, reduces coverage
  D SOURCE_EMPTY               -> fetch succeeds, returns []
  E SOURCE_ERROR               -> fetch raises
  F PARSE_FAILURE              -> fetch returns data, parse raises
None of D/E/F is ever reinterpreted as EXPECTED_ABSENCE.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astock_v2.information.expected_contract import (
    BANNED_ABSENCE_CONTROL_KEY,
    CONTRACT_CONTROL_FIELDS,
    ExpectedContract,
    build_expected_contracts,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "contracts" / "p14c" / "fixtures"


# ----------------------------------------------------------- production unit

def _contract(entry):
    return ExpectedContract("s1", entry)


def test_case_a_normal_complete():
    c = _contract({"expected_entities": ["A", "B"], "expected_dates": ["2026-03-02"]})
    comp = c.completeness([("A", "2026-03-02"), ("B", "2026-03-02")])
    assert comp["coverage_ratio"] == 1.0
    assert comp["missing_pairs"] == []
    assert c.source_missingness_class([("A", "2026-03-02"), ("B", "2026-03-02")]) == "NONE"
    assert c.classify_pairs([("A", "2026-03-02"), ("B", "2026-03-02")]) == {
        ("A", "2026-03-02"): "OBSERVED", ("B", "2026-03-02"): "OBSERVED"}


def test_case_b_expected_absence_never_in_denominator():
    c = _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02", "2026-03-03"],
                   "expected_absence_pairs": [["A", "2026-03-03"]]})
    # only the required pair delivered; the declared-absent pair is unobserved
    comp = c.completeness([("A", "2026-03-02")])
    assert comp["expected_count"] == 1          # |R| = |P| - |X|
    assert comp["actual_count"] == 1            # |A ∩ R|
    assert comp["coverage_ratio"] == 1.0        # absence does not reduce coverage
    assert comp["missing_pairs"] == []
    assert comp["expected_absence_pairs"] == [["A", "2026-03-03"]]
    assert c.classify_pairs([("A", "2026-03-02")])[("A", "2026-03-03")] == "EXPECTED_ABSENCE"
    assert c.source_missingness_class([("A", "2026-03-02")]) == "EXPECTED_ABSENCE"


def test_case_b_absence_never_counts_as_observation_or_anomaly():
    c = _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02"],
                   "expected_absence_pairs": [["A", "2026-03-02"]]})
    comp = c.completeness([])                   # nothing observed at all
    assert comp["expected_count"] == 0
    assert comp["actual_count"] == 0
    assert comp["coverage_ratio"] == 1.0        # R empty -> 1.0 by §9.2
    assert comp["missing_pairs"] == []
    # the pair is contract-declared absence, NOT SOURCE_EMPTY/ERROR/PARSE/UNEXPECTED
    assert c.classify_pairs([])[("A", "2026-03-02")] == "EXPECTED_ABSENCE"


def test_case_c_unexpected_missing_reduces_coverage():
    c = _contract({"expected_entities": ["A", "B"], "expected_dates": ["2026-03-02"]})
    comp = c.completeness([("A", "2026-03-02")])
    assert comp["missing_pairs"] == [["B", "2026-03-02"]]
    assert comp["coverage_ratio"] == 0.5
    assert c.classify_pairs([("A", "2026-03-02")])[("B", "2026-03-02")] == "UNEXPECTED_MISSING"
    assert c.source_missingness_class([("A", "2026-03-02")]) == "UNEXPECTED_MISSING"


# ---------------- P14-C-COMP-BLOCKER-001 regression (required-universe gaps)

def test_comp_blocker_001_case1_partial_declared_absence():
    """Declared absence must not leak into missing_entities/missing_dates."""
    c = _contract({"expected_entities": ["A"],
                   "expected_dates": ["2026-03-02", "2026-03-03"],
                   "expected_absence_pairs": [["A", "2026-03-03"]]})
    comp = c.completeness([("A", "2026-03-02")])
    assert comp["missing_entities"] == []
    assert comp["missing_dates"] == []
    assert comp["missing_pairs"] == []
    assert comp["expected_count"] == 1
    assert comp["actual_count"] == 1
    assert comp["coverage_ratio"] == 1.0


def test_comp_blocker_001_case2_entire_entity_declared_absent():
    c = _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02"],
                   "expected_absence_pairs": [["A", "2026-03-02"]]})
    comp = c.completeness([])
    assert comp["expected_count"] == 0
    assert comp["actual_count"] == 0
    assert comp["coverage_ratio"] == 1.0
    assert comp["missing_entities"] == []
    assert comp["missing_dates"] == []
    assert comp["missing_pairs"] == []


def test_comp_blocker_001_case3_mixed_required_and_absence():
    """Two entities x two dates: one declared absent, one required observed,
    one required missing — and an out-of-P actual pair must not satisfy
    anything."""
    c = _contract({"expected_entities": ["A", "B"],
                   "expected_dates": ["2026-03-02", "2026-03-03"],
                   "expected_absence_pairs": [["A", "2026-03-03"]]})
    # R = {(A,02),(B,02),(B,03)}; observed: (A,02) required, (B,03) missing;
    # (Z,02) is outside P and must satisfy nothing
    comp = c.completeness([("A", "2026-03-02"), ("Z", "2026-03-02")])
    assert comp["expected_count"] == 3              # |R|, X excluded
    assert comp["actual_count"] == 1                # |A ∩ R|
    assert comp["coverage_ratio"] == round(1 / 3, 4)
    assert comp["missing_pairs"] == [["B", "2026-03-02"], ["B", "2026-03-03"]]
    # declared-absent (A,03) is absent from A_pair yet enters no missing set;
    # the date 03-03 is missing only because the REQUIRED pair (B,03) is
    # unobserved
    assert comp["missing_entities"] == ["B"]
    assert comp["missing_dates"] == ["2026-03-03"]
    assert comp["expected_absence_pairs"] == [["A", "2026-03-03"]]
    assert c.source_missingness_class([("A", "2026-03-02"), ("Z", "2026-03-02")]) \
        == "UNEXPECTED_MISSING"


def test_contract_structurally_rejects_control_fields():
    """Anti-cheat as production code: control fields raise, never interpret."""
    for field in CONTRACT_CONTROL_FIELDS:
        with pytest.raises(ValueError, match="forbidden"):
            _contract({"expected_entities": ["A"], "expected_dates": [], field: True})
    with pytest.raises(ValueError, match=BANNED_ABSENCE_CONTROL_KEY):
        _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02"],
                   BANNED_ABSENCE_CONTROL_KEY: True})
    with pytest.raises(ValueError, match="outside E x D"):
        _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02"],
                   "expected_absence_pairs": [["A", "2026-03-09"]]})


def test_declaration_provenance_is_type_c_only():
    c = _contract({"expected_entities": ["A"], "expected_dates": ["2026-03-02", "2026-03-03"],
                   "expected_absence_pairs": [["A", "2026-03-03"]]})
    prov = c.declaration_provenance()
    assert len(prov) == 1
    entry = prov[0]
    assert set(entry) == {"source_id", "expected_contract_id",
                          "entity_date_pair_scope", "declaration_reference"}
    assert entry["entity_date_pair_scope"] == {"entity_id": "A", "date": "2026-03-03"}
    assert "expected_absence_pairs[0]" in entry["declaration_reference"]
    for observation_only in ("observed_at", "adapter_version", "ingestion_id",
                             "available_time", "ingested_at", "raw_payload_hash"):
        assert observation_only not in entry


def test_production_outputs_deterministic():
    entry = {"expected_entities": ["B", "A"], "expected_dates": ["2026-03-03", "2026-03-02"],
             "expected_absence_pairs": [["B", "2026-03-03"]]}
    runs = [json.dumps(build_expected_contracts({"s1": entry})["s1"].completeness(
        [("A", "2026-03-02")]), sort_keys=True) for _ in range(2)]
    assert runs[0] == runs[1]


# --------------------------------- production execution path (audit runner)

def _audit(tmp_path):
    from scripts.run_p14c_quality_audit import run_quality_audit
    out = tmp_path / "audit"
    run_quality_audit(out)
    return json.load(open(out / "completeness.json"))


def test_case_d_source_empty_not_reinterpreted(tmp_path):
    comp = _audit(tmp_path)
    se = comp["source_empty_source"]
    assert se["missingness_class"] == "SOURCE_EMPTY"   # fetch succeeded, returned []
    assert se["missingness_class"] != "EXPECTED_ABSENCE"
    assert se["expected_absence_evidence"] == []        # no declaration exists


def test_case_e_source_error_not_reinterpreted(tmp_path):
    comp = _audit(tmp_path)
    err = comp["broken_source"]
    assert err["missingness_class"] == "SOURCE_ERROR"   # fetch raises
    assert err["missingness_class"] != "EXPECTED_ABSENCE"
    assert err["expected_absence_evidence"] == []


def test_case_f_parse_failure_not_reinterpreted(tmp_path):
    comp = _audit(tmp_path)
    pf = comp["parse_failure_source"]
    assert pf["missingness_class"] == "PARSE_FAILURE"   # data returned, parse raises
    assert pf["missingness_class"] != "EXPECTED_ABSENCE"
    assert pf["expected_absence_evidence"] == []
    # the parse-failed required pair is also reported at pair granularity
    assert pf["missing_pairs"] == [["CN", "2026-03-01"]]


def test_production_expected_absence_end_to_end(tmp_path):
    comp = _audit(tmp_path)
    us = comp["us_index_daily"]
    # declared absence: pair not required, coverage untouched, Type C evidence
    assert us["expected_absence_pairs"] == [["SPX", "2026-03-03"]]
    assert us["expected_count"] == 1
    assert us["coverage_ratio"] == 1.0
    assert us["missingness_class"] == "EXPECTED_ABSENCE"
    # P14-C-COMP-BLOCKER-001: the declared-absence date leaks into NO
    # missing set
    assert us["missing_pairs"] == []
    assert us["missing_entities"] == []
    assert us["missing_dates"] == []
    prov = us["expected_absence_evidence"]
    assert len(prov) == 1
    assert prov[0]["entity_date_pair_scope"] == {"entity_id": "SPX", "date": "2026-03-03"}
    assert set(prov[0]) == {"source_id", "expected_contract_id",
                            "entity_date_pair_scope", "declaration_reference"}


def test_production_completeness_dimension_not_failed_by_absence(tmp_path):
    """P14-C-COMP-BLOCKER-001 Case 4: the completeness quality dimension
    must not count us_index_daily as failing because its declared-absence
    date was not observed."""
    from scripts.run_p14c_quality_audit import run_quality_audit
    out = tmp_path / "audit"
    run_quality_audit(out)
    qr = json.load(open(out / "quality_report.json"))
    dim = qr["dimensions"]["completeness"]
    failing_sources = {e["source"] for e in dim["evidence"]
                       if e.get("missing_entities") or e.get("missing_dates")
                       or e.get("missing_pairs")}
    assert "us_index_daily" not in failing_sources
    assert failing_sources == {"company_announcement", "parse_failure_source"}


# ------------------------- golden fixtures consumed through production code

def _fixture(golden_id: str) -> dict:
    path = next(FIXTURE_DIR.glob(f"{golden_id}_*.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def _production_entry(fixture: dict) -> ExpectedContract:
    (source_id, entry), = fixture["input"]["expected_contract"].items()
    return ExpectedContract(source_id, entry)


@pytest.mark.parametrize("gid", ["G-012", "G-015", "G-016", "G-017",
                                 "G-018", "G-019", "G-020"])
def test_golden_completeness_satisfied_by_production(gid: str):
    """The frozen golden expected answers are satisfied by the production
    implementation (golden layer untouched; fixtures are read-only oracles)."""
    fx = _fixture(gid)
    entry = _production_entry(fx)
    actual = [tuple(p) for p in fx["input"].get("actual_pairs", [])]
    comp = entry.completeness(actual)
    exp = fx["expected"]

    if "expected_pairs" in exp:                                    # G-015
        assert comp["expected_pairs"] == [list(p) for p in exp["expected_pairs"]]
        assert comp["expected_count"] == exp["expected_count"]
        return
    count_key = ("required_expected_count"
                 if "required_expected_count" in exp else "expected_count")
    if count_key in exp:                                           # G-016..G-020
        assert comp["expected_count"] == exp[count_key]
        assert comp["actual_count"] == exp["actual_count"]
        assert abs(comp["coverage_ratio"] - exp["coverage_ratio"]) < 1e-3
    for key in ("missing_entities", "missing_dates"):
        if key in exp:
            assert comp[key] == exp[key], (gid, key)
    if "missing_pairs" in exp:
        assert comp["missing_pairs"] == [list(p) for p in exp["missing_pairs"]]
    if "entities_in_expected_but_not_in_actual" in exp:            # G-012
        assert comp["missing_entities"] == exp["entities_in_expected_but_not_in_actual"]
    if "absence_pairs_reported" in exp:                            # G-020
        assert comp["expected_absence_pairs"] == [list(p) for p in exp["absence_pairs_reported"]]
        assert entry.declaration_provenance()[0]["entity_date_pair_scope"] == {
            "entity_id": exp["absence_pairs_reported"][0][0],
            "date": exp["absence_pairs_reported"][0][1]}
    if "entities_in_expected_but_not_in_actual" in exp:            # G-012
        assert comp["missing_entities"] == exp["entities_in_expected_but_not_in_actual"]


@pytest.mark.parametrize("gid", ["G-006", "G-009", "G-010"])
def test_golden_missingness_classification_satisfied_by_production(gid: str):
    """UNEXPECTED_MISSING is exactly 'required pair, not declared, not
    observed' in production — the golden expected classification holds."""
    fx = _fixture(gid)
    entry = _production_entry(fx)
    actual = [tuple(p) for p in fx["input"].get("actual_pairs", [])]
    classification = entry.classify_pairs(actual)
    unexpected = sorted(p for p, k in classification.items() if k == "UNEXPECTED_MISSING")
    declared_absent = sorted(p for p, k in classification.items() if k == "EXPECTED_ABSENCE")
    if gid == "G-006":
        assert declared_absent == []            # nothing declared -> no absence
        assert unexpected != []                 # required pair absent
    elif gid == "G-009":
        assert unexpected == [tuple(p) for p in fx["expected"]["undeclared_missing_pair"]]
        assert fx["expected"]["missingness"] == "UNEXPECTED_MISSING"
    else:                                       # G-010
        assert unexpected, fx["expected"]
        assert fx["expected"]["missingness"] == "UNEXPECTED_MISSING"
        assert sorted(entry.completeness(actual)["missing_entities"]) == \
            sorted(fx["expected"]["missing_entities"])


def test_golden_empty_vs_absence_satisfied_by_production():
    """G-007: production keeps SOURCE_EMPTY (observation evidence) and
    EXPECTED_ABSENCE (declaration) strictly apart."""
    fx = _fixture("G-007")
    entry = _production_entry(fx)
    classification = entry.classify_pairs([])
    assert classification[("SW801040", "2026-03-02")] == "EXPECTED_ABSENCE"
    assert classification[("SW801010", "2026-03-02")] == "UNEXPECTED_MISSING"
    # the fixture's observation carries the SOURCE_EMPTY evidence; production
    # maps observation_type SOURCE_EMPTY to the source-level class, never to
    # a declaration
    obs = fx["input"]["observations"][0]
    assert obs["observation_type"] == "SOURCE_EMPTY"
    assert obs["observation_type"] != "EXPECTED_ABSENCE"
