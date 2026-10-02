"""P14-E Golden Tests — frozen standard answers executed through the
P14-A/P14-B/P14-D authorities and the transcribed contract semantics.

Fixtures G-001..G-012 carry hand-written expected values. The engine
(tests/contracts/p14e/golden/core.py) replays the frozen authorities
(P14-B RawStore identity primitives, P14-A PIT/selection, P14-D
run_query, P13-U guard) and validates every hand-written expectation.
No P14-E production runtime exists or is imported (mechanically
asserted — P14E-016).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "p14e_golden_core", HERE / "golden" / "core.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

FIXTURES = core.load_fixtures()


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["golden_id"])
def test_golden_standard_answer(fixture):
    results = core.check_fixture(fixture)
    assert results, "fixture produced no checks"
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, f"{fixture['golden_id']} violations: {failures}"


def test_golden_ids_dense_and_cover_contracts():
    design = [f for f in FIXTURES if f["golden_id"].startswith("P14E-G-")]
    impl = [f for f in FIXTURES if f["golden_id"].startswith("P14E-IG-")]
    assert [f["golden_id"] for f in design] == \
        [f"P14E-G-{i:03d}" for i in range(1, 13)]
    assert [f["golden_id"] for f in impl] == \
        [f"P14E-IG-{i:03d}" for i in range(101, 108)]
    covered = set()
    for f in FIXTURES:
        covered |= set(f.get("contract_ids", []))
    # P14E-016 is covered by the sanctioned mechanical source scan
    covered |= {"P14E-016"}
    # IG fixtures bind to P14E-I-M-* rows, not design contract IDs
    assert covered == set(f"P14E-{i:03d}" for i in range(1, 18))


def test_anticheat_no_self_proving_structure():
    """Anti-cheat §23: no fixture asserts expected == its own derivation;
    expectations are hand-written literals in the fixture JSON, and no
    test assigns a production result as expected."""
    for fx in FIXTURES:
        text = json.dumps(fx, ensure_ascii=False)
        assert "expected_result" not in text
        assert "golden_override" not in text
    # every expected block is a hand-written literal structure
    for fx in FIXTURES:
        assert isinstance(fx["expected"], dict) and fx["expected"]


def test_anticheat_no_skips():
    harness_sources = [p for p in HERE.glob("test_*.py")]
    harness_sources += list((HERE / "golden").glob("*.py"))
    import re as _re
    for path in harness_sources:
        text = path.read_text(encoding="utf-8")
        text = _re.sub(r'"[^"]*"|' + chr(39) + '[^' + chr(39) + ']*' + chr(39), '""', text)
        for usage in ("pytest.skip(", "@pytest.mark.xfail",
                      "pytest.importorskip("):
            assert usage not in text, (path.name, usage)


def test_anticheat_no_wall_clock():
    """Usage scan: docstrings/string literals naming banned tokens are
    sanctioned prohibitions; only call sites fail."""
    import re as _re
    for path in HERE.glob("golden/core.py"):
        text = path.read_text(encoding="utf-8")
        text = _re.sub(r'"""(?:.|"|"(?!"))*?"""', '""', text, flags=_re.S)
        text = _re.sub(r'"[^"]*"', '""', text)
        for token in ("datetime.now(", "time.time(", "uuid.uuid4(",
                      "random.random(", "Date.now("):
            assert token not in text, token


def test_no_p14e_production_runtime_exists():
    """P14E-016: the information layer contains exactly the pinned modules —
    no evidence/bundle/provenance runtime was added for the golden stage."""
    results = core.check_source_scan()
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, failures


def test_virgin_scan_clean():
    results = core.check_virgin_scan()
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, failures


def test_deterministic_double_run():
    """Same inputs -> same canonical report bytes, twice."""
    report1 = core.canonical_report()
    report2 = core.canonical_report()
    assert report1 == report2
    parsed = json.loads(report1)
    assert parsed["phase"] == "P14-E"
    assert parsed["golden_ids"] == 19
    assert all(v["passed"] for v in parsed["validation"])


def test_expected_consumption_enforced():
    """REPAIR-001 #4: every declared expected leaf must be consumed by an
    assertion. A fixture with an unconsumed expected key must be flagged
    by the engine (mechanically prevents declaration/acceptance-surface
    drift)."""
    fixture = json.loads(json.dumps(
        next(f for f in FIXTURES if f["golden_id"] == "P14E-G-010")))
    fixture["expected"]["bogus_unused_key"] = 1
    results = core.check_fixture(fixture)
    consumption = [r for r in results if r[0].endswith("expected_consumed")]
    assert len(consumption) == 1
    assert consumption[0][1] is False
    assert "bogus_unused_key" in consumption[0][2]


def test_all_checks_green():
    failures = [(n, d) for n, ok, d in core.run_all_checks() if not ok]
    assert not failures, failures
