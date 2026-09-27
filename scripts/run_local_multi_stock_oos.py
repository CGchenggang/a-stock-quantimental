"""Multi-stock strict OOS replication for the local A-share factor baseline.

Each symbol is evaluated independently with the same walk-forward protocol.
For every test window, the factor model is compared with a train-rate
probability baseline fitted only on that window's training labels.
"""
from __future__ import annotations

import argparse
from math import exp, log

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.validation import walk_forward_windows

FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
TRAIN_SIZE, TEST_SIZE, STEP, GAP = 252, 20, 20, 1


def sigmoid(x: float) -> float:
    if x >= 0:
        z = exp(-x)
        return 1.0 / (1.0 + z)
    z = exp(x)
    return z / (1.0 + z)


def fit_predict(train_x, train_y, test_x, epochs=500, lr=0.05):
    n = float(len(train_x))
    p = len(train_x[0])
    w, b = [0.0] * p, 0.0
    for _ in range(epochs):
        gw, gb = [0.0] * p, 0.0
        for x, y in zip(train_x, train_y):
            q = sigmoid(b + sum(a * v for a, v in zip(w, x)))
            e = q - y
            gb += e
            for j, v in enumerate(x):
                gw[j] += e * v
        b -= lr * gb / n
        w = [a - lr * g / n for a, g in zip(w, gw)]
    return [sigmoid(b + sum(a * v for a, v in zip(w, x))) for x in test_x]


def metrics(probabilities, labels):
    eps = 1e-15
    if not labels:
        return float("nan"), float("nan"), float("nan")
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    logloss = -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(probabilities, labels)
    ) / len(labels)
    return accuracy, brier, logloss


def evaluate_symbol(store, symbol):
    rows = list(build_local_factor_rows(
        store, symbol, factor_names=FACTORS, lookback=20
    ))
    windows = walk_forward_windows(
        rows,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
        step=STEP,
        gap=GAP,
    )

    model_predictions = []
    baseline_predictions = []

    for window in windows:
        train_rows = rows[window.train_start:window.train_end]
        test_rows = rows[window.test_start:window.test_end]
        train_y = [r.label for r in train_rows]
        test_y = [r.label for r in test_rows]
        train_x = [[float(r.factors[name]) for name in FACTORS] for r in train_rows]
        test_x = [[float(r.factors[name]) for name in FACTORS] for r in test_rows]

        model_ps = fit_predict(train_x, train_y, test_x)
        train_rate = sum(train_y) / len(train_y)
        baseline_ps = [train_rate] * len(test_y)

        model_predictions.extend(zip(model_ps, test_y))
        baseline_predictions.extend(zip(baseline_ps, test_y))

    model_ps = [p for p, _ in model_predictions]
    ys = [y for _, y in model_predictions]
    base_ps = [p for p, _ in baseline_predictions]

    a, b, ll = metrics(model_ps, ys)
    ba, bb, bll = metrics(base_ps, ys)
    rate = sum(ys) / len(ys) if ys else float("nan")

    return {
        "symbol": symbol,
        "factor_rows": len(rows),
        "windows": len(windows),
        "oos_predictions": len(ys),
        "positive_rate": rate,
        "accuracy": a,
        "brier": b,
        "log_loss": ll,
        "baseline_accuracy": ba,
        "baseline_brier": bb,
        "baseline_log_loss": bll,
        "accuracy_delta_vs_train_rate": a - ba if ys else float("nan"),
        "brier_delta_vs_train_rate": b - bb if ys else float("nan"),
        "log_loss_delta_vs_train_rate": ll - bll if ys else float("nan"),
        "predictions": model_predictions,
        "baseline_predictions": baseline_predictions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    store = LocalHistoricalStore(args.root)
    results = [evaluate_symbol(store, symbol) for symbol in args.symbol]

    print(
        "symbol,factor_rows,windows,oos_predictions,positive_rate,"
        "accuracy,brier,log_loss,baseline_accuracy,baseline_brier,baseline_log_loss,"
        "accuracy_delta_vs_train_rate,brier_delta_vs_train_rate,log_loss_delta_vs_train_rate"
    )
    for r in results:
        print(
            f"{r['symbol']},{r['factor_rows']},{r['windows']},{r['oos_predictions']},"
            f"{r['positive_rate']:.6f},{r['accuracy']:.6f},{r['brier']:.6f},{r['log_loss']:.6f},"
            f"{r['baseline_accuracy']:.6f},{r['baseline_brier']:.6f},{r['baseline_log_loss']:.6f},"
            f"{r['accuracy_delta_vs_train_rate']:.6f},{r['brier_delta_vs_train_rate']:.6f},"
            f"{r['log_loss_delta_vs_train_rate']:.6f}"
        )

    pooled = [pair for r in results for pair in r["predictions"]]
    pooled_base = [pair for r in results for pair in r["baseline_predictions"]]
    ps = [p for p, _ in pooled]
    ys = [y for _, y in pooled]
    base_ps = [p for p, _ in pooled_base]
    a, b, ll = metrics(ps, ys)
    ba, bb, bll = metrics(base_ps, ys)

    print()
    print(f"pooled_oos_predictions: {len(ys)}")
    print(f"pooled_positive_rate: {sum(ys) / len(ys):.6f}" if ys else "pooled_positive_rate: nan")
    print(f"pooled_accuracy: {a:.6f}")
    print(f"pooled_brier: {b:.6f}")
    print(f"pooled_log_loss: {ll:.6f}")
    print(f"pooled_train_rate_baseline_accuracy: {ba:.6f}")
    print(f"pooled_train_rate_baseline_brier: {bb:.6f}")
    print(f"pooled_train_rate_baseline_log_loss: {bll:.6f}")
    print(f"pooled_accuracy_delta_vs_train_rate: {a - ba:.6f}")
    print(f"pooled_brier_delta_vs_train_rate: {b - bb:.6f}")
    print(f"pooled_log_loss_delta_vs_train_rate: {ll - bll:.6f}")
    print("Note: pooled metrics aggregate independent per-symbol OOS predictions; they are not a pooled-trained model.")


if __name__ == "__main__":
    main()
