"""Explicit adapter from legacy observations into the V2 Point-in-Time contract.

The adapter requires callers to provide event_time and available_time explicitly.
This prevents a legacy fetch timestamp from silently becoming a historical event
timestamp and keeps cached/fallback observations distinguishable from primary data.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..types import DataPoint
from ..compat import LegacyObservation


def datapoint_from_legacy(
    observation: LegacyObservation,
    *,
    event_time: str,
    available_time: str | None = None,
    value: Any | None = None,
    quality: str = "C",
    raw_ref: str | None = None,
    revision: int = 0,
) -> DataPoint:
    """Convert a legacy observation only when its timing is explicitly known."""
    event = datetime.fromisoformat(event_time)
    available = datetime.fromisoformat(available_time or observation.fetched_at)
    if available < event:
        raise ValueError("available_time cannot precede event_time")

    source = observation.source
    if observation.fallback:
        source = f"{source}:fallback"

    return DataPoint(
        symbol=observation.symbol,
        event_time=event.isoformat(),
        available_time=available.isoformat(),
        source=source,
        source_type=observation.source_type,
        value=observation.value if value is None else value,
        quality=quality,
        raw_ref=raw_ref,
        revision=revision,
    )
