"""PIT-safe stock-relative-to-index return features for local research.

The features measure a stock's return relative to a reference index over the
same trading dates. The current stock and index observations must both be
admissible at the stock's 16:00+08:00 decision boundary; older observations
are used only as lookback inputs. Missing current-date index data never gets
silently replaced by stale data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .data.catalog import HistoricalRecord
from .data.local_store import LocalHistoricalStore


@dataclass(frozen=True)
class RelativeContextRow:
    stock_symbol: str
    index_symbol: str
    event_time: str
    decision_time: str
    factors: dict[str, float]


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _admissible_by_event(
    records: tuple[HistoricalRecord, ...],
    decision_time: str,
) -> dict[str, HistoricalRecord]:
    selected: dict[str, HistoricalRecord] = {}
    for record in records:
        if not record.admissible_at(decision_time):
            continue
        current = selected.get(record.event_time)
        if current is None or record.revision > current.revision:
            selected[record.event_time] = record
    return selected


def build_stock_relative_context(
    store: LocalHistoricalStore,
    stock_symbol: str,
    index_symbol: str,
    *,
    lookback: int = 20,
) -> tuple[RelativeContextRow, ...]:
    """Build stock-minus-index returns using common trading dates."""
    if lookback < 20:
        raise ValueError("lookback must be at least 20")

    stock_records = store.read_records("cn_stock_daily", stock_symbol)
    index_records = store.read_records("cn_index_daily", index_symbol)
    if not stock_records or not index_records:
        return ()

    stock_by_event: dict[str, list[HistoricalRecord]] = {}
    for record in stock_records:
        stock_by_event.setdefault(record.event_time, []).append(record)
    index_by_event: dict[str, list[HistoricalRecord]] = {}
    for record in index_records:
        index_by_event.setdefault(record.event_time, []).append(record)

    common_events = sorted(set(stock_by_event) & set(index_by_event))
    rows: list[RelativeContextRow] = []

    for pos in range(lookback, len(common_events)):
        event_time = common_events[pos]
        decision_time = f"{event_time[:10]}T16:00:00+08:00"
        _parse_aware(decision_time)

        stock_current = _admissible_by_event(
            tuple(stock_by_event[event_time]), decision_time
        ).get(event_time)
        index_current = _admissible_by_event(
            tuple(index_by_event[event_time]), decision_time
        ).get(event_time)

        # Both current observations are required. Never substitute a stale
        # index observation for the current decision date.
        if stock_current is None or index_current is None:
            continue

        common_admitted: list[tuple[HistoricalRecord, HistoricalRecord]] = []
        for prior_event in common_events[: pos + 1]:
            stock_selected = _admissible_by_event(
                tuple(stock_by_event[prior_event]), decision_time
            ).get(prior_event)
            index_selected = _admissible_by_event(
                tuple(index_by_event[prior_event]), decision_time
            ).get(prior_event)
            if stock_selected is not None and index_selected is not None:
                common_admitted.append((stock_selected, index_selected))

        if len(common_admitted) < lookback + 1:
            continue

        stock_closes = [
            float(stock.value["close"]) for stock, _ in common_admitted[-(lookback + 1):]
        ]
        index_closes = [
            float(index.value["close"]) for _, index in common_admitted[-(lookback + 1):]
        ]
        if any(value <= 0 for value in stock_closes + index_closes):
            continue

        stock_return_5 = stock_closes[-1] / stock_closes[-6] - 1.0
        index_return_5 = index_closes[-1] / index_closes[-6] - 1.0
        stock_return_20 = stock_closes[-1] / stock_closes[-21] - 1.0
        index_return_20 = index_closes[-1] / index_closes[-21] - 1.0

        rows.append(
            RelativeContextRow(
                stock_symbol=stock_symbol,
                index_symbol=index_symbol,
                event_time=event_time,
                decision_time=decision_time,
                factors={
                    f"relative_{index_symbol}_return_5": stock_return_5 - index_return_5,
                    f"relative_{index_symbol}_return_20": stock_return_20 - index_return_20,
                },
            )
        )

    return tuple(rows)


def build_stock_relative_context_map(
    store: LocalHistoricalStore,
    stock_symbol: str,
    index_symbols: tuple[str, ...],
    *,
    lookback: int = 20,
) -> dict[str, dict[str, float]]:
    """Return decision-time -> combined relative-return factors."""
    combined: dict[str, dict[str, float]] = {}
    for index_symbol in index_symbols:
        for row in build_stock_relative_context(
            store, stock_symbol, index_symbol, lookback=lookback
        ):
            combined.setdefault(row.decision_time, {}).update(row.factors)
    return combined
