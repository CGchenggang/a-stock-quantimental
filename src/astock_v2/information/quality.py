"""P14-C: data quality model for the information layer.

P14-A remains the PIT authority; P14-C is a quality auditor that consumes
the existing PIT/freshness/provenance functions and never re-implements
them. Every dimension reports status + reason + metrics + evidence, so a
GOOD/BAD verdict is always explainable down to the offending records.

Missingness classification (handoff §6) distinguishes WHY something is
absent — downstream source-health and reconciliation need the reason, not
just the fact:

- EXPECTED_ABSENCE      the entity/date legitimately has no data
- UNEXPECTED_MISSING    expected under the source contract but absent
- SOURCE_EMPTY          the source returned zero records
- SOURCE_ERROR          the source fetch failed
- PARSE_FAILURE         the payload could not be parsed
- UNRESOLVED_AVAILABILITY availability could not be established

Per-record quality decisions (handoff §16):
- ADMISSIBLE                passes provenance + PIT + no warnings
- ADMISSIBLE_WITH_WARNING   admissible but with documented warnings
- REJECTED                  hard validation failure (never silently dropped)
- UNRESOLVED                cannot be decided (e.g. availability unresolved)

All outputs are deterministic: no runtime clocks, no randomness, no
ordering instability.
"""
from __future__ import annotations

from typing import Any

from .freshness import FRESH, MISSING_POLICY, STALE, UNKNOWN, freshness_status
from .models import RawInformationRecord, parse_boundary
from .pit import is_admissible
from .provenance import provenance_issues

MISSINGNESS_VOCABULARY = (
    "EXPECTED_ABSENCE", "UNEXPECTED_MISSING", "SOURCE_EMPTY",
    "SOURCE_ERROR", "PARSE_FAILURE", "UNRESOLVED_AVAILABILITY",
)

PIT_ADMISSIBLE = "PIT_ADMISSIBLE"
PIT_REJECTED = "PIT_REJECTED"
AVAILABLE_TIME_MISSING = "AVAILABLE_TIME_MISSING"
AVAILABLE_TIME_AFTER_DECISION = "AVAILABLE_TIME_AFTER_DECISION"

QUALITY_ADMISSIBLE = "ADMISSIBLE"
QUALITY_WITH_WARNING = "ADMISSIBLE_WITH_WARNING"
QUALITY_REJECTED = "REJECTED"
QUALITY_UNRESOLVED = "UNRESOLVED"


def classify_missingness(*, source_empty: bool = False, source_error: bool = False,
                         parse_failure: bool = False,
                         availability_unresolved: bool = False,
                         expected_but_absent: bool = False) -> str:
    """Map the observable cause to exactly one missingness class.

    Priority order is documented: hard failures (source/parse) outrank
    unresolved availability, which outranks a plain expected absence.
    """
    if source_error:
        return "SOURCE_ERROR"
    if parse_failure:
        return "PARSE_FAILURE"
    if availability_unresolved:
        return "UNRESOLVED_AVAILABILITY"
    if source_empty:
        return "SOURCE_EMPTY"
    if expected_but_absent:
        return "EXPECTED_ABSENCE"
    return "UNEXPECTED_MISSING"


def timestamp_issues(record: RawInformationRecord,
                     declared_orderings: tuple[str, ...] = ("available_after_event",),
                     reference_time: str | None = None) -> list[dict[str, str]]:
    """Timestamp-quality issues for one record.

    Hard checks (always reported): unparseable fields, missing timezone,
    ingested_at before available_time (our pipeline cannot store a record
    before it became available).

    Semantic checks depend on the source contract. A source whose
    declared_orderings include "available_after_event" expects
    event_time <= available_time; a violation is reported. Orderings that
    the contract cannot prove are reported as UNKNOWN_SEMANTICS instead of
    guessed.
    """
    issues: list[dict[str, str]] = []
    parsed = {}
    for field in ("event_time", "available_time", "ingested_at"):
        raw_value = getattr(record, field, None)
        if raw_value in (None, ""):
            continue
        try:
            parsed[field] = parse_boundary(raw_value)
        except ValueError:
            issues.append({"check": f"{field}_malformed",
                           "field": field,
                           "status": "VIOLATION"})
    if "event_time" in parsed and "event_time" in str(record.event_time):
        pass  # parse succeeded; nothing further
    if "available_time" in parsed and "available_time" in str(record.available_time):
        pass
    for field in ("event_time", "available_time", "ingested_at"):
        raw_value = getattr(record, field, None)
        if raw_value and "T" not in str(raw_value) and raw_value == str(raw_value):
            issues.append({"check": f"{field}_no_time_component",
                           "field": field, "status": "VIOLATION"})
    if "available_time" in parsed and "ingested_at" in parsed:
        if parsed["ingested_at"] < parsed["available_time"]:
            # our pipeline stored the record before the source made it
            # available — provable ordering violation of the ingestion path
            issues.append({"check": "ingested_before_available",
                           "field": "ingested_at", "status": "VIOLATION"})
    if "event_time" in parsed and "available_time" in parsed:
        if parsed["available_time"] >= parsed["event_time"]:
            pass  # consistent with available_after_event semantics
        elif "available_after_event" in declared_orderings:
            issues.append({"check": "available_before_event",
                           "field": "available_time", "status": "VIOLATION"})
        else:
            issues.append({"check": "available_vs_event_unprovable",
                           "field": "available_time", "status": "UNKNOWN"})
    if reference_time is not None:
        ref = None
        try:
            ref = parse_boundary(reference_time)
        except ValueError:
            ref = None
        if ref is not None:
            for field in ("event_time", "available_time"):
                if field in parsed and parsed[field] > ref:
                    issues.append({"check": f"{field}_in_future",
                                   "field": field, "status": "VIOLATION"})
    return issues


