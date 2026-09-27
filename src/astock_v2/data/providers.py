from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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

class MarketProvider(ABC):
    name: str
    timeout_seconds: float = 10.0

    @abstractmethod
    def quote(self, symbols: list[str]) -> ProviderResult: ...

    @abstractmethod
    def daily(self, symbol: str, start: str, end: str) -> ProviderResult: ...

    def intraday(self, symbol: str, scale: int = 5, datalen: int = 20) -> ProviderResult:
        raise NotImplementedError("intraday provider is not configured")

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
