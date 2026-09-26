from dataclasses import dataclass, field
from typing import Any, Literal

Quality = Literal["A", "B", "C", "D"]

@dataclass
class DataPoint:
    symbol: str
    event_time: str
    available_time: str
    source: str
    source_type: str
    value: Any
    quality: Quality = "B"
    raw_ref: str | None = None
    revision: int = 0

@dataclass
class DecisionPacket:
    symbol: str
    decision_time: str
    model_version: str
    p_up: dict[int, float]
    expected_return: dict[int, float]
    expected_volatility: float
    expected_drawdown: float
    regime: str
    data_quality: float
    risk_flags: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)
    decision_class: str = "RESEARCH"
