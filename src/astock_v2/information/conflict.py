"""Cross-source conflict semantics for the information layer.

Two different sources reporting the same fact (same entity, same
event_time, same unit) with different values is a CONFLICT. P14-A does not
resolve conflicts — no highest / latest / average — every variant is kept
with full provenance and the group is annotated
``conflict_status = "CONFLICT"`` for downstream researchers. Resolving a
conflict requires an explicit, frozen source-precedence policy, which does
not exist yet.

Revisions from the SAME source are corrections, not conflicts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import RawInformationRecord

CONFLICT = "CONFLICT"
NO_CONFLICT = None


def conflict_group_key(record: RawInformationRecord) -> tuple:
    return (record.entity_id, record.entity_type, record.event_time,
            record.unit, record.currency)


def detect_conflicts(
    records: Iterable[RawInformationRecord],
) -> dict[tuple, dict[str, list[str]]]:
    """Groups carrying >=2 distinct non-None values from different sources.

    Returns {group_key: {source: [record_id, ...]}} for conflict groups
    only; record_id is the canonical record id for provenance.
    """
    groups: dict[tuple, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    ids: dict[tuple, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record.value is None:
            continue
        key = conflict_group_key(record)
        groups[key][record.source].add(record.value)
        ids[key][record.source].append(record.record_id())
    conflicts = {}
    for key, by_source in sorted(groups.items()):
        distinct = {v for values in by_source.values() for v in values}
        if len(by_source) >= 2 and len(distinct) >= 2:
            conflicts[key] = {
                source: sorted(ids[key][source]) for source in sorted(by_source)
            }
    return conflicts


def annotate_conflict_status(
    records: Iterable[RawInformationRecord],
) -> list[tuple[RawInformationRecord, str | None]]:
    """Attach CONFLICT / None per record; order and values are unchanged."""
    records = list(records)
    conflicts = detect_conflicts(records)
    annotated = []
    for record in records:
        key = conflict_group_key(record)
        annotated.append((record, CONFLICT if key in conflicts else NO_CONFLICT))
    return annotated
