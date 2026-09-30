"""P14-C Golden Tests — frozen standard answers for the future production
implementation.

Workflow position (mandate §1):

    Design Contract -> Acceptance Harness (PASS) -> GOLDEN TESTS (this file)
    -> Independent Acceptance -> P14-C Production Implementation

These tests validate the FROZEN FIXTURES themselves:

- every expected value is a hand-written literal inside the fixture JSON;
  nothing here derives an expectation from a P14-C implementation
  (anti-cheat checks A-E below enforce that mechanically);
- arithmetic self-consistency: the hand-written numbers are re-derived from
  the fixture's own DECLARED sets using the frozen contract formulas;
- authority cross-checks: P14-A (PIT / freshness / timestamps), P14-B
  (RawStore durable ingestion) and P13-U (research boundary) are replayed
  read-only and their frozen outcomes must match the standard answers;
- coverage closure: every canonical Contract ID in the frozen Acceptance
  Matrix maps to at least one golden fixture;
- determinism: the canonical report is byte-identical across reruns and
  contains no runtime timestamp / UUID / machine path.

A future P14-C production implementation is graded AGAINST these fixtures;
it can never define its own standard answer.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "p14c_golden_core", _HERE / "golden" / "core.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)


# ----------------------------------------------------------- per-fixture gate

@pytest.fixture(scope="module")
def fixtures():
    return core.load_fixtures()


@pytest.mark.parametrize("fixture", core.load_fixtures(), ids=lambda f: f["golden_id"])
def test_golden_fixture_standard_answer(fixture):
    """Every check inside one fixture must pass."""
    results = core.check_fixture(fixture)
    assert results, "fixture produced no checks"
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, f"{fixture['golden_id']} standard answer violations: {failures}"


def test_fixture_ids_dense_and_unique(fixtures):
    ids = [f["golden_id"] for f in fixtures]
    assert ids == [f"P14C-GOLD-{i:03d}" for i in range(1, len(ids) + 1)]
    assert len(fixtures) == 64


# ------------------------------------------------------------- global gates

def test_schema_and_matrix_trace(fixtures):
    failures = [(n, d) for n, ok, d in core.check_schema(fixtures) if not ok]
    assert not failures, failures
    for f in fixtures:
        assert f["contract_ids"] == f["matrix_ids"]


def test_coverage_matrix_closure(fixtures):
    failures = [(n, d) for n, ok, d in core.check_coverage(fixtures) if not ok]
    assert not failures, failures
    covered = {c for f in fixtures for c in f["contract_ids"]}
    assert covered == core.matrix_ids()


def test_boundary_all_dates_in_research_zone(fixtures):
    failures = [(n, d) for n, ok, d in core.check_boundary_dates(fixtures) if not ok]
    assert not failures, failures


def test_anticheat_no_fixture_control_fields(fixtures):
    failures = [(n, d) for n, ok, d in core.check_anticheat_fixtures(fixtures) if not ok]
    assert not failures, failures


def test_anticheat_no_implementation_derivation():
    """Checks A + E: the golden layer must not import the P14-C production
    implementation (quality / reconciliation / source_health / adapters /
    the P14-C audit script)."""
    failures = [(n, d) for n, ok, d in core.check_anticheat_layer() if not ok]
    assert not failures, failures


def test_anticheat_expected_not_derived_from_actual(fixtures):
    """Check B: fixtures where actual != expected prove the expected sets are
    declared a priori rather than derived from the payload."""
    exp_fixture = next(f for f in fixtures
                       if f["contract_ids"] == ["P14C-EXP-001"])
    entry = exp_fixture["input"]["expected_contract"]["cn_stock_quote"]
    actual_entities = {p[0] for p in exp_fixture["input"]["actual_pairs"]}
    assert set(entry["expected_entities"]) - actual_entities == {"600001", "600002"}


def test_anticheat_contract_pinned():
    """Check D: the contract/matrix bytes are pinned; a silent contract edit
    fails the golden layer instead of re-blessing the answers."""
    failures = [(n, d) for n, ok, d in core.check_contract_pinned() if not ok]
    assert not failures, failures


def test_recon_001_vs_006_distinct(fixtures):
    """Mandate §26: RECON-001 (tolerance classification) and RECON-006
    (output-schema prohibition) must carry demonstrably different semantics.
    They do — therefore no CONTRACT_BLOCKER."""
    failures = [(n, d) for n, ok, d in core.check_recon_001_vs_006(fixtures) if not ok]
    assert not failures, failures


def test_deterministic_report():
    """Contract P14C-DET-001..003: canonical report is byte-identical across
    rebuilds and free of runtime timestamps / UUIDs / machine paths."""
    failures = [(n, d) for n, ok, d in core.det_report_clean() if not ok]
    assert not failures, failures
    report1 = core.canonical_report()
    report2 = core.canonical_report()
    assert report1 == report2
    manifest = json.loads(report1)["manifest"]
    assert manifest["fixture_count"] == 64
    assert len(manifest["fixture_digests"]) == 64


def test_golden_doc_matches_fixtures(fixtures):
    """The coverage doc's table rows must exactly mirror the fixture set."""
    doc = Path(core.REPO_ROOT) / "docs" / "contracts" / "P14-C-GOLDEN-TESTS.md"
    text = doc.read_text(encoding="utf-8")
    for f in fixtures:
        assert f["golden_id"] in text, f"{f['golden_id']} missing from coverage doc"
        for cid in f["contract_ids"]:
            row = next(line for line in text.splitlines() if f["golden_id"] in line)
            assert cid in row, f"{cid} missing from {f['golden_id']} doc row"


def test_all_checks_green():
    """Belt-and-braces: every check produced by the engine must pass."""
    failures = [(n, d) for n, ok, d in core.run_all_checks() if not ok]
    assert not failures, failures
