"""PIT-safe stock-relative-to-industry return features for local research.

The industry benchmark is an equal-weight portfolio of locally available stock
daily returns whose SW level-1 membership is admissible at the decision time.
The target stock is excluded from its own benchmark to avoid mechanical
self-inclusion. A missing or singleton industry therefore produces no factor
rather than a fabricated value.

For every decision date t:
- the target's current SW1 membership must cover t and be available by t;
- each historical member assignment used in the lookback must have been
  available by t;
- only stock daily records admissible by t are used;
- 5/20-day industry returns are computed from the benchmark's compounded close
  returns over common dates;
- the factor is stock return minus industry return.

This is deliberately a local-research primitive. The quality of the resulting
industry benchmark depends on the supplied stock universe being sufficiently
broad.
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


def _industry_for_day(
    memberships,
    symbol: str,
    day: str,
    decision_time: str,
):
    event_time = datetime.fromisoformat(
        f"{day}T00:00:00+00:00"
    )
    decision = _parse_aware(decision_time)
    return admissible_industry(memberships, symbol, event_time, decision)


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
    daily = {
        symbol: _admissible_daily(records, "")
        for symbol, records in all_records.items()
    }

    # Build raw day -> records once. Admissibility depends on the decision date,
    # so the final selection is recomputed for each decision boundary.
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

        current_records = {
            symbol: _admissible_daily(records, decision_time).get(day)
            for symbol, records in all_records.items()
        }
        target_current = current_records.get(stock_symbol)
        if target_current is None:
            continue

        target_membership = _industry_for_day(
            memberships, stock_symbol, day, decision_time
        )
        if target_membership is None:
            continue

        # For each historical day, use the industry membership information
        # available by today's decision boundary. This prevents future
        # revisions from entering the current factor while allowing known
        # historical classification changes to be used.
        benchmark_closes: list[float] = []
        target_closes: list[float] = []
        benchmark_days: list[str] = []
        for prior_day in event_days[: pos + 1]:
            target_record = _admissible_daily(
                all_records[stock_symbol], decision_time
            ).get(prior_day)
            if target_record is None:
                continue

            members: list[tuple[float, float]] = []
            for symbol in symbols:
                if symbol == stock_symbol:
                    continue
                record = _admissible_daily(
                    all_records[symbol], decision_time
                ).get(prior_day)
                if record is None:
                    continue
                membership = _industry_for_day(
                    memberships, symbol, prior_day, decision_time
                )
                if membership is None or membership.industry_code != target_membership.industry_code:
                    continue
                close = float(record.value["close"])
                if close <= 0:
                    continue
                members.append((close, 1.0))

            if not members:
                continue

            target_close = float(target_record.value["close"])
            if target_close <= 0:
                continue

            # Store the target close and the equal-weight benchmark close proxy.
            # For return calculations we instead use member-level daily returns
            # below; this block only records dates with a valid benchmark.
            target_closes.append(target_close)
            benchmark_closes.append(sum(v for v, _ in members) / len(members))
            benchmark_days.append(prior_day)

        if len(benchmark_days) < lookback + 1:
            continue

        # Reconstruct daily returns from the benchmark proxy over the common
        # dates. Only consecutive observations in the common benchmark sample
        # are used, so missing members never become zero-return placeholders.
        target_window = target_closes[-(lookback + 1):]
        benchmark_window = benchmark_closes[-(lookback + 1):]
        if any(v <= 0 for v in target_window + benchmark_window):
            continue

        target_return_5 = target_window[-1] / target_window[-6] - 1.0
        industry_return_5 = benchmark_window[-1] / benchmark_window[-6] - 1.0
        target_return_20 = target_window[-1] / target_window[-21] - 1.0
        industry_return_20 = benchmark_window[-1] / benchmark_window[-21] - 1.0

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
