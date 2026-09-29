"""Build a PIT-safe factor/label dataset from local A-share daily history."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from .data.catalog import HistoricalRecord
from .data.local_store import LocalHistoricalStore
from .data.providers import ProviderResult
from .factors import compute_factor


@dataclass(frozen=True)
class LocalFactorRow:
    symbol: str
    decision_time: str
    factors: Mapping[str, float]
    label: int
    next_return: float
    source_event_time: str


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _prepare_pit_updates(
    ordered: list[HistoricalRecord],
    event_index: dict[str, int],
) -> list[tuple[datetime, int, int, HistoricalRecord]]:
    """Flatten records into one availability-ordered admission schedule.

    Each entry is (available_dt, revision, event_index, record) sorted by
    availability so a single incremental pointer can admit everything known at
    a decision boundary; the revision key stabilises same-instant ties.
    Records that can never become PIT-admissible (unparseable or backwards
    availability) are excluded exactly as admissible_at() would reject them,
    but parsed once here instead of once per decision day.
    """
    updates: list[tuple[datetime, int, int, HistoricalRecord]] = []
    for record in ordered:
        if not record.available_time:
            continue
        try:
            available_dt = datetime.fromisoformat(
                record.available_time.replace("Z", "+00:00")
            )
            event_dt = datetime.fromisoformat(
                record.event_time.replace("Z", "+00:00")
            )
        except ValueError:
            continue
        if available_dt.tzinfo is None or event_dt.tzinfo is None:
            continue
        if available_dt < event_dt:
            continue
        updates.append(
            (available_dt, record.revision, event_index[record.event_time], record)
        )
    updates.sort(key=lambda item: (item[0], item[1]))
    return updates


def build_local_factor_rows(
    store: LocalHistoricalStore,
    symbol: str,
    *,
    factor_names: tuple[str, ...] = ("momentum", "volatility", "trend", "volume_ratio"),
    lookback: int = 20,
) -> tuple[LocalFactorRow, ...]:
    """Build one observation per completed trading day.

    Factors at day t use only revisions that were available by t's decision
    time. The label is the next trading day's close return and is therefore
    outside the factor input window.
    """
    if lookback <= 0:
        raise ValueError("lookback must be positive")

    records = store.read_records("cn_stock_daily", symbol)
    if len(records) < lookback + 2:
        return ()

    ordered = sorted(records, key=lambda r: (r.event_time, r.revision))
    event_times = sorted({record.event_time for record in ordered})
    event_index = {event_time: index for index, event_time in enumerate(event_times)}
    by_event: dict[str, list[HistoricalRecord]] = defaultdict(list)
    for record in ordered:
        by_event[record.event_time].append(record)
    updates = _prepare_pit_updates(ordered, event_index)

    rows: list[LocalFactorRow] = []
    update_pointer = 0
    admitted_by_event: list[HistoricalRecord | None] = [None] * len(event_times)
    for index in range(lookback, len(event_times) - 1):
        event_time = event_times[index]
        # Daily A-share research uses a fixed post-close decision boundary.
        # This is the same explicit 16:00 Asia/Shanghai availability
        # convention used by the downloader, not a fetch-time assumption.
        decision_time = f"{event_time[:10]}T16:00:00+08:00"
        decision_dt = _parse_aware(decision_time)
        while update_pointer < len(updates) and updates[update_pointer][0] <= decision_dt:
            _, revision, event_idx, record = updates[update_pointer]
            current = admitted_by_event[event_idx]
            if current is None or revision > current.revision:
                admitted_by_event[event_idx] = record
            update_pointer += 1

        current = admitted_by_event[index]
        if current is None:
            continue
        active = admitted_by_event[: index + 1]
        if None in active:
            admitted = [record for record in active if record is not None]
        else:
            admitted = active
        if len(admitted) < lookback + 1:
            continue

        provider = ProviderResult(
            data=[record.value for record in admitted],
            source="local:cn_stock_daily",
            source_type="local_historical",
            fetched_at="",
            available_time=decision_time,
        )

        factors: dict[str, float] = {}
        for name in factor_names:
            output = compute_factor(
                name,
                provider,
                symbol=symbol,
                decision_time=decision_time,
                lookback=lookback,
            )
            if not output.admissible or output.value is None:
                break
            factors[name] = float(output.value)

        if len(factors) != len(factor_names):
            continue

        today_close = float(current.value["close"])
        next_record = max(
            by_event[event_times[index + 1]],
            key=lambda record: record.revision,
        )
        next_close = float(next_record.value["close"])
        if today_close <= 0:
            continue

        next_return = next_close / today_close - 1.0
        rows.append(
            LocalFactorRow(
                symbol=symbol,
                decision_time=decision_time,
                factors=factors,
                label=int(next_return > 0),
                next_return=next_return,
                source_event_time=current.event_time,
            )
        )

    return tuple(rows)
