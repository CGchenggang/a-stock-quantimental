"""P14-C quality layer invariants (handoff §24 items 1-12, 17-20)."""
from __future__ import annotations

import json

import pytest

from astock_v2.information import (
    FRESHNESS_POLICIES,
    QUALITY_ADMISSIBLE,
    QUALITY_WITH_WARNING,
    RawInformationRecord,
    record_quality_decision,
    freshness_quality,
    pit_quality,
    MISSING_POLICY,
    revision_integrity_issues,
    timestamp_issues,
    classify_missingness,
    MISSINGNESS_VOCABULARY,
    MISSING_POLICY,
)


def _record(**overrides):
    base = {
        "source": "macro_pmi_cn", "source_id": "PMI_CN_2026M01",
        "source_category": "MACRO", "entity_id": "CN",
        "entity_type": "ECONOMY",
        "event_time": "2026-01-31T09:00:00+08:00",
        "available_time": "2026-02-01T09:30:00+08:00",
        "revision": 0, "ingested_at": "2026-02-01T10:00:00+08:00",
        "value": 50.1, "unit": "index",
        "freshness_policy_id": "macro_release_35d",
    }
    base.update(overrides)
    return RawInformationRecord(**base)


# 1. completeness / 2. missingness / 3. classification
def test_missingness_classification_vocabulary_and_priority():
    assert set(MISSINGNESS_VOCABULARY) == {
        "EXPECTED_ABSENCE", "UNEXPECTED_MISSING", "SOURCE_EMPTY",
        "SOURCE_ERROR", "PARSE_FAILURE", "UNRESOLVED_AVAILABILITY",
    }
    assert classify_missingness(source_error=True, parse_failure=True) == "SOURCE_ERROR"
    assert classify_missingness(parse_failure=True) == "PARSE_FAILURE"
    assert classify_missingness(availability_unresolved=True) == "UNRESOLVED_AVAILABILITY"
    assert classify_missingness(source_empty=True) == "SOURCE_EMPTY"
    assert classify_missingness(expected_but_absent=True) == "EXPECTED_ABSENCE"
    assert classify_missingness() == "UNEXPECTED_MISSING"


def test_timestamp_malformed_and_timezone_issues():
    """The quality layer must tolerate malformed timestamp fields on a
    shim record (the model itself rejects them at construction)."""
    from types import SimpleNamespace
    record = SimpleNamespace(
        event_time="2026-01-31 09:00",  # malformed (no T / no tz)
        available_time="2026-02-01T09:30:00+08:00",
        ingested_at="2026-02-01T10:00:00+08:00")
    issues = timestamp_issues(record)
    assert any(i["check"] == "event_time_malformed" for i in issues)
    record_bad = SimpleNamespace(
        event_time="2026-01-31T09:00:00+08:00",
        available_time="2026-02-32T09:00:00+08:00",  # invalid date
        ingested_at="2026-02-01T10:00:00+08:00")
    assert any(i["check"] == "available_time_malformed"
               for i in timestamp_issues(record_bad))


def test_ingested_before_available_is_a_violation():
    record = _record(ingested_at="2026-01-01T09:00:00+08:00")
    issues = timestamp_issues(record)
    assert any(i["check"] == "ingested_before_available" for i in issues)


def test_timestamp_semantic_uncertainty_not_guessed():
    """available_time BEFORE event_time: the default contract
    (available_after_event) flags it; an unknown-semantics source reports
    UNKNOWN instead of a verdict."""
    record = _record(event_time="2026-02-10T09:00:00+08:00",
                     available_time="2026-02-01T09:00:00+08:00")
    default = timestamp_issues(record)
    assert any(i["check"] == "available_before_event" for i in default)
    unknown_semantics = timestamp_issues(record, declared_orderings=())
    checks = {i["check"] for i in unknown_semantics}
    assert "available_vs_event_unprovable" in checks


def test_future_timestamp_against_reference():
    record = _record(event_time="2027-01-01T09:00:00+08:00")
    issues = timestamp_issues(record, reference_time="2026-06-01T00:00:00+08:00")
    assert any(i["check"] == "event_time_in_future" for i in issues)


