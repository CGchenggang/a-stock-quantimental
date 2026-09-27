"""Point-in-time safe industry membership primitives.

Industry membership is modeled as an effective-dated interval. A membership
record becomes usable only at available_time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


@dataclass(frozen=True)
class IndustryMembership:
    symbol: str
    industry_code: str
    industry_name: str
    level: str
    effective_from: datetime
    effective_to: Optional[datetime]
    available_time: datetime
    source: str
    source_type: str
    raw_ref: str = ""
    quality: str = "OK"

    def validate(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if not self.industry_code:
            raise ValueError("industry_code is required")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        if self.available_time < self.effective_from:
            raise ValueError("available_time cannot precede effective_from")
        if not self.source:
            raise ValueError("source is required")
        if not self.source_type:
            raise ValueError("source_type is required")


def admissible_industry(
    memberships: Iterable[IndustryMembership],
    symbol: str,
    event_time: datetime,
    decision_time: datetime,
) -> Optional[IndustryMembership]:
    """Return the unique PIT-admissible industry at a decision boundary.

    Effective interval is [effective_from, effective_to). A record must both
    cover event_time and have been available by decision_time.
    """
    candidates = [
        m for m in memberships
        if m.symbol == symbol
        and m.effective_from <= event_time
        and (m.effective_to is None or event_time < m.effective_to)
        and m.available_time <= decision_time
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda m: (m.effective_from, m.available_time), reverse=True)
    winner = candidates[0]
    same_effective = [m for m in candidates if m.effective_from == winner.effective_from]
    if len({m.industry_code for m in same_effective}) > 1:
        raise ValueError(
            f"ambiguous industry membership for {symbol} at {event_time.isoformat()}"
        )
    return winner


def validate_membership_history(memberships: Iterable[IndustryMembership]) -> None:
    """Reject malformed or overlapping classification intervals."""
    grouped: dict[str, list[IndustryMembership]] = {}
    for membership in memberships:
        membership.validate()
        grouped.setdefault(membership.symbol, []).append(membership)

    for symbol, rows in grouped.items():
        rows.sort(key=lambda x: (x.effective_from, x.effective_to or datetime.max.replace(tzinfo=x.effective_from.tzinfo)))
        for left, right in zip(rows, rows[1:]):
            if left.effective_to is None or right.effective_from < left.effective_to:
                raise ValueError(
                    f"overlapping industry intervals for {symbol}: "
                    f"{left.industry_code} -> {right.industry_code}"
                )
