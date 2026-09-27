"""Probability calibration diagnostics for P4/P10."""
from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Sequence


@dataclass(frozen=True)
class CalibrationReport:
    brier_score: float
    log_loss: float
    bins: tuple[dict[str, float | int], ...]


def calibration_report(
    probabilities: Sequence[float],
    labels: Sequence[int],
    *,
    bins: int = 10,
) -> CalibrationReport:
    if len(probabilities) != len(labels) or not probabilities:
        raise ValueError("probabilities and labels must have equal non-zero length")
    if bins <= 0:
        raise ValueError("bins must be positive")
    if any(not 0.0 <= float(p) <= 1.0 for p in probabilities):
        raise ValueError("probabilities must be in [0, 1]")
    if any(y not in (0, 1) for y in labels):
        raise ValueError("labels must be 0 or 1")

    brier = sum((float(p) - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    eps = 1e-15
    logloss = -sum(
        y * log(max(min(float(p), 1.0 - eps), eps))
        + (1 - y) * log(max(min(1.0 - float(p), 1.0 - eps), eps))
        for p, y in zip(probabilities, labels)
    ) / len(labels)

    groups = []
    for idx in range(bins):
        lo = idx / bins
        hi = (idx + 1) / bins
        selected = [
            (float(p), y)
            for p, y in zip(probabilities, labels)
            if (lo <= p < hi) or (idx == bins - 1 and p == hi)
        ]
        if selected:
            groups.append(
                {
                    "bin": idx,
                    "count": len(selected),
                    "mean_probability": sum(p for p, _ in selected) / len(selected),
                    "observed_rate": sum(y for _, y in selected) / len(selected),
                }
            )
    return CalibrationReport(
        brier_score=brier,
        log_loss=logloss,
        bins=tuple(groups),
    )
