"""Contracts for P2 factor outputs.

The contract carries provenance and PIT quality with every factor value so
downstream probability/risk stages can reject incomplete quantitative inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .data_quality import DataQualitySummary


@dataclass(frozen=True)
class FactorOutput:
    name: str
    symbol: str
    value: float | None
    decision_time: str
    input_quality: DataQualitySummary
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, Any] | None = None

    @property
    def admissible(self) -> bool:
        return self.value is not None and self.input_quality.pit_admissible

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "value": self.value,
            "decision_time": self.decision_time,
            "admissible": self.admissible,
            "provenance": list(self.provenance),
            "metadata": dict(self.metadata or {}),
            "data_quality": self.input_quality.as_dict(),
        }


def factor_output_ready(output: FactorOutput) -> bool:
    """Single downstream gate for quantitative consumers."""
    return output.admissible
