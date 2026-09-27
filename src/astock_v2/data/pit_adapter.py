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


def minute_klines_to_datapoints(
    payload: dict[str, Any],
    *,
    fetched_at: str,
    quality: str = "B",
    raw_ref: str | None = None,
    revision: int = 0,
) -> list[DataPoint]:
    """Convert legacy minute K-lines to PIT OHLCV datapoints.

    The bar timestamp remains event_time; fetched_at is available_time.
    This deliberately does not infer event_time from retrieval time.
    """
    code = str(payload.get("code") or "").strip()
    if not code:
        raise ValueError("minute kline payload requires code")
    klines = payload.get("klines")
    if not isinstance(klines, list):
        raise ValueError("minute kline payload requires klines list")

    available = _iso(fetched_at)
    scale = int(payload.get("scale") or 1)
    points: list[DataPoint] = []

    for bar in klines:
        if not isinstance(bar, dict) or not bar.get("time"):
            raise ValueError("each minute kline requires time")
        event = _iso(str(bar["time"]))
        if available < event:
            raise ValueError("available_time cannot precede event_time")
        points.append(
            DataPoint(
                symbol=code,
                event_time=event,
                available_time=available,
                source="legacy_sina_minute",
                source_type="legacy_adapter",
                value={
                    "scale": scale,
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "close": bar.get("close"),
                    "volume": bar.get("volume"),
                },
                quality=quality,
                raw_ref=raw_ref,
                revision=revision,
            )
        )
    return points
