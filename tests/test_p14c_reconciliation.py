"""P14-C cross-source reconciliation invariants (handoff §24 items 13-16)."""
from __future__ import annotations

import json

import pytest

from astock_v2.information import (
    DEFAULT_POLICY,
    ReconciliationPolicy,
    RawInformationRecord,
    reconcile,
    reconcile_pair,
)


def _record(source, value, event_time="2026-01-31T09:00:00+08:00",
            entity_id="CN", unit="index"):
    return RawInformationRecord(
        source=source, source_id=f"{source}_{entity_id}",
        source_category="MACRO", entity_id=entity_id,
        entity_type="ECONOMY", event_time=event_time,
        available_time="2026-02-01T09:00:00+08:00",
        ingested_at="2026-02-01T10:00:00+08:00",
        value=value, unit=unit)


# 13./14. cross-source consistency and conflict
def test_two_sources_same_value_consistent():
    result = reconcile([_record("src_a", 100.0), _record("src_b", 100.0)])
    group = result["groups"][0]
    assert group["status"] == "CONSISTENT"
    assert group["difference"] == 0.0


def test_two_sources_different_values_conflict_with_provenance():
    result = reconcile([_record("src_a", 100.0), _record("src_b", 101.0)])
    group = result["groups"][0]
    assert group["status"] == "CONFLICT"
    assert group["difference"] == 1.0
    assert abs(group["relative_difference"] - 1.0 / 101.0) < 1e-12
    sources = {s["source"]: s["value"] for s in group["sources"]}
    assert sources == {"src_a": 100.0, "src_b": 101.0}  # both preserved


# 15. tolerance policy
def test_tolerance_policy_absolute_and_relative():
    strict = ReconciliationPolicy(
        policy_id="strict", policy_version="1",
        absolute_tolerance=0.0, relative_tolerance=0.0)
    loose = ReconciliationPolicy(
        policy_id="loose", policy_version="1",
        absolute_tolerance=0.5, relative_tolerance=0.01)
    assert reconcile_pair(100.0, 100.4, strict) == "CONFLICT"
    assert reconcile_pair(100.0, 100.4, loose) == "CONSISTENT"
    # relative tolerance: 0.5% of 1000 = 5
    rel = ReconciliationPolicy(
        policy_id="rel", policy_version="1",
        absolute_tolerance=0.0, relative_tolerance=0.005)
    assert reconcile_pair(1000.0, 1004.0, rel) == "CONSISTENT"
    assert reconcile_pair(1000.0, 1006.0, rel) == "CONFLICT"


def test_reconciliation_policy_is_versioned_and_recorded():
    result = reconcile([_record("src_a", 1.0)])
    group = result["groups"][0]
    assert group["status"] == "INSUFFICIENT_SOURCES"
    assert group["policy_id"] == DEFAULT_POLICY.policy_id
    assert group["policy_version"] == DEFAULT_POLICY.policy_version


def test_reconciliation_is_deterministic():
    records = [_record("src_a", 100.0), _record("src_b", 101.0)]
    first = json.dumps(reconcile(records), sort_keys=True)
    second = json.dumps(reconcile(reversed(records)), sort_keys=True)
    assert first == second
