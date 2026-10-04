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


# ---------------------------------------------------------------------------
# Selection/rejection chain labels (frozen vocabulary, P14E-P-007).
# Defined HERE — next to the selection rule they name — so the version
# selection authority resolves its own decision labels. P14-D emits them
# in the resolved result; P14-E consumes them verbatim and never
# re-derives any comparison (P14-E Production Implementation REPAIR-002).
# ---------------------------------------------------------------------------

SELECTED_HIGHEST_REVISION = "SELECTED_HIGHEST_REVISION"
SELECTED_EARLIEST_ON_REVISION_TIE = "SELECTED_EARLIEST_ON_REVISION_TIE"
SELECTED_CANONICAL_TIEBREAK = "SELECTED_CANONICAL_TIEBREAK"
REJECTED_LOWER_REVISION = "REJECTED_LOWER_REVISION"
REJECTED_REVISION_TIE_NOT_EARLIEST = "REJECTED_REVISION_TIE_NOT_EARLIEST"
REJECTED_CANONICAL_TIEBREAK = "REJECTED_CANONICAL_TIEBREAK"


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


def _selection_identity(record: RawInformationRecord) -> tuple:
    return (record.source, record.source_id, record.revision,
            record.available_time, record.canonical_json())


def resolve_selection(
    records: Sequence[RawInformationRecord],
    winners: dict[tuple[str, str], RawInformationRecord],
) -> tuple[list, list]:
    """Classify an already-resolved selection over the records it was
    computed from.

    ``winners`` is the mapping returned by :func:`visible_revisions` for
    the same ``records``. Returns ``(selected, rejected)`` — each a list
    of ``(record, label)`` pairs: the winner of every lineage with its
    selection label, and every visible non-selected record with its
    rejection label. The labels restate the exact comparisons
    :func:`visible_revisions` applies, so the rule and its vocabulary
    live in one place; callers project and emit them verbatim. Records
    identical to their lineage winner (same canonical content) ARE the
    winner and produce no rejection entry.
    """
    lineages: dict[tuple[str, str], list] = {}
    for record in records:
        lineages.setdefault((record.source, record.source_id), []).append(
            record)

    selected: list[tuple[RawInformationRecord, str]] = []
    rejected: list[tuple[RawInformationRecord, str]] = []
    for key in sorted(winners):
        winner = winners[key]
        w_id = _selection_identity(winner)
        others = [c for c in lineages.get(key, [])
                  if _selection_identity(c) != w_id]
        same_rev = [c for c in others if c.revision == winner.revision]
        if not others or all(c.revision < winner.revision for c in others):
            label = SELECTED_HIGHEST_REVISION
        elif same_rev and all(c.available_time > winner.available_time
                              for c in same_rev):
            label = SELECTED_EARLIEST_ON_REVISION_TIE
        else:
            label = SELECTED_CANONICAL_TIEBREAK
        selected.append((winner, label))
        for cand in others:
            if cand.revision < winner.revision:
                r_label = REJECTED_LOWER_REVISION
            elif cand.available_time > winner.available_time:
                r_label = REJECTED_REVISION_TIE_NOT_EARLIEST
            else:
                r_label = REJECTED_CANONICAL_TIEBREAK
            rejected.append((cand, r_label))
    return selected, rejected
