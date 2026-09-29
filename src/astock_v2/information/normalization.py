"""Deterministic normalization: raw records -> research information records.

Pipeline (every step deterministic, no runtime timestamps, no random
ordering):

    provenance validation
        -> deduplication by (source, source_id, revision)
        -> cross-source conflict annotation (CONFLICT kept, not resolved)
        -> sort by (available_time, source, source_id, revision, record text)
        -> research records with record_id = sha256(raw_id | conflict)

Unregistered sources, placeholder provenance and non-OK quality records
are rejected with an explicit error; they never silently reach the
research layer.
"""
from __future__ import annotations

from typing import Iterable

from .conflict import annotate_conflict_status
from .dedup import deduplicate
from .models import RawInformationRecord, ResearchInformationRecord
from .provenance import provenance_issues, to_research_record
from .registry import is_registered


def normalize(
    records: Iterable[RawInformationRecord],
) -> list[ResearchInformationRecord]:
    raw = list(records)
    rejected = []
    for record in raw:
        if not is_registered(record.source):
            rejected.append(f"unregistered_source:{record.source!r}")
        elif provenance_issues(record):
            rejected.append(
                f"provenance_issues:{record.source_id} "
                f"{provenance_issues(record)}"
            )
    if rejected:
        raise ValueError(
            "information records rejected by normalization: " + "; ".join(rejected)
        )
    deduped = deduplicate(raw)
    annotated = annotate_conflict_status(deduped)
    research = [to_research_record(record, status) for record, status in annotated]
    research.sort(
        key=lambda r: (
            r.available_time, r.source, r.source_id, r.revision, r.record_id
        )
    )
    return research
