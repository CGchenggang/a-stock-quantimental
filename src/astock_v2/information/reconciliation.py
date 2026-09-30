"""Deterministic cross-source reconciliation for the information layer.

Two sources reporting the same fact (entity_id + event_time + unit) are
reconciled under an explicit, frozen tolerance policy:

    consistent   iff  |a - b| <= max(absolute_tolerance,
                                     relative_tolerance * max(|a|, |b|))
    CONFLICT     otherwise

Every comparison keeps both values, their difference, relative difference,
timestamps and provenance. Nothing is auto-resolved — no "source A wins",
no averaging. The policy is versioned infrastructure configuration, never
tuned from data results.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import RawInformationRecord


@dataclass(frozen=True)
class ReconciliationPolicy:
    policy_id: str
    policy_version: str
    absolute_tolerance: float
    relative_tolerance: float
    description: str = ""


DEFAULT_POLICY = ReconciliationPolicy(
    policy_id="p14c_reconciliation_default",
    policy_version="1",
    absolute_tolerance=0.0,
    relative_tolerance=0.0,
    description="strict equality until a source-specific frozen tolerance "
                "is documented; any nonzero difference is a CONFLICT",
)


def _group_key(record: RawInformationRecord) -> tuple:
    return (record.entity_id, record.entity_type, record.event_time,
            record.unit, record.currency)


def reconcile(records: Iterable[RawInformationRecord],
              policy: ReconciliationPolicy = DEFAULT_POLICY) -> dict:
    """Reconcile numeric values across sources, deterministically.

    Returns per-group status (CONSISTENT / CONFLICT / INSUFFICIENT_SOURCES)
    with both values, their difference, relative difference, timestamps and
    provenance preserved. Groups and rows are sorted for stable output.
    """
    groups: dict[tuple, list[RawInformationRecord]] = {}
    for record in records:
        if record.value is None:
            continue
        groups.setdefault(_group_key(record), []).append(record)

    results = []
    for key in sorted(groups):
        rows = sorted(groups[key],
                      key=lambda r: (r.available_time, r.source, r.source_id))
        values = [float(r.value) for r in rows]
        if len(values) < 2:
            status = "INSUFFICIENT_SOURCES"
            difference = None
            relative_difference = None
        else:
            reference = max(abs(v) for v in values)
            difference = max(values) - min(values)
            relative_difference = (
                difference / reference if reference > 0 else difference
            )
            consistent = (
                abs(difference) <= policy.absolute_tolerance
                or (reference > 0 and abs(difference)
                    <= policy.relative_tolerance * reference)
            )
            status = "CONSISTENT" if consistent else "CONFLICT"
        results.append({
            "entity_id": key[0], "entity_type": key[1], "event_time": key[2],
            "unit": key[3], "currency": key[4],
            "status": status,
            "policy_id": policy.policy_id,
            "policy_version": policy.policy_version,
            "sources": [
                {"source": r.source, "source_id": r.source_id,
                 "value": float(r.value),
                 "available_time": r.available_time}
                for r in rows
            ],
            "difference": difference,
            "relative_difference": relative_difference,
        })
    return {"policy": {"policy_id": policy.policy_id,
                       "policy_version": policy.policy_version,
                       "absolute_tolerance": policy.absolute_tolerance,
                       "relative_tolerance": policy.relative_tolerance},
            "groups": results}


def reconcile_pair(value_a: float, value_b: float,
                   policy: ReconciliationPolicy = DEFAULT_POLICY) -> str:
    """Two-source verdict under the frozen tolerance policy."""
    reference = max(abs(value_a), abs(value_b))
    difference = abs(value_a - value_b)
    if difference <= policy.absolute_tolerance:
        return "CONSISTENT"
    if reference > 0 and difference <= policy.relative_tolerance * reference:
        return "CONSISTENT"
    return "CONFLICT"
