"""Run the strict OOS benchmark matrix on local 300308 data."""
from __future__ import annotations

from astock_v2.calibration import calibration_report
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.data_quality import DataQualitySummary
from astock_v2.factor_contracts import FactorOutput
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.pipeline import run_walk_forward_probability
from astock_v2.validation import walk_forward_windows

ALL_FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
TRAIN_SIZE = 252
TEST_SIZE = 20
STEP = 20
GAP = 1


def build_model_rows(local_rows):
    quality = DataQualitySummary(
        total=1, admissible=1,
        status_counts={"ADMISSIBLE": 1, "FUTURE": 0, "MISSING_TIME": 0, "FALLBACK": 0, "INVALID_TIME": 0},
        admissible_ratio=1.0, pit_admissible=True,
    )
    rows, labels = [], []
    for item in local_rows:
        rows.append({
            name: FactorOutput(
                name=name, symbol=item.symbol, value=float(item.factors[name]),
                decision_time=item.decision_time, input_quality=quality,
                provenance=("local:cn_stock_daily", item.source_event_time),
                metadata={"lookback": 20},
            )
            for name in ALL_FACTORS
        })
        labels.append(item.label)
    return rows, labels


def evaluate(probabilities, labels):
    report = calibration_report(probabilities, labels, bins=10)
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    return accuracy, report


def run_logistic(rows, labels, factor_names):
    report = run_walk_forward_probability(
        rows, labels, factor_names=factor_names,
        train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP,
        learning_rate=0.05, epochs=500,
    )
    probabilities = tuple(p.probability for p in report.predictions)
    oos_labels = tuple(p.label for p in report.predictions)
    accuracy, calibration = evaluate(probabilities, oos_labels)
    return {
        "name": "+".join(factor_names),
        "accuracy": accuracy,
        "brier": calibration.brier_score,
        "log_loss": calibration.log_loss,
        "bins": calibration.bins,
        "n": len(probabilities),
        "windows": len(report.windows),
    }


def run_simple_baselines(rows, labels):
    windows = walk_forward_windows(
        rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP
    )
    majority, train_rate, constant, oos_labels = [], [], [], []
    for window in windows:
        train = labels[window.train_start:window.train_end]
        rate = sum(train) / len(train)
        majority_p = 1.0 if rate >= 0.5 else 0.0
        for index in range(window.test_start, window.test_end):
            majority.append(majority_p)
            train_rate.append(rate)
            constant.append(0.5)
            oos_labels.append(labels[index])

    results = []
    for name, probabilities in (
        ("train_majority", majority),
        ("train_rate", train_rate),
        ("constant_0.50", constant),
    ):
        accuracy, calibration = evaluate(probabilities, oos_labels)
        results.append({
            "name": name, "accuracy": accuracy, "brier": calibration.brier_score,
            "log_loss": calibration.log_loss, "bins": calibration.bins,
            "n": len(oos_labels), "windows": len(windows),
        })
    return results


def main() -> None:
    store = LocalHistoricalStore("data")
    local_rows = build_local_factor_rows(store, "300308", factor_names=ALL_FACTORS, lookback=20)
    if len(local_rows) < 300:
        raise SystemExit(f"Only {len(local_rows)} usable factor rows; at least 300 are required.")

    rows, labels = build_model_rows(local_rows)
    results = run_simple_baselines(rows, labels)
    for factor in ALL_FACTORS:
        results.append(run_logistic(rows, labels, (factor,)))
    results.append(run_logistic(rows, labels, ALL_FACTORS))

    print(f"factor rows: {len(local_rows)}")
    print(f"walk-forward windows: {results[-1]['windows']}")
    print(f"walk-forward gap: {GAP} trading day (label embargo)")
    print(f"OOS predictions per model: {results[-1]['n']}")
    print()
    print("model,accuracy,brier,log_loss,calibration_bins")
    for result in results:
        print(
            f"{result['name']},{result['accuracy']:.6f},{result['brier']:.6f},"
            f"{result['log_loss']:.6f},{len(result['bins'])}"
        )

    four_factor = results[-1]
    print()
    print("four-factor calibration:")
    for item in four_factor["bins"]:
        print(
            f"bin={item['bin']} count={item['count']} "
            f"mean_p={item['mean_probability']:.4f} "
            f"observed={item['observed_rate']:.4f}"
        )


if __name__ == "__main__":
    main()
