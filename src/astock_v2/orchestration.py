"""P8 orchestration boundary for legacy V1 morning/pre-market snapshots.

This module deliberately does not execute legacy scripts. It normalizes their
already-produced JSON-like payloads into a V2-safe envelope while preserving
freshness/provenance uncertainty.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _iso(value: str) -> str:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def legacy_snapshot_to_v2(
    snapshot: dict[str, Any],
    *,
    source: str,
    available_time: str | None = None,
) -> dict[str, Any]:
    """Normalize a legacy collector result without upgrading its freshness claim.

    available_time must be supplied by the V2 orchestration layer when the
    snapshot becomes available. A legacy generated_at value is metadata only
    and is never silently treated as a decision-time observation.
    """
    if not isinstance(snapshot, dict):
        raise TypeError("legacy snapshot must be a dict")
    if not source:
        raise ValueError("source is required")

    generated_at = snapshot.get("generated_at")
    if generated_at:
        generated_at = _iso(str(generated_at))

    available = _iso(available_time) if available_time else None
    quality = snapshot.get("data_quality")
    if not isinstance(quality, dict):
        quality = {}

    return {
        "schema_version": "v2-legacy-orchestration-1",
        "source": str(source),
        "source_type": "legacy_orchestration",
        "generated_at": generated_at,
        "available_time": available,
        "freshness_status": "UNKNOWN" if available is None else "DECLARED_AVAILABLE",
        "realtime_admissible": False,
        "data_quality": quality,
        "payload": snapshot,
        "migration_warning": (
            "legacy snapshot retained as compatibility input; "
            "field-level PIT semantics must be established before backtesting"
        ),
    }


def collect_legacy_outputs(
    *,
    morning: dict[str, Any] | None = None,
    pre_market: dict[str, Any] | None = None,
    available_time: str | None = None,
) -> dict[str, Any]:
    """Compose legacy collector outputs behind one V2 orchestration boundary."""
    outputs: dict[str, Any] = {}
    if morning is not None:
        outputs["morning"] = legacy_snapshot_to_v2(
            morning, source="legacy_morning_collector", available_time=available_time
        )
    if pre_market is not None:
        outputs["pre_market"] = legacy_snapshot_to_v2(
            pre_market, source="legacy_pre_market_pipeline", available_time=available_time
        )
    return {
        "schema_version": "v2-legacy-orchestration-1",
        "outputs": outputs,
        "legacy_fallback": bool(outputs),
    }
