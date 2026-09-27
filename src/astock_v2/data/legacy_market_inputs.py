"""Adapters for V1 market-wide inputs consumed by the V2 regime layer."""
from __future__ import annotations

from math import sqrt
from typing import Any

from .legacy_provider import provider_result_from_legacy_payload
from .providers import MarketProvider, ProviderResult


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _breadth_from_quotes(quotes: dict[str, Any]) -> dict[str, float | int | None]:
    rows = [
        value for value in quotes.values()
        if isinstance(value, dict) and value.get("price") is not None
    ]
    up = sum(float(row.get("pct") or 0) > 0 for row in rows)
    down = sum(float(row.get("pct") or 0) < 0 for row in rows)
    flat = len(rows) - up - down
    limit_up = sum(float(row.get("pct") or 0) >= 9.8 for row in rows)
    limit_down = sum(float(row.get("pct") or 0) <= -9.8 for row in rows)
    total = len(rows)
    return {
        "sample_size": total,
        "advancers": up,
        "decliners": down,
        "unchanged": flat,
        "breadth": (up - down) / total if total else None,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "limit_pressure": (limit_up - limit_down) / total if total else None,
    }


class LegacyMarketInputs:
    """Build explicit, labeled V2 market-regime inputs from legacy payloads."""

    def __init__(self, provider: MarketProvider):
        self.provider = provider

    def snapshot(self) -> dict[str, Any]:
        quote = self.provider.quote([])
        quote_data = quote.data if isinstance(quote.data, dict) else {}
        quotes = quote_data.get("quotes") or {}
        breadth = _breadth_from_quotes(quotes)

        # Quote provider is allowed to scope an empty request to all V1 quotes.
        # The resulting breadth is therefore a cross-sectional proxy, not a
        # canonical exchange breadth feed.
        return {
            "quote": quote,
            "breadth": {
                **breadth,
                "source": quote.source,
                "proxy": True,
                "warning": "derived from V1 full-market quote snapshot",
            },
        }

    def sector_dispersion(self, payload: dict[str, Any]) -> ProviderResult:
        values = [
            float(row["pct"])
            for row in payload.get("sectors", [])
            if isinstance(row, dict) and row.get("pct") is not None
        ]
        dispersion = _std(values)
        normalized = {
            "sector_count": len(values),
            "pct_std": dispersion,
            "sector_dispersion": dispersion,
            "proxy": True,
        }
        return provider_result_from_legacy_payload(
            {
                "source": payload.get("source", "legacy_sector_board"),
                "fetched_at": payload.get("ts"),
                "data": normalized,
            },
            source_type="legacy_sector_provider",
            available_time=payload.get("ts"),
        )


    def regime_inputs(self, index_symbol: str = "sh000300") -> dict[str, Any]:
        """Return P3-compatible inputs plus provenance and explicit missing fields."""
        market = self.snapshot()
        index = self.provider.index_daily(index_symbol)
        sector = self.provider.sector_board()
        try:
            turnover = self.provider.market_turnover()
        except NotImplementedError:
            turnover = ProviderResult(
                data={"turnover_z": None, "pit_ready": False},
                source="unavailable",
                source_type="missing",
                fetched_at="",
                available_time=None,
                warnings=["market turnover provider is not configured"],
            )

        index_data = index.data if isinstance(index.data, dict) else {}
        pct = float(index_data.get("pct") or 0.0)
        above_ma20 = index_data.get("above_ma20")
        index_trend = (1.0 if above_ma20 else -1.0) + max(-1.0, min(1.0, pct / 3.0))

        sector_data = sector.data if isinstance(sector.data, dict) else {}
        values = [
            float(row["pct"])
            for row in sector_data.get("sectors", [])
            if isinstance(row, dict) and row.get("pct") is not None
        ]
        dispersion = _std(values)

        breadth = market["breadth"]
        inputs = {
            "index_trend": index_trend,
            "breadth": breadth["breadth"],
            "turnover_z": (turnover.data.get("turnover_z") if isinstance(turnover.data, dict) and turnover.data.get("pit_ready") else None),
            "volatility_z": index_data.get("volatility_z"),
            "sector_dispersion": dispersion,
            "limit_pressure": breadth["limit_pressure"],
            "liquidity": None,
        }
        return {
            "inputs": inputs,
            "provenance": {
                "index": index,
                "quote": market["quote"],
                "sector": sector,
                "turnover": turnover,
            },
            "proxy_fields": [
                "breadth",
                "limit_pressure",
                "index_trend",
                "sector_dispersion",
            ],
            "missing_fields": [key for key, value in inputs.items() if value is None],
        }
