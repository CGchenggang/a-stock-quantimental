"""Focused adapters for high-value V1 market provider payloads."""
from __future__ import annotations

from typing import Any

from .legacy_provider import provider_result_from_legacy_payload
from .providers import ProviderResult


def legacy_quote_result(
    payload: dict[str, Any],
    *,
    available_time: str,
) -> ProviderResult:
    """Adapt a V1 realtime quote while requiring explicit V2 availability."""
    return provider_result_from_legacy_payload(
        payload,
        source_type="legacy_quote_provider",
        available_time=available_time,
    )


def legacy_daily_result(
    payload: dict[str, Any],
    *,
    available_time: str,
) -> ProviderResult:
    """Adapt a V1 daily-history result without changing its payload semantics."""
    return provider_result_from_legacy_payload(
        payload,
        source_type="legacy_daily_provider",
        available_time=available_time,
    )


def legacy_intraday_result(
    payload: dict[str, Any],
    *,
    available_time: str,
    fetched_at: str | None = None,
) -> ProviderResult:
    """Adapt V1 intraday output; fetch time may come from the adapter boundary."""
    result = provider_result_from_legacy_payload(
        payload,
        source_type="legacy_intraday_provider",
        available_time=available_time,
        fetched_at=fetched_at,
    )
    if not isinstance(result.data.get("klines"), list):
        raise ValueError("legacy intraday payload requires klines list")
    if not result.data.get("scale"):
        raise ValueError("legacy intraday payload requires explicit scale")
    return result


def legacy_sector_result(
    payload: dict[str, Any],
    *,
    available_time: str,
) -> ProviderResult:
    """Adapt the legacy sector-board snapshot."""
    return provider_result_from_legacy_payload(
        payload,
        source_type="legacy_sector_provider",
        available_time=available_time,
    )
