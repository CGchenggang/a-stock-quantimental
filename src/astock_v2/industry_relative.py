"""PIT-safe stock-relative-to-SW1-industry return features for local research.

The industry benchmark is an equal-weight portfolio of locally available stock
daily returns whose SW level-1 membership is admissible at the decision time.
The target stock is excluded from its own benchmark. A missing or singleton
industry therefore produces no factor rather than a fabricated value.

At decision time t, historical membership assignments are evaluated using only
information available by t. Daily member returns are then averaged cross-
sectionally and compounded over the requested lookback horizon.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .data.catalog import HistoricalRecord
from .data.local_store import LocalHistoricalStore
from .industry import admissible_industry
from .industry_loader import load_industry_memberships


@dataclass(frozen=True)
class IndustryRelativeContextRow:
    stock_symbol: str
    industry_code: str
    event_time: str
    decision_time: str
    factors: dict[str, float]


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _admissible_daily(
    records: tuple[HistoricalRecord, ...],
    decision_time: str,
) -> dict[str, HistoricalRecord]:
    selected: dict[str, HistoricalRecord] = {}
    for record in records:
        if not record.admissible_at(decision_time):
            continue
        day = record.event_time[:10]
        current = selected.get(day)
        if current is None or record.revision > current.revision:
            selected[day] = record
    return selected


def _industry_for_day(memberships, symbol: str, day: str, decision_time: str):
    event_time = datetime.fromisoformat(f"{day}T00:00:00+00:00")
    return admissible_industry(
        memberships,
        symbol,
        event_time,
        _parse_aware(decision_time),
    )


def _daily_returns(
    records: tuple[HistoricalRecord, ...],
    decision_time: str,
) -> dict[str, float]:
    """Return close-to-close returns for records admissible at one decision time."""
    selected = _admissible_daily(records, decision_time)
    days = sorted(selected)
    result: dict[str, float] = {}
    for previous_day, day in zip(days, days[1:]):
        previous_close = float(selected[previous_day].value["close"])
        close = float(selected[day].value["close"])
        if previous_close > 0 and close > 0:
            result[day] = close / previous_close - 1.0
    return result


def build_stock_industry_relative_context(
    store: LocalHistoricalStore,
    membership_path: str | Path,
    stock_symbol: str,
    universe_symbols: tuple[str, ...],
    *,
    lookback: int = 20,
) -> tuple[IndustryRelativeContextRow, ...]:
    """Build stock-minus-SW1-industry returns from a local stock universe."""
    if lookback < 20:
        raise ValueError("lookback must be at least 20")

    symbols = tuple(dict.fromkeys(str(s).strip().zfill(6) for s in universe_symbols))
    if stock_symbol not in symbols:
        symbols = (stock_symbol, *symbols)

    memberships = load_industry_memberships(membership_path)
    all_records = {
        symbol: store.read_records("cn_stock_daily", symbol)
        for symbol in symbols
    }
    event_days = sorted(
        {
            record.event_time[:10]
            for records in all_records.values()
            for record in records
        }
    )

    rows: list[IndustryRelativeContextRow] = []
    for pos in range(lookback, len(event_days)):
        day = event_days[pos]
        decision_time = f"{day}T16:00:00+08:00"
        _parse_aware(decision_time)

        target_daily = _admissible_daily(all_records[stock_symbol], decision_time)
        target_current = target_daily.get(day)
        if target_current is None:
            continue

        target_membership = _industry_for_day(
            memberships, stock_symbol, day, decision_time
        )
        if target_membership is None:
            continue

        target_returns = _daily_returns(
            all_records[stock_symbol], decision_time
        )

        # The industry benchmark is reconstructed from member-level daily
        # returns. Membership is evaluated at today's decision boundary, so no
        # classification information unavailable at t can enter the factor.
        industry_returns_by_day: dict[str, list[float]] = {}
        for symbol in symbols:
            if symbol == stock_symbol:
                continue
            symbol_records = all_records[symbol]
            symbol_returns = _daily_returns(symbol_records, decision_time)
            symbol_daily = _admissible_daily(symbol_records, decision_time)
            for return_day, stock_return in symbol_returns.items():
                membership = _industry_for_day(
                    memberships, symbol, return_day, decision_time
                )
                if membership is None:
                    continue
                if membership.industry_code != target_membership.industry_code:
                    continue
                industry_returns_by_day.setdefault(return_day, []).append(stock_return)

        common_days = [
            d for d in sorted(target_returns)
            if d in industry_returns_by_day and industry_returns_by_day[d]
        ]
        if len(common_days) < lookback:
            continue

        recent_days = common_days[-lookback:]
        target_recent = [target_returns[d] for d in recent_days]
        industry_recent = [
            sum(industry_returns_by_day[d]) / len(industry_returns_by_day[d])
            for d in recent_days
        ]

        def compounded(values: list[float]) -> float:
            result = 1.0
            for value in values:
                result *= 1.0 + value
            return result - 1.0

        target_return_20 = compounded(target_recent)
        industry_return_20 = compounded(industry_recent)
        target_return_5 = compounded(target_recent[-5:])
        industry_return_5 = compounded(industry_recent[-5:])

        rows.append(
            IndustryRelativeContextRow(
                stock_symbol=stock_symbol,
                industry_code=target_membership.industry_code,
                event_time=target_current.event_time,
                decision_time=decision_time,
                factors={
                    "industry_relative_return_5": target_return_5 - industry_return_5,
                    "industry_relative_return_20": target_return_20 - industry_return_20,
                },
            )
        )

    return tuple(rows)


def build_stock_industry_relative_context_map(
    store: LocalHistoricalStore,
    membership_path: str | Path,
    stock_symbol: str,
    universe_symbols: tuple[str, ...],
    *,
    lookback: int = 20,
) -> dict[str, dict[str, float]]:
    """Return decision-time -> industry-relative factor map."""
    return {
        row.decision_time: row.factors
        for row in build_stock_industry_relative_context(
            store,
            membership_path,
            stock_symbol,
            universe_symbols,
            lookback=lookback,
        )
    }
