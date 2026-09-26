from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Postmortem:
    symbol: str
    decision_time: str
    outcome_horizon: int
    prediction: float | None
    actual_return: float | None
    causes: list[str] = field(default_factory=list)
    data_quality_flags: list[str] = field(default_factory=list)
    model_feedback: dict[str, Any] = field(default_factory=dict)

def build_postmortem(symbol, decision_time, horizon, prediction=None,
                     actual_return=None, causes=None, data_quality_flags=None,
                     model_feedback=None):
    return Postmortem(
        symbol=symbol,
        decision_time=decision_time,
        outcome_horizon=int(horizon),
        prediction=prediction,
        actual_return=actual_return,
        causes=list(causes or []),
        data_quality_flags=list(data_quality_flags or []),
        model_feedback=dict(model_feedback or {}),
    )
