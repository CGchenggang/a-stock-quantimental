"""Admission gate for factor outputs entering probability models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .factor_contracts import FactorOutput


@dataclass(frozen=True)
class ProbabilityInputGate:
    admitted: tuple[FactorOutput, ...]
    rejected: tuple[FactorOutput, ...]
    ready: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "admitted": [item.name for item in self.admitted],
            "rejected": [item.name for item in self.rejected],
        }


def gate_probability_inputs(
    factors: Iterable[FactorOutput],
    *,
    required_names: Iterable[str] = (),
) -> ProbabilityInputGate:
    """Admit only PIT-safe, valued factors and require named factors when given."""
    items = tuple(factors)
    admitted = tuple(item for item in items if item.admissible)
    rejected = tuple(item for item in items if not item.admissible)
    names = {item.name for item in admitted}
    required = set(required_names)
    ready = not rejected and required.issubset(names) and bool(admitted)
    return ProbabilityInputGate(admitted=admitted, rejected=rejected, ready=ready)
