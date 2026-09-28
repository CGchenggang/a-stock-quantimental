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
    ordered = tuple(ordered)
    effective = tuple(item.effective_from for item in ordered)
    available = tuple(sorted(item.available_time for item in ordered))
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
    decision_dt = decision_time if isinstance(decision_time, datetime) else _parse_aware(decision_time)
    event_dt = datetime.fromisoformat(f"{day}T00:00:00+08:00")
    available_end = bisect_right(available, decision_dt)
    if available_end == 0:
        return None
    effective_end = bisect_right(effective, event_dt)
    index = min(available_end, effective_end) - 1
    if index < 0:
        return None
    return ordered[index]


def _historical_membership_maps(schedule, days):
    """Precompute effective-date membership for historical return-day lookups.

    With the project convention that an assignment effective on day D becomes
    available at 16:00 on the next calendar day, a return day earlier than the
    decision day can use the latest assignment effective on or before that
    return day. For the decision day itself, an assignment effective that same
    day is not yet available and must be excluded.
    """
    ordered, effective, _available = schedule
    effective_days = tuple(item.effective_from[:10] for item in ordered)
    on_or_before = {}
    before = {}
    for day in days:
        index = bisect_right(effective_days, day) - 1
        on_or_before[day] = ordered[index] if index >= 0 else None
        before_index = index
        while before_index >= 0 and effective_days[before_index] == day:
            before_index -= 1
        before[day] = ordered[before_index] if before_index >= 0 else None
    return on_or_before, before


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
    """Build stock-minus-SW1-industry returns from a local stock universe.

    For the single-stock path, restrict the return-state universe to stocks
    whose historical membership ever uses an industry code that the target
    stock itself has used. This is an exact candidate reduction: a peer can
    contribute only when its PIT membership code equals the target's
    decision-time industry code. Stocks that never share any such code can
    never contribute, so excluding them does not change the factor values.
    """
    if lookback < 20:
        raise ValueError("lookback must be at least 20")

    symbols = tuple(dict.fromkeys(str(s).strip().zfill(6) for s in universe_symbols))
    if stock_symbol not in symbols:
        symbols = (stock_symbol, *symbols)

    memberships = load_industry_memberships(membership_path)
    memberships_by_symbol = {}
    all_symbol_memberships = {}
    for symbol in symbols:
        schedule = _membership_schedule(
            [m for m in memberships if m.symbol == symbol]
        )
        all_symbol_memberships[symbol] = schedule
        memberships_by_symbol[symbol] = schedule

    target_schedule = memberships_by_symbol[stock_symbol]
    target_industry_codes = {
        membership.industry_code for membership in target_schedule[0]
        if membership.industry_code
    }

    candidate_symbols = tuple(
        symbol
        for symbol in symbols
        if symbol == stock_symbol
        or any(
            membership.industry_code in target_industry_codes
            for membership in all_symbol_memberships[symbol][0]
        )
    )

    # Only candidate peers can contribute to the target's industry benchmark.
    # This keeps the exact PIT lookup semantics while avoiding unrelated stocks
    # in the hot return-state and peer loop.
    memberships_by_symbol = {
        symbol: all_symbol_memberships[symbol]
        for symbol in candidate_symbols
    }
    all_records = {
        symbol: store.read_records("cn_stock_daily", symbol)
        for symbol in candidate_symbols
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
            target_schedule, day, decision_time
        )
        if target_membership is None:
            continue

        target_returns = state[stock_symbol]["returns"]

        # Only stocks that have ever used the target's industry codes can
        # contribute. Within that exact candidate set, preserve the original
        # newest-first target-return-day search semantics.
        peer_symbols = tuple(
            symbol
            for symbol in candidate_symbols
            if symbol != stock_symbol
            and target_membership.industry_code in {
                membership.industry_code
                for membership in memberships_by_symbol[symbol][0]
            }
        )

        common_days = []
        industry_recent_by_day: dict[str, list[float]] = {}
        for return_day in sorted(target_returns, reverse=True):
            peer_values: list[float] = []
            for symbol in peer_symbols:
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

