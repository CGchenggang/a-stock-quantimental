from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from .providers import ProviderResult

@dataclass(frozen=True)
class AdapterSpec:
    name: str
    source_type: str
    timeout_seconds: float = 10.0
    retries: int = 2

class AdapterError(RuntimeError):
    pass

class CallableAdapter:
    """Adapter wrapper that standardizes timing, retries and source metadata."""

    def __init__(self, spec: AdapterSpec, fetcher: Callable[..., Any]):
        self.spec=spec
        self.fetcher=fetcher

    def fetch(self, *args, **kwargs) -> ProviderResult:
        last=None
        for attempt in range(self.spec.retries+1):
            started=perf_counter()
            try:
                data=self.fetcher(*args, **kwargs)
                now=datetime.now(timezone.utc).isoformat()
                return ProviderResult(data,self.spec.name,self.spec.source_type,now,
                                     available_time=now,
                                     latency_ms=(perf_counter()-started)*1000,
                                     warnings=[] if attempt==0 else [f"retry_count={attempt}"])
            except Exception as exc:
                last=exc
        raise AdapterError(f"{self.spec.name} failed after retries: {last}") from last
