"""PIT admissibility for the information layer.

Contract: information is admissible at decision_time iff

    available_time <= decision_time      (inclusive boundary)

event_time is NEVER used for admissibility. Late-arriving information
(event_time < available_time) is admitted on the same terms as any other
record, purely by available_time.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from .models import RawInformationRecord, parse_boundary


def is_admissible(record: RawInformationRecord, decision_time: str) -> bool:
    return parse_boundary(record.available_time) <= parse_boundary(decision_time)


def admissible_records(
    records: Iterable[RawInformationRecord], decision_time: str
) -> list[RawInformationRecord]:
    return [r for r in records if is_admissible(r, decision_time)]


def visible_revisions(
    records: Sequence[RawInformationRecord], decision_time: str
) -> dict[tuple[str, str], RawInformationRecord]:
    """Latest admissible revision per (source, source_id) at decision_time.

    A revision only becomes visible when its own available_time has passed,
    so a later revision can never rewrite history before its availability.
    Ties on revision resolve to the record available EARLIEST (then by the
    smallest canonical text) to stay deterministic — the same revision is
    the same information, so the survivor is the copy that was knowable
    first (P14-D-REPAIR-001: the comparison previously preferred the latest
    available_time, contradicting this documented rule).
    """
    best: dict[tuple[str, str], RawInformationRecord] = {}

    def _wins(candidate: RawInformationRecord, current: RawInformationRecord) -> bool:
        if candidate.revision != current.revision:
            return candidate.revision > current.revision
        if candidate.available_time != current.available_time:
            return candidate.available_time < current.available_time
        return candidate.canonical_json() < current.canonical_json()

    for record in admissible_records(records, decision_time):
        key = (record.source, record.source_id)
        current = best.get(key)
        if current is None or _wins(record, current):
            best[key] = record
    return best