def build_universe_industry_relative_context_maps(
    store: LocalHistoricalStore,
    membership_path: str | Path,
    universe_symbols: tuple[str, ...],
    *,
    lookback: int = 20,
) -> dict[str, dict[str, dict[str, float]]]:
    """Build PIT-safe industry-relative contexts once for the whole universe.

    The return state is shared across target stocks. For each decision day,
    peer benchmarks are computed lazily only for the historical return days
    actually requested by targets. This avoids rebuilding a full
    day x stock x history matrix at every decision boundary.
    """
    if lookback < 20:
        raise ValueError("lookback must be at least 20")

    symbols = tuple(dict.fromkeys(str(s).strip().zfill(6) for s in universe_symbols))
    memberships = load_industry_memberships(membership_path)
    memberships_by_symbol = {
        symbol: _membership_schedule(
            [m for m in memberships if m.symbol == symbol]
        )
        for symbol in symbols
    }
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
    historical_memberships = {
        symbol: _historical_membership_maps(
            memberships_by_symbol[symbol], event_days
        )
        for symbol in symbols
    }
    result = {symbol: {} for symbol in symbols}

    for pos in range(lookback, len(event_days)):
        day = event_days[pos]
        decision_time = f"{day}T16:00:00+08:00"
        _advance_pit_return_state(state, decision_time)
        decision_dt = _parse_aware(decision_time)
        membership_cache: dict[tuple[str, str], object] = {}

        def scheduled(symbol: str, lookup_day: str):
            key = (symbol, lookup_day)
            if key not in membership_cache:
                membership_cache[key] = _scheduled_industry(
                    memberships_by_symbol[symbol], lookup_day, decision_dt
                )
            return membership_cache[key]

        # Only active target industries are relevant on this decision day.
        current_membership: dict[str, object] = {}
        active_targets: list[tuple[str, object, HistoricalRecord]] = []
        target_industry_codes: set[str] = set()
        for symbol in symbols:
            target_current = state[symbol]["selected"].get(day)
            target_membership = scheduled(symbol, day)
            if target_current is None or target_membership is None:
                continue
            current_membership[symbol] = target_membership
            active_targets.append((symbol, target_membership, target_current))
            target_industry_codes.add(target_membership.industry_code)

        recent_peer_stats: dict[tuple[str, str], tuple[float, float]] = {}
        candidate_days = sorted(
            {return_day for item in state.values() for return_day in item["returns"]},
            reverse=True,
        )
        recent_candidate_days = candidate_days[:60]

        # Historical membership is an exact superset filter: if a symbol has
        # never carried an industry code, it can never be admissible for that
        # code at a later PIT decision time.
        historical_symbols_by_code: dict[str, tuple[str, ...]] = {}
        for code in target_industry_codes:
            historical_symbols_by_code[code] = tuple(
                symbol
                for symbol in symbols
                if any(
                    membership.industry_code == code
                    for membership in memberships_by_symbol[symbol][0]
                )
            )

        candidate_symbols = tuple(
            dict.fromkeys(
                symbol
                for code in target_industry_codes
                for symbol in historical_symbols_by_code[code]
            )
        )

        # Precompute only the industry aggregates actually requested by the
        # active targets.
        for return_day in recent_candidate_days:
            for symbol in candidate_symbols:
                stock_return = state[symbol]["returns"].get(return_day)
                if stock_return is None:
                    continue
                membership = (
                    historical_memberships[symbol][1].get(return_day)
                    if return_day == day
                    else historical_memberships[symbol][0].get(return_day)
                )
                if membership is None or membership.industry_code not in target_industry_codes:
                    continue
                key = (return_day, membership.industry_code)
                total, count = recent_peer_stats.get(key, (0.0, 0.0))
                recent_peer_stats[key] = (total + stock_return, count + 1.0)


        for symbol in symbols:
            target_current = state[symbol]["selected"].get(day)
            # Some validation symbols have no official SW1 history. They are
            # valid price-series symbols but cannot produce a PIT-safe
            # industry-relative factor, so skip them rather than indexing a
            # missing membership entry.
            target_membership = current_membership.get(symbol)
            if target_current is None or target_membership is None:
                continue

            target_returns = state[symbol]["returns"]
            common_days: list[str] = []
            industry_recent_by_day: dict[str, float] = {}

            # Preserve the exact single-stock search order: each target scans
            # its own available return days newest-first. The shared peer
            # aggregates are only an optimization for those same days.
            for return_day in recent_candidate_days:
                target_return = target_returns.get(return_day)
                if target_return is None:
                    continue
                key = (return_day, target_membership.industry_code)
                peer_sum, peer_count = recent_peer_stats.get(key, (0.0, 0.0))
                target_historical_membership = (
                    historical_memberships[symbol][1].get(return_day)
                    if return_day == day
                    else historical_memberships[symbol][0].get(return_day)
                )
                if (
                    target_historical_membership is not None
                    and target_historical_membership.industry_code
                    == target_membership.industry_code
                ):
                    peer_sum -= target_return
                    peer_count -= 1.0
                if peer_count <= 0:
                    continue
                common_days.append(return_day)
                industry_recent_by_day[return_day] = peer_sum / peer_count
                if len(common_days) >= lookback:
                    break

            if len(common_days) < lookback:
                # Exact fallback for sparse or short-lived industry membership.
                for return_day in candidate_days[60:]:
                    target_return = target_returns.get(return_day)
                    if target_return is None:
                        continue
                    key = (return_day, target_membership.industry_code)
                    peer_sum, peer_count = recent_peer_stats.get(key, (0.0, 0.0))
                    if key not in recent_peer_stats:
                        peer_sum = peer_count = 0.0
                        for peer_symbol in symbols:
                            peer_return = state[peer_symbol]["returns"].get(return_day)
                            if peer_return is None:
                                continue
                            peer_membership = (
                                historical_memberships[peer_symbol][1].get(return_day)
                                if return_day == day
                                else historical_memberships[peer_symbol][0].get(return_day)
                            )
                            if peer_membership is None or peer_membership.industry_code != target_membership.industry_code:
                                continue
                            peer_sum += peer_return
                            peer_count += 1.0
                        recent_peer_stats[key] = (peer_sum, peer_count)
                    target_historical_membership = (
                        historical_memberships[symbol][1].get(return_day)
                        if return_day == day
                        else historical_memberships[symbol][0].get(return_day)
                    )
                    if (
                        target_historical_membership is not None
                        and target_historical_membership.industry_code == target_membership.industry_code
                    ):
                        peer_sum -= target_return
                        peer_count -= 1.0
                    if peer_count <= 0:
                        continue
                    common_days.append(return_day)
                    industry_recent_by_day[return_day] = peer_sum / peer_count
                    if len(common_days) >= lookback:
                        break

            if len(common_days) < lookback:
                continue
            recent_days = sorted(common_days)
            target_recent = [target_returns[d] for d in recent_days]
            industry_recent = [industry_recent_by_day[d] for d in recent_days]
            target_return_20 = _compounded(target_recent)
            industry_return_20 = _compounded(industry_recent)
            target_return_5 = _compounded(target_recent[-5:])
            industry_return_5 = _compounded(industry_recent[-5:])

            result[symbol][decision_time] = {
                "industry_relative_return_5": (
                    target_return_5 - industry_return_5
                ),
                "industry_relative_return_20": (
                    target_return_20 - industry_return_20
                ),
            }

    return result


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
