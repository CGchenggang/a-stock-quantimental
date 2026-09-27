"""Build a V2 research packet directly from a MarketProvider."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from .agent.orchestrator import ResearchPacket
from .data.providers import MarketProvider, ProviderResult
from .data.legacy_market_inputs import LegacyMarketInputs
from .regime import classify_regime

def _iso(value: str) -> str:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def _pit_admissible(result: ProviderResult, decision_time: str) -> bool:
    if not result.available_time:
        return False
    try:
        return _iso(result.available_time) <= _iso(decision_time)
    except (TypeError, ValueError):
        return False

def _health(results: list[ProviderResult], decision_time: str) -> dict[str, Any]:
    total = len(results)
    missing = sum(result.data in (None, {}, []) for result in results)
    fallback = sum(bool(result.fallback) for result in results)
    warning_count = sum(len(result.warnings) for result in results)
    available = [result.available_time for result in results if result.available_time]
    future_data = [result for result in results if result.available_time and not _pit_admissible(result, decision_time)]
    pit_admissible = sum(_pit_admissible(result, decision_time) for result in results)
    return {
        "score": round(
            max(0.0, 1.0 - missing / total) * 0.5
            + max(0.0, 1.0 - fallback / total) * 0.3
            + max(0.0, 1.0 - warning_count / max(1, total)) * 0.2, 4),
        "provider_results": total,
        "missing_ratio": missing / total if total else 1.0,
        "fallback_ratio": fallback / total if total else 1.0,
        "warning_count": warning_count,
        "available_times": available,
        "decision_time": _iso(decision_time),
        "pit_admissible_ratio": pit_admissible / total if total else 0.0,
        "future_data_count": len(future_data),
        "availability_complete": all(
            result.available_time is not None and not result.fallback for result in results
        ) if results else False,
        "pit_admissible": all(
            _pit_admissible(result, decision_time) and not result.fallback for result in results
        ) if results else False,
    }

def build_research_packet_from_provider(
    provider: MarketProvider, *, symbol: str, decision_time: str,
    daily_start: str, daily_end: str,
) -> ResearchPacket:
    """Consume V2 provider results and create evidence-only research context."""
    decision = _iso(decision_time)
    quote = provider.quote([symbol])
    daily = provider.daily(symbol, daily_start, daily_end)
    market_inputs = LegacyMarketInputs(provider).regime_inputs(decision_time=decision)
    regime_result = classify_regime(market_inputs["inputs"])
    health = _health(
        [quote, daily, market_inputs["provenance"]["index"], market_inputs["provenance"]["sector"]],
        decision,
    )
    quote_admissible = _pit_admissible(quote, decision)
    return ResearchPacket(
        symbol=symbol, decision_time=decision,
        market={
            "quotes": quote.data.get("quotes", {}) if quote_admissible and isinstance(quote.data, dict) else {},
            "source": quote.source, "available_time": quote.available_time,
            "regime_inputs": market_inputs["inputs"], "regime": regime_result,
            "regime_provenance": market_inputs["provenance"],
            "regime_proxy_fields": market_inputs["proxy_fields"],
            "regime_missing_fields": market_inputs["missing_fields"],
        },
        stock={
            "daily": daily.data if _pit_admissible(daily, decision) else [],
            "source": daily.source, "supporting_evidence": [],
            "contradictory_evidence": [], "missing_evidence": [],
        },
        factors={}, events=[], model={}, risk={"flags": ["QUANT_MODEL_NOT_RUN"]},
        data_quality=health,
    )
