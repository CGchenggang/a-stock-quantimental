"""Freshness and provenance helpers for legacy data-layer payloads.

This module is intentionally independent of AkShare/network code. It lets the
migration boundary classify cached, fallback and primary observations before
they enter V2 workflows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def freshness_age_seconds(fetched_at: str, now: str | None = None) -> float:
    fetched = parse_timestamp(fetched_at)
    current = parse_timestamp(now) if now else datetime.now(timezone.utc)
    return max(0.0, (current - fetched).total_seconds())


def classify_legacy_payload(
    payload: dict[str, Any],
    *,
    now: str | None = None,
    realtime_ttl_seconds: int = 300,
) -> dict[str, Any]:
    """Classify a legacy payload without calling it realtime by default."""
    fetched_at = payload.get("fetched_at") or payload.get("ts")
    source = str(payload.get("source") or "legacy_unknown")
    if not fetched_at:
        return {
            "source": source,
            "status": "UNKNOWN",
            "age_seconds": None,
            "is_realtime_admissible": False,
            "reason": "missing_fetched_at",
        }

    age = freshness_age_seconds(str(fetched_at), now)
    fallback = bool(payload.get("fallback")) or "fallback" in source.lower()
    stale = bool(payload.get("is_stale")) or age > realtime_ttl_seconds

    if fallback:
        status = "FALLBACK"
    elif stale:
        status = "STALE"
    else:
        status = "FRESH"

    return {
        "source": source,
        "status": status,
        "age_seconds": age,
        "is_realtime_admissible": status == "FRESH",
        "reason": "fallback" if fallback else ("ttl_expired" if stale else "within_ttl"),
    }
