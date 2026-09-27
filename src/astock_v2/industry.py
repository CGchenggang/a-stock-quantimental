"""Point-in-time safe industry membership primitives and CSV loader.

Industry membership is modeled as an effective-dated interval. A membership
record becomes usable only at available_time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


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
        m
        for m in memberships
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
        rows.sort(
            key=lambda x: (
                x.effective_from,
                x.effective_to or datetime.max.replace(tzinfo=x.effective_from.tzinfo),
            )
        )
        for left, right in zip(rows, rows[1:]):
            if left.effective_to is None or right.effective_from < left.effective_to:
                raise ValueError(
                    f"overlapping industry intervals for {symbol}: "
                    f"{left.industry_code} -> {right.industry_code}"
                )


_REQUIRED_CSV_COLUMNS = {
    "symbol",
    "industry_code",
    "industry_name",
    "level",
    "effective_from",
    "effective_to",
    "available_time",
    "source",
    "source_type",
}


def _as_datetime(value: object) -> datetime:
    parsed = pd.to_datetime(value, utc=True, errors="raise")
    return parsed.to_pydatetime()


def load_industry_membership_csv(
    path: str | Path,
    *,
    validate: bool = True,
) -> list[IndustryMembership]:
    """Load a normalized P13-M membership CSV.

    Empty effective_to values become None. Timestamps are normalized to
    timezone-aware UTC datetimes. No membership is inferred before the first
    explicitly observed effective_from.
    """
    df = pd.read_csv(path)
    missing = sorted(_REQUIRED_CSV_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"industry membership CSV missing columns: {missing}")

    rows: list[IndustryMembership] = []
    for record in df.to_dict("records"):
        effective_to = record["effective_to"]
        effective_to_dt = (
            None
            if pd.isna(effective_to) or str(effective_to).strip() == ""
            else _as_datetime(effective_to)
        )
        rows.append(
            IndustryMembership(
                symbol=str(record["symbol"]).strip(),
                industry_code=str(record["industry_code"]).strip(),
                industry_name=str(record["industry_name"]).strip(),
                level=str(record["level"]).strip(),
                effective_from=_as_datetime(record["effective_from"]),
                effective_to=effective_to_dt,
                available_time=_as_datetime(record["available_time"]),
                source=str(record["source"]).strip(),
                source_type=str(record["source_type"]).strip(),
                raw_ref=str(record.get("raw_ref", "") or "").strip(),
                quality=str(record.get("quality", "OK") or "OK").strip(),
            )
        )

    if validate:
        validate_membership_history(rows)
    return rows


def coverage_start(
    memberships: Iterable[IndustryMembership],
) -> dict[str, datetime]:
    """Return the earliest explicitly observed effective date per symbol."""
    result: dict[str, datetime] = {}
    for membership in memberships:
        current = result.get(membership.symbol)
        if current is None or membership.effective_from < current:
            result[membership.symbol] = membership.effective_from
    return result
