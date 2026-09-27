"""OOS evaluation helpers combining predictions and equity metrics."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from .metrics import PerformanceMetrics, performance_metrics
from .pipeline import OOSPrediction

@dataclass(frozen=True)
class OOSReport:
    predictions: tuple[OOSPrediction, ...]
    classification_accuracy: float | None
    brier_score: float | None
    performance: PerformanceMetrics | None

def evaluate_oos_predictions(predictions: Sequence[OOSPrediction], *, equity: Sequence[float] | None = None) -> OOSReport:
    items=tuple(predictions)
    accuracy=(sum((p.probability >= .5)==bool(p.label) for p in items)/len(items)) if items else None
    brier=(sum((p.probability-p.label)**2 for p in items)/len(items)) if items else None
    performance=performance_metrics(equity) if equity is not None else None
    return OOSReport(items,accuracy,brier,performance)
