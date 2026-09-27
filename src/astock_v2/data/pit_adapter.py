"""Adapters from legacy market payloads into V2 Point-in-Time data."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..types import DataPoint


def _iso(value: str) -> str:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _point(
    *,
    symbol: str,
    event_time: str,
    available_time: str,
    value: Any,
    source: str,
    quality: str,
    raw_ref: str | None,
    revision: int,
) -> DataPoint:
    event = _iso(event_time)
    available = _iso(available_time)
    if available < event:
        raise ValueError("available_time cannot precede event_time")
    return DataPoint(
        symbol=symbol,
        event_time=event,
        available_time=available,
        source=source,
        source_type="legacy_adapter",
        value=value,
        quality=quality,
        raw_ref=raw_ref,
        revision=revision,
    )


def daily_latest_to_datapoint(
    payload: dict[str, Any],
    *,
    available_time: str,
    quality: str = "B",
    raw_ref: str | None = None,
    revision: int = 0,
) -> DataPoint:
    """Convert the latest legacy daily bar without inventing availability time."""
    code = str(payload.get("code") or "").strip()
    latest_date = payload.get("latest_date")
    latest = payload.get("latest")
    if not code:
        raise ValueError("daily payload requires code")
    if not latest_date or not isinstance(latest, dict):
        raise ValueError("daily payload requires latest_date and latest")

    return _point(
        symbol=code,
        event_time=str(latest_date),
        available_time=available_time,
        value=latest,
        source="legacy_daily",
        quality=quality,
        raw_ref=raw_ref,
        revision=revision,
    )


def minute_klines_to_datapoints(
    payload: dict[str, Any],
    *,
    fetched_at: str,
    quality: str = "B",
    raw_ref: str | None = None,
    revision: int = 0,
) -> list[DataPoint]:
    """Convert legacy minute K-lines to PIT OHLCV datapoints."""
    code = str(payload.get("code") or "").strip()
    if not code:
        raise ValueError("minute kline payload requires code")
    klines = payload.get("klines")
    if not isinstance(klines, list):
        raise ValueError("minute kline payload requires klines list")

    scale = int(payload.get("scale") or 1)
    points: list[DataPoint] = []
    for bar in klines:
        if not isinstance(bar, dict) or not bar.get("time"):
            raise ValueError("each minute kline requires time")
        points.append(
            _point(
                symbol=code,
                event_time=str(bar["time"]),
                available_time=fetched_at,
                value={
                    "scale": scale,
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "close": bar.get("close"),
                    "volume": bar.get("volume"),
                },
                source="legacy_sina_minute",
                quality=quality,
                raw_ref=raw_ref,
                revision=revision,
            )
        )
    return points
