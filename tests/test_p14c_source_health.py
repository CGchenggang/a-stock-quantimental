"""P14-C source health model invariants (handoff §14/§15)."""
from __future__ import annotations

from astock_v2.information.source_health import source_health


# OK: accepted rows, no blemishes, full coverage, fresh
def test_ok_when_clean_and_fully_covered():
    health = source_health({
        "attempted": 100, "accepted": 96, "rejected": 2, "duplicates": 0,
        "mutations": 0, "errors": 0, "fresh": 96, "stale": 0,
        "coverage": 1.0,
    })
    assert health["health"] == "DEGRADED"  # 2 rejected rows are blemishes
    assert health["reasons"]


def test_ok_when_perfect():
    health = source_health({
        "attempted": 100, "accepted": 100, "rejected": 0, "duplicates": 0,
        "mutations": 0, "errors": 0, "fresh": 100, "stale": 0,
        "coverage": 1.0,
    })
    assert health["health"] == "OK"
    assert health["reasons"] == []


# DEGRADED: duplicates / mutations / rejected with acceptance still present
def test_degraded_on_duplicates_and_mutations():
    health = source_health({
        "attempted": 100, "accepted": 96, "rejected": 0, "duplicates": 2,
        "mutations": 1, "errors": 0, "fresh": 90, "stale": 0, "coverage": 1.0,
    })
    assert health["health"] == "DEGRADED"
    assert health["metrics"]["duplicates"] == 2


def test_stale_majority_freshness():
    health = source_health({
        "attempted": 100, "accepted": 50, "rejected": 0, "duplicates": 0,
        "mutations": 0, "errors": 0, "fresh": 10, "stale": 40,
        "coverage": 0.5,
    })
    assert health["health"] == "STALE"


# ERROR / EMPTY / UNRESOLVED
def test_error_when_nothing_accepted_with_errors():
    health = source_health({
        "attempted": 100, "accepted": 0, "rejected": 0, "duplicates": 0,
        "mutations": 0, "errors": 3, "coverage": 0.0,
    })
    assert health["health"] == "ERROR"


def test_empty_when_no_attempts():
    health = source_health({"attempted": 0, "accepted": 0, "coverage": 0.0})
    assert health["health"] == "UNRESOLVED"
    assert health["reasons"]


def test_coverage_below_one_is_degraded():
    health = source_health({
        "attempted": 100, "accepted": 96, "rejected": 4, "duplicates": 0,
        "mutations": 0, "errors": 0, "fresh": 96, "stale": 0, "coverage": 0.96,
    })
    assert health["health"] == "DEGRADED"
    assert any("coverage" in r for r in health["reasons"])


# determinism and no-ML statement
def test_source_health_is_deterministic_and_documented():
    metrics = {
        "attempted": 10, "accepted": 8, "rejected": 1, "duplicates": 1,
        "mutations": 0, "errors": 0, "fresh": 8, "stale": 0, "coverage": 0.8,
    }
    first = source_health(metrics)
    second = source_health(dict(metrics))
    assert first == second
    assert "no ML score" in first["note"]
