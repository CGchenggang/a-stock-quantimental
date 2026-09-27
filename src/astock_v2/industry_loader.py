"""Load PIT-safe industry membership CSV exports."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .industry import IndustryMembership, validate_membership_history


_REQUIRED = {
    "symbol",
    "industry_code",
    "industry_name",
    "level",
    "effective_from",
    "effective_to",
    "available_time",
    "source",
    "source_type",
    "raw_ref",
}


def _parse_dt(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    return datetime.fromisoformat(value)


def load_industry_memberships(path: str | Path) -> list[IndustryMembership]:
    """Load and validate CNINFO-derived membership intervals.

    The loader never fills missing historical intervals. A symbol with no
    admissible record before an event remains unavailable to the caller.
    """
    rows: list[IndustryMembership] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = _REQUIRED - fields
        if missing:
            raise ValueError(f"missing industry membership columns: {sorted(missing)}")

        for row in reader:
            membership = IndustryMembership(
                symbol=str(row["symbol"]).strip(),
                industry_code=str(row["industry_code"]).strip(),
                industry_name=str(row["industry_name"]).strip(),
                level=str(row["level"]).strip(),
                effective_from=_parse_dt(row["effective_from"]),
                effective_to=_parse_dt(row["effective_to"]),
                available_time=_parse_dt(row["available_time"]),
                source=str(row["source"]).strip(),
                source_type=str(row["source_type"]).strip(),
                raw_ref=str(row.get("raw_ref", "")).strip(),
                quality=str(row.get("quality", "OK") or "OK").strip(),
            )
            membership.validate()
            rows.append(membership)

    validate_membership_history(rows)
    return rows
