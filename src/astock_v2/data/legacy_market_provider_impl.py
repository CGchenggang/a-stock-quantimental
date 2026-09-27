"""Legacy-backed V2 market provider.

This adapter is intentionally thin: it calls existing V1 functions and wraps
their outputs with explicit provenance. It does not recompute or relabel V1 data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .legacy_market_provider import legacy_daily_result, legacy_quote_result
from .providers import MarketProvider, ProviderResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LegacyMarketProvider(MarketProvider):
    """Expose selected V1 data-layer functions through the V2 provider contract."""

    name = "legacy_v1"

    def __init__(
        self,
        *,
        realtime_fetcher: Callable[[], dict[str, Any]],
        daily_fetcher: Callable[[str, int], dict[str, Any]],
    ) -> None:
        self._realtime_fetcher = realtime_fetcher
        self._daily_fetcher = daily_fetcher

    def quote(self, symbols: list[str]) -> ProviderResult:
        payload = self._realtime_fetcher()
        if not isinstance(payload, dict):
            raise TypeError("legacy realtime fetcher must return dict")
        return legacy_quote_result(payload, available_time=_now_iso())

    def daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        days = max(1, (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days + 1)
        payload = self._daily_fetcher(symbol, days)
        if not isinstance(payload, dict):
            raise TypeError("legacy daily fetcher must return dict")
        return legacy_daily_result(payload, available_time=_now_iso())
