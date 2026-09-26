"""Compatibility bridge for gradually migrating legacy V1 scripts into V2 contracts.

This module deliberately does not promote legacy data to "real-time" or
Point-in-Time truth without explicit provenance. Legacy observations are
returned with source, fetched time, freshness, and fallback status so callers
can decide whether they are admissible for a V2 workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class LegacyObservation:
    symbol: str
    value: Any
    source: str
    fetched_at: str
    is_stale: bool = False
    fallback: bool = False
    warning: str | None = None

    @property
    def source_type(self) -> str:
        return "legacy_adapter"


def observation_from_legacy(symbol: str, payload: dict[str, Any], *, fetched_at: str | None = None) -> LegacyObservation:
    """Normalize a legacy data-layer payload without relabeling its provenance."""
    fetched = fetched_at or datetime.now(timezone.utc).isoformat()
    source = str(payload.get("source") or "legacy_unknown")
    fallback = "fallback" in source or source.endswith("_stale") or source == "prev_close_fallback"
    return LegacyObservation(
        symbol=symbol,
        value=payload,
        source=source,
        fetched_at=fetched,
        is_stale=bool(payload.get("is_stale", False)),
        fallback=fallback,
        warning=payload.get("_note") or payload.get("warning"),
    )


def call_legacy_realtime(fetcher: Callable[[str], dict[str, Any]], symbol: str) -> LegacyObservation:
    """Call a legacy realtime function and preserve fallback/staleness metadata."""
    return observation_from_legacy(symbol, fetcher(symbol))


LEGACY_SCRIPT_ROLES = {
    "scripts/data_layer.py": "legacy data provider; migration target: astock_v2.data.providers",
    "scripts/market_regime_check.py": "legacy single-index regime check; migration target: multi-input regime engine",
    "scripts/intraday_reversal_detector.py": "legacy intraday heuristic; migration target: factor/event pipeline",
    "scripts/morning_collector.py": "legacy collection orchestration; migration target: P1 data adapters + agent workflow",
    "scripts/pre_market_pipeline.py": "legacy orchestration; migration target: V2 CLI/orchestrator",
    "scripts/stock_diagoser.py": "legacy stock analysis; migration target: stock-research skill + quant packet",
}


def legacy_regime_mapping(weather: str) -> str:
    """Map legacy weather labels for display only; never treat as validated regime truth."""
    return {
        "SUNNY": "TREND_UP",
        "CLOUDY": "RANGE",
        "RAIN": "TREND_DOWN",
        "STORM": "RISK_OFF",
    }.get(str(weather).upper(), "UNKNOWN")
