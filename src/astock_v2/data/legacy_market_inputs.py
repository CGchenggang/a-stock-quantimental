"""Adapters for V1 market-wide inputs consumed by the V2 regime layer."""
from __future__ import annotations
from math import sqrt
from typing import Any
from .legacy_provider import provider_result_from_legacy_payload
from .providers import MarketProvider, ProviderResult, pit_admissible
from ..data_quality import summarize_pit

def _std(values: list[float]) -> float | None:
    if len(values) < 2: return None
    mean = sum(values) / len(values)
    return sqrt(sum((x - mean) ** 2 for x in values) / len(values))

def _breadth_from_quotes(quotes: dict[str, Any]) -> dict[str, float | int | None]:
    rows = [v for v in quotes.values() if isinstance(v, dict) and v.get("price") is not None]
    # Proxy breadth convention: non-declining quotes (pct >= 0) count as
    # advancers, so a flat market reads as mildly positive, not as zero sample.
    up = sum(float(r.get("pct") or 0) >= 0 for r in rows)
    down = sum(float(r.get("pct") or 0) < 0 for r in rows)
    total = len(rows)
    limit_up = sum(float(r.get("pct") or 0) >= 9.8 for r in rows)
    limit_down = sum(float(r.get("pct") or 0) <= -9.8 for r in rows)
    return {
        "sample_size": total, "advancers": up, "decliners": down,
        "unchanged": total - up - down, "breadth": (up - down) / total if total else None,
        "limit_up": limit_up, "limit_down": limit_down,
        "limit_pressure": (limit_up - limit_down) / total if total else None,
    }

class LegacyMarketInputs:
    """Build explicit, labeled V2 market-regime inputs from legacy market payloads."""
    def __init__(self, provider: MarketProvider): self.provider = provider

    def snapshot(self, decision_time: str | None = None) -> dict[str, Any]:
        quote = self.provider.quote([])
        data = quote.data if isinstance(quote.data, dict) else {}
        admissible = decision_time is None or pit_admissible(quote, decision_time)
        breadth = _breadth_from_quotes(data.get("quotes") or {}) if admissible else _breadth_from_quotes({})
        return {"quote": quote, "breadth": {
            **breadth, "source": quote.source, "proxy": True,
            "warning": "derived from V1 full-market quote snapshot",
        }}

    def sector_dispersion(self, payload: dict[str, Any]) -> ProviderResult:
        values = [float(r["pct"]) for r in payload.get("sectors", []) if isinstance(r, dict) and r.get("pct") is not None]
        dispersion = _std(values)
        normalized = {"sector_count": len(values), "pct_std": dispersion, "sector_dispersion": dispersion, "proxy": True}
        return provider_result_from_legacy_payload(
            {"source": payload.get("source", "legacy_sector_board"), "fetched_at": payload.get("ts"), "data": normalized},
            source_type="legacy_sector_provider", available_time=payload.get("ts"))

    def regime_inputs(self, index_symbol: str = "sh000300", decision_time: str | None = None) -> dict[str, Any]:
        market = self.snapshot(decision_time=decision_time)
        index = self.provider.index_daily(index_symbol)
        sector = self.provider.sector_board()
        try:
            turnover = self.provider.market_turnover()
        except NotImplementedError:
            turnover = ProviderResult(data={"turnover_z": None, "pit_ready": False}, source="unavailable",
                source_type="missing", fetched_at="", available_time=None,
                warnings=["market turnover provider is not configured"])
        ia = decision_time is None or pit_admissible(index, decision_time)
        sa = decision_time is None or pit_admissible(sector, decision_time)
        ta = decision_time is None or pit_admissible(turnover, decision_time)
        index_data = index.data if ia and isinstance(index.data, dict) else {}
        pct = float(index_data.get("pct") or 0.0)
        above = index_data.get("above_ma20")
        index_trend = ((1.0 if above else -1.0) + max(-1.0, min(1.0, pct / 3.0))) if index_data else None
        sector_data = sector.data if sa and isinstance(sector.data, dict) else {}
        values = [float(r["pct"]) for r in sector_data.get("sectors", []) if isinstance(r, dict) and r.get("pct") is not None]
        dispersion = _std(values)
        breadth = market["breadth"]
        inputs = {
            "index_trend": index_trend, "breadth": breadth["breadth"],
            "turnover_z": turnover.data.get("turnover_z") if ta and isinstance(turnover.data, dict) and turnover.data.get("pit_ready") else None,
            "volatility_z": index_data.get("volatility_z"),
            "sector_dispersion": dispersion, "limit_pressure": breadth["limit_pressure"],
            "liquidity": None,
        }
        provenance = {"index": index, "quote": market["quote"], "sector": sector, "turnover": turnover}
        data_quality = summarize_pit(provenance.values(), decision_time) if decision_time is not None else None
        return {
            "inputs": inputs,
            "provenance": provenance,
            "proxy_fields": ["breadth", "limit_pressure", "index_trend", "sector_dispersion"],
            "missing_fields": [k for k, v in inputs.items() if v is None],
            "missing_reasons": {
                "liquidity": "no PIT-complete dedicated liquidity history is currently migrated"
            } if inputs["liquidity"] is None else {},
            "data_quality": data_quality.as_dict() if data_quality is not None else None,
        }
