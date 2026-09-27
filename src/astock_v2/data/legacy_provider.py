"""Adapters for moving legacy market payloads across the V2 provider boundary."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .providers import ProviderResult


def provider_result_from_legacy_payload(
    payload: dict[str, Any],
    *,
    source_type: str = "legacy_adapter",
    available_time: str | None = None,
    fetched_at: str | None = None,
) -> ProviderResult:
    """Normalize a legacy response while preserving provenance and fallback state.

    fetched_at may be supplied by an adapter when the legacy payload itself
    has no fetch timestamp. This records adapter fetch completion, not the
    market event time.
    """
    fetched_value = fetched_at or payload.get("fetched_at") or payload.get("ts")
    if not fetched_value:
        raise ValueError("legacy payload requires fetched_at or ts")

    fetched = datetime.fromisoformat(str(fetched_value).replace("Z", "+00:00"))
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)

    available = available_time or fetched.isoformat()
    warnings = list(payload.get("warnings") or [])
    if payload.get("warning"):
        warnings.append(str(payload["warning"]))
    if payload.get("_note"):
        warnings.append(str(payload["_note"]))

    source = str(payload.get("source") or "legacy_unknown")
    fallback = bool(payload.get("fallback")) or "fallback" in source.lower()
    return ProviderResult(
        data=payload,
        source=source,
        source_type=source_type,
        fetched_at=fetched.isoformat(),
        available_time=available,
        latency_ms=payload.get("latency_ms"),
        fallback=fallback,
        warnings=warnings,
    )
