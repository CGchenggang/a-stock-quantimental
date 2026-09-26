"""Multi-input market regime classifier for the V2 pipeline.

This replaces the legacy single-index/weather concept with explicit inputs:
index trend, breadth, turnover, volatility, sector dispersion, limit-up/down
pressure and liquidity. Missing inputs reduce confidence and can yield UNKNOWN.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RegimeSnapshot:
    index_trend: float
    breadth: float
    turnover_z: float
    volatility_z: float
    sector_dispersion: float
    limit_pressure: float
    liquidity: float


REGIMES = ("TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOL", "RISK_OFF", "UNKNOWN")


def classify_regime(values: Mapping[str, float | None]) -> dict[str, float | str]:
    keys = (
        "index_trend", "breadth", "turnover_z", "volatility_z",
        "sector_dispersion", "limit_pressure", "liquidity",
    )
    present = [values.get(k) for k in keys]
    missing = sum(v is None for v in present)
    if missing >= 4:
        return {"regime": "UNKNOWN", "confidence": 0.0, "missing_inputs": missing}

    def num(k: str) -> float:
        v = values.get(k)
        return float(v) if v is not None else 0.0

    trend = num("index_trend")
    breadth = num("breadth")
    vol = num("volatility_z")
    liquidity = num("liquidity")
    pressure = num("limit_pressure")

    if vol >= 2.0:
        regime = "HIGH_VOL"
    elif liquidity <= -2.0 and pressure <= -1.0:
        regime = "RISK_OFF"
    elif trend >= 1.0 and breadth >= 0.5:
        regime = "TREND_UP"
    elif trend <= -1.0 and breadth <= -0.5:
        regime = "TREND_DOWN"
    else:
        regime = "RANGE"

    confidence = min(1.0, max(0.0, 1.0 - missing / len(keys)))
    return {
        "regime": regime,
        "confidence": round(confidence, 4),
        "missing_inputs": missing,
    }
