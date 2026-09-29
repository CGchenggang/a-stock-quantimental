"""Explicit freshness policies for the information layer.

PIT and freshness are different questions:

- PIT:  could the researcher see this at decision_time?  (available_time
  <= decision_time) — see pit.py.
- Freshness: at decision_time, is this information still new enough to be
  usable?  (decision_time - available_time <= policy.max_age)

Freshness is therefore measured from ``available_time`` (never from
``event_time``) and every record carries an explicit
``freshness_policy_id``; using one global window for every source is not
allowed. Statuses: ``fresh`` / ``stale`` / ``unknown`` (no policy id on
the record) / ``missing_policy`` (policy id not present in the provided
policies).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import RawInformationRecord, parse_boundary

FRESH = "fresh"
STALE = "stale"
UNKNOWN = "unknown"
MISSING_POLICY = "missing_policy"


@dataclass(frozen=True)
class FreshnessPolicy:
    policy_id: str
    max_age_seconds: float
    description: str = ""


def freshness_status(
    record: RawInformationRecord,
    decision_time: str,
    policies: dict[str, FreshnessPolicy],
) -> str:
    policy_id = record.freshness_policy_id
    if not policy_id:
        return UNKNOWN
    policy = policies.get(policy_id)
    if policy is None:
        return MISSING_POLICY
    decision = parse_boundary(decision_time)
    available = parse_boundary(record.available_time)
    age = (decision - available).total_seconds()
    if age < 0:
        # information cannot be fresher than its own availability; a
        # decision before availability is a PIT failure handled elsewhere.
        return STALE
    return FRESH if age <= policy.max_age_seconds else STALE


def freshness_summary(
    records: Iterable[RawInformationRecord],
    decision_time: str,
    policies: dict[str, FreshnessPolicy],
) -> dict:
    counts: dict[str, int] = {FRESH: 0, STALE: 0, UNKNOWN: 0, MISSING_POLICY: 0}
    for record in records:
        counts[freshness_status(record, decision_time, policies)] += 1
    counts["n"] = sum(v for k, v in counts.items() if k != "n")
    return counts
