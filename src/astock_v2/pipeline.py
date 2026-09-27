"""End-to-end quantitative research pipeline primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence
from .factor_contracts import FactorOutput
from .probability import LogisticProbabilityModel, fit_logistic_probability_model
from .calibration import CalibrationReport, calibration_report
from .validation import WalkForwardWindow, walk_forward_windows

@dataclass(frozen=True)
class OOSPrediction:
    test_index: int
    probability: float
    label: int

@dataclass(frozen=True)
class WalkForwardReport:
    windows: tuple[WalkForwardWindow, ...]
    predictions: tuple[OOSPrediction, ...]
    calibration: CalibrationReport | None
    models: tuple[LogisticProbabilityModel, ...]

def run_walk_forward_probability(
    rows: Sequence[Mapping[str, FactorOutput]],
    labels: Sequence[int],
    *,
    factor_names: Sequence[str],
    train_size: int,
    test_size: int,
    step: int | None = None,
    gap: int = 0,
    learning_rate: float = 0.05,
    epochs: int = 500,
) -> WalkForwardReport:
    if len(rows) != len(labels):
        raise ValueError("rows and labels must have equal length")
    windows = walk_forward_windows(
        rows,
        train_size=train_size,
        test_size=test_size,
        step=step,
        gap=gap,
    )
    predictions: list[OOSPrediction] = []
    models: list[LogisticProbabilityModel] = []
    for window in windows:
        train_labels = labels[window.train_start:window.train_end]
        model = fit_logistic_probability_model(
            window.train, train_labels,
            factor_names=factor_names,
            learning_rate=learning_rate,
            epochs=epochs,
        )
        models.append(model)
        for offset, row in enumerate(window.test):
            p=model.predict(tuple(row[name] for name in factor_names))
            predictions.append(OOSPrediction(window.test_start+offset,p,int(labels[window.test_start+offset])))
    report = calibration_report(
        [item.probability for item in predictions],
        [item.label for item in predictions],
    ) if predictions else None
    return WalkForwardReport(tuple(windows),tuple(predictions),report,tuple(models))
