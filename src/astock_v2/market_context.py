"""PIT-safe local CN index market-state features for stock research.

The module derives only same-day-or-earlier index information admissible at a
stock decision time. It deliberately returns raw state variables rather than
regime labels; regime thresholds are a later research step.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import log, sqrt
from statistics import pstdev

from .data.catalog import HistoricalRecord
from .data.local_store import LocalHistoricalStore


@dataclass(frozen=True)
class MarketContextRow:
    symbol: str
    event_time: str
    decision_time: str
    factors: dict[str, float]


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _latest_admissible(records: tuple[HistoricalRecord, ...], decision_time: str):
    selected: dict[str, HistoricalRecord] = {}
    for record in records:
        if not record.admissible_at(decision_time):
            continue
        current = selected.get(record.event_time)
        if current is None or record.revision > current.revision:
            selected[record.event_time] = record
    return sorted(selected.values(), key=lambda item: item.event_time)


def build_index_market_context(
    store: LocalHistoricalStore,
    symbol: str,
    *,
    lookback: int = 20,
) -> tuple[MarketContextRow, ...]:
    """Build fixed index-state variables from local PIT-safe index history.

    Variables per index:
      return_5: close[t] / close[t-5] - 1
      return_20: close[t] / close[t-20] - 1
      close_vs_sma20: close[t] / mean(close[t-19:t+1]) - 1
      volatility_20: annualized population std of 20 daily log returns
    """
    if lookback < 20:
        raise ValueError("lookback must be at least 20")

    records = store.read_records("cn_index_daily", symbol)
    if not records:
        return ()

    by_event: dict[str, list[HistoricalRecord]] = {}
    for record in records:
        by_event.setdefault(record.event_time, []).append(record)
    event_times = sorted(by_event)
    rows: list[MarketContextRow] = []

    for index in range(lookback, len(event_times)):
        event_time = event_times[index]
        decision_time = f"{event_time[:10]}T16:00:00+08:00"
        _parse_aware(decision_time)
        admitted = []
        for prior_event in event_times[: index + 1]:
            candidates = [
                record for record in by_event[prior_event]
                if record.admissible_at(decision_time)
            ]
            if candidates:
                admitted.append(max(candidates, key=lambda r: r.revision))
        if len(admitted) < 21:
            continue

        closes = [float(record.value["close"]) for record in admitted]
        if any(value <= 0 for value in closes[-21:]):
            continue

        close = closes[-1]
        return_5 = close / closes[-6] - 1.0
        return_20 = close / closes[-21] - 1.0
        sma20 = sum(closes[-20:]) / 20.0
        log_returns = [
            log(closes[j] / closes[j - 1])
            for j in range(len(closes) - 20, len(closes))
        ]
        volatility_20 = pstdev(log_returns) * sqrt(252.0)

        rows.append(
            MarketContextRow(
                symbol=symbol,
                event_time=event_time,
                decision_time=decision_time,
                factors={
                    f"{symbol}_return_5": return_5,
                    f"{symbol}_return_20": return_20,
                    f"{symbol}_close_vs_sma20": close / sma20 - 1.0,
                    f"{symbol}_volatility_20": volatility_20,
                },
            )
        )
    return tuple(rows)


def build_market_context_map(
    store: LocalHistoricalStore,
    symbols: tuple[str, ...],
    *,
    lookback: int = 20,
) -> dict[str, dict[str, float]]:
    """Return decision-date -> combined market-state factors."""
    combined: dict[str, dict[str, float]] = {}
    for symbol in symbols:
        for row in build_index_market_context(store, symbol, lookback=lookback):
            combined.setdefault(row.decision_time, {}).update(row.factors)
    return combined
