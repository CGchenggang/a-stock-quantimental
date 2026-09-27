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
) -> ProviderResult:
    """Adapt V1 intraday output; granularity remains an explicit caller contract."""
    result = provider_result_from_legacy_payload(
        payload,
        source_type="legacy_intraday_provider",
        available_time=available_time,
    )
    if not isinstance(result.data.get("klines"), list):
        raise ValueError("legacy intraday payload requires klines list")
    if not result.data.get("scale"):
        raise ValueError("legacy intraday payload requires explicit scale")
    return result
