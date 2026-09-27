"""Run the local 300308 factor -> walk-forward probability evaluation.

This script reads data/ locally and does not download or modify source data.
"""
from __future__ import annotations

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.data_quality import DataQualitySummary
from astock_v2.factor_contracts import FactorOutput
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.oos import evaluate_oos_predictions
from astock_v2.pipeline import run_walk_forward_probability


FACTOR_NAMES = ("momentum", "volatility", "trend", "volume_ratio")


def main() -> None:
    store = LocalHistoricalStore("data")
    local_rows = build_local_factor_rows(
        store,
        "300308",
        factor_names=FACTOR_NAMES,
        lookback=20,
    )
    if len(local_rows) < 300:
        raise SystemExit(
            f"Only {len(local_rows)} usable factor rows; at least 300 are required "
            "for the default walk-forward evaluation."
        )

    quality = DataQualitySummary(
        total=1,
        admissible=1,
        status_counts={
            "ADMISSIBLE": 1,
            "FUTURE": 0,
            "MISSING_TIME": 0,
            "FALLBACK": 0,
            "INVALID_TIME": 0,
        },
        admissible_ratio=1.0,
        pit_admissible=True,
    )

    model_rows = []
    labels = []
    for local_row in local_rows:
        factor_row = {}
        for name in FACTOR_NAMES:
            factor_row[name] = FactorOutput(
                name=name,
                symbol=local_row.symbol,
                value=float(local_row.factors[name]),
                decision_time=local_row.decision_time,
                input_quality=quality,
                provenance=("local:cn_stock_daily", local_row.source_event_time),
                metadata={"lookback": 20},
            )
        model_rows.append(factor_row)
        labels.append(local_row.label)

    report = run_walk_forward_probability(
        model_rows,
        labels,
        factor_names=FACTOR_NAMES,
        train_size=252,
        test_size=20,
        step=20,
        learning_rate=0.05,
        epochs=500,
    )
    oos = evaluate_oos_predictions(report.predictions)

    print(f"factor rows: {len(local_rows)}")
    print(f"walk-forward windows: {len(report.windows)}")
    print(f"OOS predictions: {len(report.predictions)}")
    print(f"classification accuracy: {oos.classification_accuracy}")
    print(f"Brier score: {oos.brier_score}")
    if report.calibration is not None:
        print(f"calibration bins: {len(report.calibration.bins)}")


if __name__ == "__main__":
    main()