# 6. PIT quality delegation (no second PIT implementation)
def test_pit_quality_delegates_and_counts():
    from types import SimpleNamespace
    good = _record(source_id="A")
    after = SimpleNamespace(available_time="2026-03-01T09:00:00+08:00")
    missing = SimpleNamespace(available_time=None)
    records = [good, after, missing]
    counts = pit_quality(records, "2026-02-15T16:00:00+08:00")
    assert counts["PIT_ADMISSIBLE"] == 1
    assert counts["AVAILABLE_TIME_AFTER_DECISION"] == 1
    assert counts["AVAILABLE_TIME_MISSING"] == 1


# 7./8. freshness quality counts with stale detection
def test_freshness_quality_counts():
    policies = dict(FRESHNESS_POLICIES)
    fresh = _record(available_time="2026-02-01T09:30:00+08:00")
    stale = _record(source_id="OLD", available_time="2025-01-01T09:00:00+08:00")
    from types import SimpleNamespace
    nopolicy = SimpleNamespace(freshness_policy_id=None,
                               available_time="2026-02-01T09:30:00+08:00")
    counts = freshness_quality([fresh, stale, nopolicy],
                               "2026-02-10T00:00:00+08:00", policies)
    assert counts["FRESH"] == 1 and counts["STALE"] == 1
    assert counts["UNKNOWN"] == 1
    decision = record_quality_decision(
        stale, "2026-02-10T00:00:00+08:00", freshness_policies=policies)
    assert decision["quality_status"] == QUALITY_WITH_WARNING
    assert decision["stale"] is True


# 9. revision integrity
def test_revision_integrity_detects_gaps_regression_and_duplicate_revision():
    rows = [
        _record(source_id="PMI", revision=0, available_time="2026-02-01T09:00:00+08:00"),
        _record(source_id="PMI", revision=1, available_time="2026-02-10T09:00:00+08:00"),
        _record(source_id="PMI", revision=4, available_time="2026-02-20T09:00:00+08:00"),  # gap 2,3
    ]
    issues = revision_integrity_issues(rows)
    checks = {i["check"] for i in issues}
    assert "revision_gap" in checks
    # duplicate revision with different payload
    rows.append(_record(source_id="PMI", revision=4,
                        available_time="2026-02-21T09:00:00+08:00", value=77.7))
    issues = revision_integrity_issues(rows)
    assert any(i["check"] == "same_revision_different_payload" for i in issues)
    # regression: rev2 made available EARLIER than rev1
    rows.append(_record(source_id="PMI", revision=2,
                        available_time="2026-02-05T09:00:00+08:00"))
    issues = revision_integrity_issues(rows)
    assert any(i["check"] == "revision_available_time_regression" for i in issues)


def test_revision_anomalies_preserved_not_deleted():
    rows = [
        _record(source_id="PMI", revision=0, available_time="2026-02-01T09:00:00+08:00"),
        _record(source_id="PMI", revision=3, available_time="2026-03-01T09:00:00+08:00"),
    ]
    issues = revision_integrity_issues(rows)
    assert any(i["check"] == "revision_gap" for i in issues)
    assert len(rows) == 2  # preserved


# 17.-20. deterministic output helpers
def test_quality_decision_is_deterministic():
    packet = _record()
    first = record_quality_decision(packet, "2026-02-10T00:00:00+08:00")
    second = record_quality_decision(packet, "2026-02-10T00:00:00+08:00")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def _record(**overrides):
    base = {
        "source": "macro_pmi_cn", "source_id": "PMI_CN_2026M01",
        "source_category": "MACRO", "entity_id": "CN",
        "entity_type": "ECONOMY",
        "event_time": "2026-01-31T09:00:00+08:00",
        "available_time": "2026-02-01T09:30:00+08:00",
        "revision": 0, "ingested_at": "2026-02-01T10:00:00+08:00",
        "value": 50.1, "unit": "index",
        "freshness_policy_id": "macro_release_35d",
    }
    base.update(overrides)
    return RawInformationRecord(**base)
