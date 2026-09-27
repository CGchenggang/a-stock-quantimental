"""Build a PIT-safe factor/label dataset from local A-share daily history."""
from __future__ import annotations

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


def build_local_factor_rows(
    store: LocalHistoricalStore,
    symbol: str,
    *,
    factor_names: tuple[str, ...] = ("momentum", "volatility", "trend", "volume_ratio"),
    lookback: int = 20,
) -> tuple[LocalFactorRow, ...]:
    """Build one training observation per completed trading day.

    The factor snapshot for day t uses only records available by t's
    decision_time. The label is the next trading day's close return, which is
    deliberately not included in the factor input.
    """
    records = store.read_records("cn_stock_daily", symbol)
    if len(records) < lookback + 2:
        return ()

    ordered = sorted(records, key=lambda r: (r.event_time, r.revision))
    latest: dict[str, HistoricalRecord] = {}
    for record in ordered:
        current = latest.get(record.event_time)
        if current is None or record.revision > current.revision:
            latest[record.event_time] = record
    days = sorted(latest.values(), key=lambda r: r.event_time)

    rows: list[LocalFactorRow] = []
    for index in range(lookback, len(days) - 1):
        current = days[index]
        decision_time = current.available_time
        if not decision_time:
            continue
        _parse_aware(decision_time)

        # Only records available at the current decision boundary may enter
        # the factor provider result.
        admitted = [
            record for record in days[: index + 1]
            if record.admissible_at(decision_time)
        ]
        if len(admitted) < lookback + 1:
            continue

        provider_rows = [dict(record.value) for record in admitted]
        provider = ProviderResult(
            data=provider_rows,
            source="local:cn_stock_daily",
            source_type="local_historical",
            fetched_at="",
            available_time=decision_time,
        )

        factors = {}
        outputs = []
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
            outputs.append(output)
        if len(outputs) != len(factor_names):
            continue

        today_close = float(current.value["close"])
        next_close = float(days[index + 1].value["close"])
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
