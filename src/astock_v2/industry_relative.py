"""PIT-safe stock-relative-to-SW1-industry return features for local research.

The industry benchmark is an equal-weight portfolio of locally available stock
daily returns whose SW level-1 membership is admissible at the decision time.
The target stock is excluded from its own benchmark. A missing or singleton
industry therefore produces no factor rather than a fabricated value.

The implementation keeps the original PIT semantics but avoids rebuilding every
stock's full return history for every decision day. Daily closes are advanced
incrementally as records become admissible; membership lookups use sorted
effective/availability schedules and binary search.
"""
from __future__ import annotations

from bisect import bisect_right
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


def _membership_schedule(memberships):
    """Prepare one stock's membership schedule for fast PIT lookups."""
    ordered = sorted(memberships, key=lambda item: item.effective_from)
    effective = [item.effective_from for item in ordered]
    available = sorted(item.available_time for item in ordered)
    return ordered, effective, available


def _scheduled_industry(schedule, day: str, decision_time: str):
    """Resolve the latest effective assignment known at decision_time.

    The importer uses monotone availability (effective date + one day), so
    admissible assignments form a prefix of the effective-date schedule.
    Binary search keeps the hot peer loop logarithmic in membership history.
    """
    ordered, effective, available = schedule
    if not ordered:
        return None
    available_end = bisect_right(available, decision_time)
    if available_end == 0:
        return None
    effective_end = bisect_right(effective, f"{day}T00:00:00+08:00")
    index = min(available_end, effective_end) - 1
    if index < 0:
        return None
    return ordered[index]


def _build_pit_return_state(
    records_by_symbol: dict[str, tuple[HistoricalRecord, ...]],
):
    """Create mutable PIT state advanced by decision time.

    Each stock keeps its latest admissible close per trading day and only the
    affected adjacent returns are recomputed when a revision becomes known.
    """
    state = {}
    for symbol, records in records_by_symbol.items():
        days = sorted({record.event_time[:10] for record in records})
        index = {day: pos for pos, day in enumerate(days)}
        ordered = sorted(
            (record for record in records if record.pit_ready),
            key=lambda record: (record.available_time or "", record.revision),
        )
        state[symbol] = {
            "days": days,
            "index": index,
            "records": ordered,
            "cursor": 0,
            "selected": {},
            "returns": {},
        }
    return state


def _advance_pit_return_state(state, decision_time: str) -> None:
    """Advance all stocks to one monotonically increasing decision boundary."""
    for item in state.values():
        selected = item["selected"]
        returns = item["returns"]
        days = item["days"]
        index = item["index"]
        records = item["records"]

        while item["cursor"] < len(records):
            record = records[item["cursor"]]
            if record.available_time is None or record.available_time > decision_time:
                break
            item["cursor"] += 1

            day = record.event_time[:10]
            current = selected.get(day)
            if current is not None and current.revision >= record.revision:
                continue
            selected[day] = record

            pos = index[day]
            for neighbor_pos, return_day in (
                (pos, day),
                (pos + 1, days[pos + 1] if pos + 1 < len(days) else None),
            ):
                if return_day is None or neighbor_pos == 0:
                    continue
                previous_day = days[neighbor_pos - 1]
                previous = selected.get(previous_day)
                current_record = selected.get(return_day)
                if previous is None or current_record is None:
                    returns.pop(return_day, None)
                    continue
                previous_close = float(previous.value["close"])
                close = float(current_record.value["close"])
                if previous_close > 0 and close > 0:
                    returns[return_day] = close / previous_close - 1.0
                else:
                    returns.pop(return_day, None)


def _compounded(values) -> float:
    result = 1.0
    for value in values:
        result *= 1.0 + value
    return result - 1.0


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
    memberships_by_symbol = {}
    for symbol in symbols:
        memberships_by_symbol[symbol] = _membership_schedule(
            [m for m in memberships if m.symbol == symbol]
        )

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
    state = _build_pit_return_state(all_records)

    rows: list[IndustryRelativeContextRow] = []
    for pos in range(lookback, len(event_days)):
        day = event_days[pos]
        decision_time = f"{day}T16:00:00+08:00"
        _parse_aware(decision_time)
        _advance_pit_return_state(state, decision_time)

        target_current = state[stock_symbol]["selected"].get(day)
        if target_current is None:
            continue

        target_membership = _scheduled_industry(
            memberships_by_symbol[stock_symbol], day, decision_time
        )
        if target_membership is None:
            continue

        target_returns = state[stock_symbol]["returns"]

        # Only the most recent target return days can enter a lookback factor.
        # Scan backward until enough common peer days have been found. This
        # avoids constructing a full historical peer benchmark for every t.
        common_days = []
        industry_recent_by_day: dict[str, list[float]] = {}
        for return_day in sorted(target_returns, reverse=True):
            peer_values: list[float] = []
            for symbol in symbols:
                if symbol == stock_symbol:
                    continue
                stock_return = state[symbol]["returns"].get(return_day)
                if stock_return is None:
                    continue
                membership = _scheduled_industry(
                    memberships_by_symbol[symbol],
                    return_day,
                    decision_time,
                )
                if membership is None:
                    continue
                if membership.industry_code != target_membership.industry_code:
                    continue
                peer_values.append(stock_return)

            if peer_values:
                common_days.append(return_day)
                industry_recent_by_day[return_day] = peer_values
                if len(common_days) >= lookback:
                    break

        if len(common_days) < lookback:
            continue

        recent_days = sorted(common_days)
        target_recent = [target_returns[d] for d in recent_days]
        industry_recent = [
            sum(industry_recent_by_day[d]) / len(industry_recent_by_day[d])
            for d in recent_days
        ]

        target_return_20 = _compounded(target_recent)
        industry_return_20 = _compounded(industry_recent)
        target_return_5 = _compounded(target_recent[-5:])
        industry_return_5 = _compounded(industry_recent[-5:])

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
