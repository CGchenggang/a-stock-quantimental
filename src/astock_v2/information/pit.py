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
    Ties on revision resolve to the record available earliest (then by
    canonical text) to stay deterministic.
    """
    best: dict[tuple[str, str], RawInformationRecord] = {}
    for record in admissible_records(records, decision_time):
        key = (record.source, record.source_id)
        current = best.get(key)
        if current is None or (record.revision, record.available_time, record.canonical_json()) > (
            current.revision, current.available_time, current.canonical_json()
        ):
            best[key] = record
    return best
