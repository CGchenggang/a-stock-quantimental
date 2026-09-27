"""Legacy-backed V2 market provider.

The adapter keeps V1 payloads intact but narrows quote results to the symbols
requested by the V2 contract. The full V1 response remains available as
provenance metadata so narrowing never silently discards source evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .legacy_market_provider import legacy_daily_result, legacy_quote_result
from .providers import MarketProvider, ProviderResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_symbol(symbol: str) -> str:
    value = str(symbol).strip()
    if value.startswith(("sh", "sz")) and len(value) > 2:
        return value[2:]
    return value


class LegacyMarketProvider(MarketProvider):
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

        result = legacy_quote_result(
            payload, available_time=_now_iso()
        )
        quotes = payload.get("quotes")
        if not isinstance(quotes, dict):
            raise ValueError("legacy realtime payload requires quotes dict")

        requested = {_clean_symbol(s) for s in symbols}
        selected: dict[str, Any] = {}
        for key, value in quotes.items():
            if _clean_symbol(str(key)) in requested:
                selected[_clean_symbol(str(key))] = value

        return ProviderResult(
            data={
                "ok": bool(payload.get("ok", False)),
                "quotes": selected,
                "requested_symbols": sorted(requested),
                "legacy_payload": payload,
            },
            source=result.source,
            source_type=result.source_type,
            fetched_at=result.fetched_at,
            available_time=result.available_time,
            latency_ms=result.latency_ms,
            fallback=result.fallback,
            warnings=result.warnings,
        )

    def daily(self, symbol: str, start: str, end: str) -> ProviderResult:
        days = max(
            1,
            (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days + 1,
        )
        payload = self._daily_fetcher(symbol, days)
        if not isinstance(payload, dict):
            raise TypeError("legacy daily fetcher must return dict")
        return legacy_daily_result(payload, available_time=_now_iso())
