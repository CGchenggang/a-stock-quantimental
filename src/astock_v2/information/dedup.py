"""Deterministic deduplication for the information layer.

Deduplication key: ``(source, source_id, revision)`` — the same fact from
the same source at the same revision is one information unit regardless of
how many times it was ingested. Different revisions are different records
(a correction timeline, handled by pit.visible_revisions). Different
sources are different provenance (handled by conflict detection).

The survivor is chosen deterministically: smallest canonical JSON text
(identical duplicates make this a no-op). Input order never matters.
"""
from __future__ import annotations

from typing import Iterable

from .models import RawInformationRecord


def dedup_key(record: RawInformationRecord) -> tuple[str, str, int]:
    return (record.source, record.source_id, record.revision)


def deduplicate(records: Iterable[RawInformationRecord]) -> list[RawInformationRecord]:
    best: dict[tuple[str, str, int], RawInformationRecord] = {}
    for record in records:
        key = dedup_key(record)
        current = best.get(key)
        if current is None or record.canonical_json() < current.canonical_json():
            best[key] = record
    return [best[key] for key in sorted(best)]
