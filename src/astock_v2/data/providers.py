from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

@dataclass(frozen=True)
class ProviderResult:
    data: Any
    source: str
    source_type: str
    fetched_at: str
    available_time: str | None = None
    latency_ms: float | None = None
    fallback: bool = False
    warnings: list[str] = field(default_factory=list)

def normalize_time(value: str) -> str:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Canonical UTC: PIT comparisons compare ISO strings, which is only sound
    # when every value carries the same offset (mixed offsets break lex order).
    return dt.astimezone(timezone.utc).isoformat()

class PitStatus(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    FUTURE = "FUTURE"
    MISSING_TIME = "MISSING_TIME"
    FALLBACK = "FALLBACK"
    INVALID_TIME = "INVALID_TIME"


def pit_status(result: ProviderResult, decision_time: str) -> PitStatus:
    """Classify a provider result relative to a decision-time PIT boundary."""
    if result.fallback:
        return PitStatus.FALLBACK
    if not result.available_time:
        return PitStatus.MISSING_TIME
    try:
        available = normalize_time(result.available_time)
        decision = normalize_time(decision_time)
    except (TypeError, ValueError):
        return PitStatus.INVALID_TIME
    return PitStatus.ADMISSIBLE if available <= decision else PitStatus.FUTURE


def pit_admissible(result: ProviderResult, decision_time: str) -> bool:
    """Return True only when the provider result is usable at decision_time."""
    return pit_status(result, decision_time) is PitStatus.ADMISSIBLE

class MarketProvider(ABC):
    name: str
    timeout_seconds: float = 10.0

    @abstractmethod
    def quote(self, symbols: list[str]) -> ProviderResult: ...

    @abstractmethod
    def daily(self, symbol: str, start: str, end: str) -> ProviderResult: ...

    def intraday(self, symbol: str, scale: int = 5, datalen: int = 20) -> ProviderResult:
        raise NotImplementedError("intraday provider is not configured")

    def index_daily(self, symbol: str) -> ProviderResult:
        raise NotImplementedError("index provider is not configured")

    def sector_board(self) -> ProviderResult:
        raise NotImplementedError("sector board provider is not configured")

    def market_turnover(self) -> ProviderResult:
        raise NotImplementedError("market turnover provider is not configured")

    def health(self) -> dict[str, Any]:
        return {"provider": self.name, "status": "UNKNOWN"}

class NullProvider(MarketProvider):
    name = "null"
    def quote(self, symbols):
        return ProviderResult({}, self.name, "fallback", "", fallback=True,
                              warnings=["No real market provider configured"])
    def daily(self, symbol, start, end):
        return ProviderResult([], self.name, "fallback", "", fallback=True,
                              warnings=["No real market provider configured"])
