"""Build a V2 research packet directly from a MarketProvider."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .agent.orchestrator import ResearchPacket
from .data.providers import MarketProvider, ProviderResult


def _iso(value: str) -> str:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _health(results: list[ProviderResult]) -> dict[str, Any]:
    total = len(results)
    missing = sum(result.data in (None, {}, []) for result in results)
    fallback = sum(bool(result.fallback) for result in results)
    warning_count = sum(len(result.warnings) for result in results)
    available = [result.available_time for result in results if result.available_time]
    return {
        "score": round(
            max(0.0, 1.0 - missing / total) * 0.5
            + max(0.0, 1.0 - fallback / total) * 0.3
            + max(0.0, 1.0 - warning_count / max(1, total)) * 0.2,
            4,
        ),
        "provider_results": total,
        "missing_ratio": missing / total if total else 1.0,
        "fallback_ratio": fallback / total if total else 1.0,
        "warning_count": warning_count,
        "available_times": available,
        "realtime_admissible": all(
            result.available_time is not None and not result.fallback
            for result in results
        ) if results else False,
    }


def build_research_packet_from_provider(
    provider: MarketProvider,
    *,
    symbol: str,
    decision_time: str,
    daily_start: str,
    daily_end: str,
) -> ResearchPacket:
    """Consume V2 provider results and create evidence-only research context.

    No factor/model/risk output is inferred here. Quantitative model outputs
    remain the responsibility of later V2 stages.
    """
    decision = _iso(decision_time)
    quote = provider.quote([symbol])
    daily = provider.daily(symbol, daily_start, daily_end)
    health = _health([quote, daily])

    return ResearchPacket(
        symbol=symbol,
        decision_time=decision,
        market={
            "quotes": quote.data.get("quotes", {}) if isinstance(quote.data, dict) else {},
            "source": quote.source,
            "available_time": quote.available_time,
        },
        stock={
            "daily": daily.data,
            "source": daily.source,
            "supporting_evidence": [],
            "contradictory_evidence": [],
            "missing_evidence": [],
        },
        factors={},
        events=[],
        model={},
        risk={"flags": ["QUANT_MODEL_NOT_RUN"]},
        data_quality=health,
    )
