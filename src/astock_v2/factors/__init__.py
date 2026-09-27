"""Public factor API and backward-compatible deterministic price/volume factors."""
from __future__ import annotations
from math import log, sqrt
from statistics import mean, pstdev
from typing import Any, Callable, Mapping, Sequence
from ..data.providers import ProviderResult
from ..factor_contracts import FactorOutput
from ..factor_inputs import gate_factor_inputs

def _rows(result: ProviderResult) -> list[Mapping[str, Any]]:
    data = result.data
    if isinstance(data, Mapping):
        data = data.get("rows", data.get("klines", data.get("data", [])))
    if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
        return []
    return [row for row in data if isinstance(row, Mapping)]

def _number(row: Mapping[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None

def _output(name: str, symbol: str, decision_time: str, result: ProviderResult, value: float | None, lookback: int, count: int, method: str) -> FactorOutput:
    gate = gate_factor_inputs((result,), decision_time)
    return FactorOutput(name=name, symbol=symbol, value=value if gate.ready else None, decision_time=decision_time, input_quality=gate.quality, provenance=(result.source, result.fetched_at, result.available_time or ""), metadata={"lookback": lookback, "observation_count": count, "method": method})

def momentum_factor(result: ProviderResult, *, symbol: str, decision_time: str, lookback: int = 20) -> FactorOutput:
    rows = _rows(result)
    closes = [x for x in (_number(r, "close", "Close") for r in rows) if x is not None]
    value = closes[-1] / closes[-lookback - 1] - 1.0 if len(closes) >= lookback + 1 and closes[-lookback - 1] > 0 else None
    return _output("momentum", symbol, decision_time, result, value, lookback, len(closes), "close_return")

def volatility_factor(result: ProviderResult, *, symbol: str, decision_time: str, lookback: int = 20) -> FactorOutput:
    rows = _rows(result)
    closes = [x for x in (_number(r, "close", "Close") for r in rows) if x is not None and x > 0]
    returns = [log(b / a) for a, b in zip(closes, closes[1:])]
    value = pstdev(returns[-lookback:]) * sqrt(252) if len(returns) >= lookback and lookback > 1 else None
    return _output("volatility", symbol, decision_time, result, value, lookback, len(returns), "annualized_log_return_std")

def trend_factor(result: ProviderResult, *, symbol: str, decision_time: str, lookback: int = 20) -> FactorOutput:
    rows = _rows(result)
    closes = [x for x in (_number(r, "close", "Close") for r in rows) if x is not None]
    baseline = mean(closes[-lookback:]) if len(closes) >= lookback else None
    value = closes[-1] / baseline - 1.0 if baseline else None
    return _output("trend", symbol, decision_time, result, value, lookback, len(closes), "close_vs_sma")

def volume_ratio_factor(result: ProviderResult, *, symbol: str, decision_time: str, lookback: int = 20) -> FactorOutput:
    rows = _rows(result)
    volumes = [x for x in (_number(r, "volume", "Volume", "vol") for r in rows) if x is not None]
    value = None
    if len(volumes) >= lookback + 1:
        baseline = mean(volumes[-lookback - 1:-1])
        value = volumes[-1] / baseline - 1.0 if baseline > 0 else None
    return _output("volume_ratio", symbol, decision_time, result, value, lookback, len(volumes), "volume_vs_prior_sma")

FACTOR_REGISTRY: dict[str, Callable[..., FactorOutput]] = {
    "momentum": momentum_factor,
    "volatility": volatility_factor,
    "trend": trend_factor,
    "volume_ratio": volume_ratio_factor,
}

def compute_factor(name: str, result: ProviderResult, *, symbol: str, decision_time: str, lookback: int = 20) -> FactorOutput:
    if name not in FACTOR_REGISTRY:
        raise ValueError(f"unknown factor: {name}")
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    return FACTOR_REGISTRY[name](result, symbol=symbol, decision_time=decision_time, lookback=lookback)

def winsorize(values: Sequence[float], lower: float = 0.05, upper: float = 0.95) -> list[float]:
    if not values:
        return []
    if not 0 <= lower <= upper <= 1:
        raise ValueError("invalid winsorization bounds")
    ordered = sorted(float(x) for x in values)
    def quantile(q: float) -> float:
        pos = (len(ordered) - 1) * q
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        weight = pos - lo
        return ordered[lo] * (1 - weight) + ordered[hi] * weight
    lo, hi = quantile(lower), quantile(upper)
    return [min(max(float(x), lo), hi) for x in values]

def zscore(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    avg = mean(values)
    sd = pstdev(values)
    return [0.0 for _ in values] if sd == 0 else [(float(x) - avg) / sd for x in values]

def pearson_correlation(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("correlation requires equal non-empty series")
    lx, rx = zscore(left), zscore(right)
    if all(x == 0 for x in lx) or all(x == 0 for x in rx):
        return 0.0
    return sum(a * b for a, b in zip(lx, rx)) / len(lx)

def normalize_factor_history(values: Sequence[float], *, lower: float = 0.05, upper: float = 0.95) -> list[float]:
    return zscore(winsorize(values, lower=lower, upper=upper))

def decorrelate_factor_histories(histories: Mapping[str, Sequence[float]], *, threshold: float = 0.90) -> tuple[str, ...]:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    selected: list[str] = []
    for name, values in histories.items():
        if not values:
            continue
        if all(abs(pearson_correlation(values, histories[other])) < threshold for other in selected):
            selected.append(name)
    return tuple(selected)
