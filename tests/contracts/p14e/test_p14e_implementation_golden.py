"""P14-E-006 Implementation Golden Tests — frozen standard answers for the
P14-E Evidence Runtime / EvidenceStore / Bundle / Reverse Trace production
implementation.

The fixtures IG-101..IG-107 carry hand-written expected values; the engine
(golden/implementation.py) transcribes the accepted P14-E-004 Production
Contract v1.1 + P14-E-005 Implementation Contract v1.0 semantics as the
oracle. The future production implementation is graded against these same
fixtures — it can never define its own standard answer.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "p14e_impl", HERE / "golden" / "implementation.py")
impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(impl)

FIXTURES = impl.load_implementation_fixtures()


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["golden_id"])
def test_implementation_golden_standard_answer(fixture):
    results = impl.check_implementation_fixture(fixture)
    assert results, "fixture produced no checks"
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, f"{fixture['golden_id']} violations: {failures}"
    consumption = [r for r in results if r[0].endswith("expected_consumed")]
    assert consumption and consumption[0][1], \
        f"{fixture['golden_id']} has unconsumed expected fields"


def test_implementation_ids_dense():
    assert [f["golden_id"] for f in FIXTURES] == \
        [f"P14E-IG-{i:03d}" for i in range(101, 108)]


def test_implementation_closure():
    results = impl.check_implementation_closure()
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, failures


def test_four_class_taxonomy_frozen():
    assert impl.REVERSE_TRACE_CLASSES == (
        "REVERSE_TRACE_NOT_FOUND",
        "REVERSE_TRACE_AMBIGUOUS",
        "REVERSE_TRACE_IDENTITY_MISMATCH",
        "RAW_RECORD_CORRUPTED",
    )


def test_lifecycle_states_frozen():
    assert impl.LIFECYCLE_STATES == ["CREATE", "VALIDATE", "FREEZE", "STORED"]
    assert impl.LIFECYCLE_ALLOWED == {
        "CREATE": {"VALIDATE"},
        "VALIDATE": {"FREEZE"},
        "FREEZE": {"STORED"},
        "STORED": set(),
    }


def test_failure_layers_frozen():
    assert impl.FAILURE_LAYERS == (
        "input_validation", "authority_violation", "pit_violation",
        "identity_failure", "storage_failure", "trace_failure",
    )


def test_no_production_runtime_files():
    results = core_source_scan()
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, failures


def core_source_scan():
    return impl.core.check_source_scan()