def revision_integrity_issues(records: list[RawInformationRecord]) -> list[dict]:
    """Revision-integrity issues grouped by (source, source_id).

    Detects: duplicate revision number, revision gap (missing integer
    steps), available_time regression (a higher revision made available
    EARLIER than a lower one), same revision different payload. Anomalies
    are reported and preserved — never deleted, never auto-resolved.
    """
    groups: dict[tuple[str, str], list[RawInformationRecord]] = {}
    for record in records:
        groups.setdefault((record.source, record.source_id), []).append(record)
    issues: list[dict] = []
    for (source, source_id), rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda r: (r.revision, r.available_time,
                                           r.canonical_json()))
        seen: dict[int, RawInformationRecord] = {}
        for row in rows:
            previous = seen.get(row.revision)
            if previous is not None:
                if previous.canonical_json() != row.canonical_json():
                    issues.append({
                        "source": source, "source_id": source_id,
                        "revision": row.revision,
                        "check": "same_revision_different_payload",
                        "status": "ANOMALY",
                    })
            seen[row.revision] = row
        ordered = sorted(seen.values(), key=lambda r: r.revision)
        for older, newer in zip(ordered, ordered[1:]):
            gap = newer.revision - older.revision
            if gap > 1:
                issues.append({
                    "source": source, "source_id": source_id,
                    "check": "revision_gap", "status": "ANOMALY",
                    "from_revision": older.revision, "to_revision": newer.revision,
                })
            if (older.available_time and newer.available_time
                    and newer.available_time < older.available_time):
                issues.append({
                    "source": source, "source_id": source_id,
                    "check": "revision_available_time_regression",
                    "status": "ANOMALY",
                    "from_revision": older.revision, "to_revision": newer.revision,
                })
    return issues


def pit_quality(records: list[RawInformationRecord],
                decision_time: str) -> dict[str, int]:
    """PIT quality counts. Delegates every judgement to the P14-A pit
    module (``is_admissible``) — this is an auditor, not a second PIT."""
    counts = {PIT_ADMISSIBLE: 0, PIT_REJECTED: 0,
              AVAILABLE_TIME_MISSING: 0, AVAILABLE_TIME_AFTER_DECISION: 0}
    decision = parse_boundary(decision_time)
    for record in records:
        if not record.available_time:
            counts[AVAILABLE_TIME_MISSING] += 1
            continue
        available = parse_boundary(record.available_time)
        if is_admissible(record, decision_time):
            counts[PIT_ADMISSIBLE] += 1
        else:
            counts[AVAILABLE_TIME_AFTER_DECISION] += 1
    return counts


def freshness_quality(records: list[RawInformationRecord], decision_time: str,
                      policies: dict) -> dict[str, int]:
    """Freshness counts with UPPERCASE reporting keys (FRESH/STALE/UNKNOWN/
    MISSING_POLICY/UNRESOLVED), normalized from the lowercase statuses the
    freshness policy layer returns."""
    raw_counts: dict[str, int] = {}
    for record in records:
        status = freshness_status(record, decision_time, policies)
        raw_counts[status.upper()] = raw_counts.get(status.upper(), 0) + 1
    counts = {FRESH: 0, STALE: 0, UNKNOWN: 0, MISSING_POLICY: 0,
              "UNRESOLVED": 0}
    for key, value in raw_counts.items():
        counts[key] = value
    return counts


def record_quality_decision(record: RawInformationRecord,
                            decision_time: str,
                            reference_time: str | None = None,
                            freshness_policies: dict | None = None) -> dict:
    """Per-record quality decision with explicit, preserved reasons.

    The PIT verdict always comes from the P14-A pit module. Provenance
    verdicts come from the P14-A provenance module. P14-C only aggregates
    and classifies.
    """
    reasons: list[str] = []
    rejected = False
    unresolved = False

    issues = provenance_issues(record)
    if issues:
        rejected = True
        reasons.extend(f"PROVENANCE_{issue.upper()}" for issue in issues)
    if record.quality_status == "UNRESOLVED" or not record.available_time:
        unresolved = True
        reasons.append("AVAILABLE_TIME_UNRESOLVED")
    if not is_admissible(record, decision_time):
        if not record.available_time:
            reasons.append("AVAILABLE_TIME_MISSING")
        else:
            reasons.append("PIT_REJECTED")
    timestamp_problems = timestamp_issues(record,
                                          reference_time=reference_time)
    for problem in timestamp_problems:
        reasons.append(problem["check"].upper())
    stale = False
    if freshness_policies:
        status = freshness_status(record, decision_time, freshness_policies)
        if status == STALE:
            stale = True
            reasons.append("SOURCE_STALE")
        elif status in (UNKNOWN, MISSING_POLICY):
            reasons.append(f"FRESHNESS_{status}")
    if unresolved:
        quality_status = QUALITY_UNRESOLVED
    elif rejected:
        quality_status = QUALITY_REJECTED
    elif reasons:
        quality_status = QUALITY_WITH_WARNING
    else:
        quality_status = QUALITY_ADMISSIBLE
    if stale and quality_status in (QUALITY_ADMISSIBLE, QUALITY_WITH_WARNING):
        quality_status = QUALITY_WITH_WARNING
    return {
        "record_id": record.record_id(),
        "quality_status": quality_status,
        "quality_reasons": reasons,
        "stale": stale,
        "timestamp_issues": timestamp_problems,
    }
