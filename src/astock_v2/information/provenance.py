"""Source provenance contract for the information layer.

``source`` answers "where did this information come from?" and
``source_id`` answers "which record/event inside that source?". A record
whose provenance cannot be confirmed must never enter the PIT-safe
research layer: it is marked ``UNRESOLVED`` (or ``INVALID``) and rejected
by :func:`provenance_issues`.
"""
from __future__ import annotations

from typing import Iterable

from .models import (
    QUALITY_INVALID,
    QUALITY_UNRESOLVED,
    RawInformationRecord,
    ResearchInformationRecord,
    hashlib_sha256,
)

RESERVED_PLACEHOLDER_SOURCES = {"", "unknown", "unknown_source", "n/a", "none"}


def provenance_issues(record: RawInformationRecord) -> list[str]:
    issues: list[str] = []
    if str(record.source).strip().lower() in RESERVED_PLACEHOLDER_SOURCES:
        issues.append("source_is_placeholder")
    if not str(record.source_id).strip():
        issues.append("missing_source_id")
    if not str(record.ingested_at or "").strip():
        issues.append("missing_ingested_at")
    if record.quality_status == QUALITY_UNRESOLVED:
        issues.append("provenance_unresolved")
    if record.quality_status == QUALITY_INVALID:
        issues.append("provenance_invalid")
    return issues


def has_valid_provenance(record: RawInformationRecord) -> bool:
    return not provenance_issues(record)


def to_research_record(
    record: RawInformationRecord, conflict_status: str | None = None
) -> ResearchInformationRecord:
    """Admit a provenance-valid record to the research layer.

    Raises when provenance is not confirmable: unknown-origin records are
    rejected, not silently laundered into research inputs.
    """
    issues = provenance_issues(record)
    if issues or record.quality_status != "OK":
        raise ValueError(
            "information record cannot enter the research layer: "
            f"source={record.source!r} source_id={record.source_id!r} issues={issues}"
        )
    raw_id = record.record_id()
    return ResearchInformationRecord(
        record_id=hashlib_sha256(raw_id + f"|conflict={conflict_status}"),
        raw_record_id=raw_id,
        research_only=True,
        conflict_status=conflict_status,
        source=record.source,
        source_id=record.source_id,
        source_category=record.source_category,
        entity_id=record.entity_id,
        entity_type=record.entity_type,
        event_time=record.event_time,
        available_time=record.available_time,
        revision=record.revision,
        ingested_at=record.ingested_at,
        symbol=record.symbol,
        content=record.content,
        value=record.value,
        unit=record.unit,
        currency=record.currency,
        language=record.language,
        quality_status=record.quality_status,
        freshness_policy_id=record.freshness_policy_id,
        metadata=dict(record.metadata),
    )


def provenance_summary(records: Iterable[RawInformationRecord]) -> dict:
    rows = list(records)
    rejected = [r for r in rows if not has_valid_provenance(r)]
    return {
        "n": len(rows),
        "n_rejected": len(rejected),
        "rejected_ids": [r.record_id() for r in rejected],
        "sources": sorted({r.source for r in rows}),
    }
