"""PIT-safe adapters from the local historical store to provider contracts.

The loader is intentionally strict: rows are filtered by available_time before
they reach factor calculations, and when revisions exist only the latest
revision admissible at the decision time is retained for each event_time.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .catalog import HistoricalRecord
from .local_store import LocalHistoricalStore
from .providers import ProviderResult


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _in_window(record: HistoricalRecord, start: str | None, end: str | None) -> bool:
    event = _parse_aware(record.event_time)
    if start is not None and event < _parse_aware(start):
        return False
    if end is not None and event > _parse_aware(end):
        return False
    return True


def _latest_admissible(
    records: tuple[HistoricalRecord, ...],
    *,
    decision_time: str,
    start: str | None,
    end: str | None,
) -> list[HistoricalRecord]:
    _parse_aware(decision_time)
    selected: dict[str, HistoricalRecord] = {}
    for record in records:
        if not record.admissible_at(decision_time):
            continue
        if not _in_window(record, start, end):
            continue
        current = selected.get(record.event_time)
        if current is None or record.revision > current.revision:
            selected[record.event_time] = record
    return sorted(selected.values(), key=lambda item: item.event_time)


def load_daily_provider_result(
    store: LocalHistoricalStore,
    symbol: str,
    *,
    decision_time: str,
    start: str | None = None,
    end: str | None = None,
) -> ProviderResult:
    """Load only daily observations admissible at decision_time.

    Returned rows use the normalized factor schema (date/open/close/high/low/
    volume/amount). A future row, missing-availability row, or fallback row is
    never passed downstream.
    """
    records = store.read_records("cn_stock_daily", symbol)
    selected = _latest_admissible(
        records,
        decision_time=decision_time,
        start=start,
        end=end,
    )
    rows: list[dict[str, Any]] = []
    for record in selected:
        row = dict(record.value)
        row["date"] = record.event_time
        row["_available_time"] = record.available_time
        row["_revision"] = record.revision
        row["_raw_ref"] = record.raw_ref
        rows.append(row)

    available_times = [record.available_time for record in selected if record.available_time]
    available_time = max(available_times) if available_times else None
    return ProviderResult(
        data=rows,
        source="local:cn_stock_daily",
        source_type="local_historical",
        fetched_at="",
        available_time=available_time,
        warnings=[] if selected else ["No PIT-admissible local observations in requested window"],
    )
