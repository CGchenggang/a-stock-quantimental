"""Multi-stock strict OOS replication for the local A-share factor baseline.

This experiment keeps the existing four factors and 1-trading-day label.
Each symbol is evaluated independently with the same walk-forward protocol,
then OOS predictions are aggregated only for descriptive replication
statistics. It does not create a pooled production model.
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
    predictions = []
    for window in windows:
        train_rows = rows[window.train_start:window.train_end]
        test_rows = rows[window.test_start:window.test_end]
        train_y = [r.label for r in train_rows]
        test_y = [r.label for r in test_rows]
        train_x = [[float(r.factors[name]) for name in FACTORS] for r in train_rows]
        test_x = [[float(r.factors[name]) for name in FACTORS] for r in test_rows]
        predictions.extend(zip(fit_predict(train_x, train_y, test_x), test_y))

    ps = [p for p, _ in predictions]
    ys = [y for _, y in predictions]
    a, b, ll = metrics(ps, ys)
    rate = sum(ys) / len(ys) if ys else float("nan")
    baseline_a = sum((0.5 >= 0.5) == bool(y) for y in ys) / len(ys) if ys else float("nan")
    baseline_b = sum((0.5 - y) ** 2 for y in ys) / len(ys) if ys else float("nan")
    baseline_ll = -sum(
        y * log(0.5) + (1 - y) * log(0.5) for y in ys
    ) / len(ys) if ys else float("nan")
    return {
        "symbol": symbol,
        "factor_rows": len(rows),
        "windows": len(windows),
        "oos_predictions": len(ys),
        "positive_rate": rate,
        "accuracy": a,
        "brier": b,
        "log_loss": ll,
        "accuracy_delta_vs_50": a - baseline_a if ys else float("nan"),
        "brier_delta_vs_50": b - baseline_b if ys else float("nan"),
        "log_loss_delta_vs_50": ll - baseline_ll if ys else float("nan"),
        "predictions": predictions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    store = LocalHistoricalStore(args.root)
    results = [evaluate_symbol(store, symbol) for symbol in args.symbol]

    print("symbol,factor_rows,windows,oos_predictions,positive_rate,accuracy,brier,log_loss,accuracy_delta_vs_50,brier_delta_vs_50,log_loss_delta_vs_50")
    for r in results:
        print(
            f"{r['symbol']},{r['factor_rows']},{r['windows']},{r['oos_predictions']},"
            f"{r['positive_rate']:.6f},{r['accuracy']:.6f},{r['brier']:.6f},{r['log_loss']:.6f},"
            f"{r['accuracy_delta_vs_50']:.6f},{r['brier_delta_vs_50']:.6f},{r['log_loss_delta_vs_50']:.6f}"
        )

    pooled = [pair for r in results for pair in r["predictions"]]
    ps = [p for p, _ in pooled]
    ys = [y for _, y in pooled]
    a, b, ll = metrics(ps, ys)
    print()
    print(f"pooled_oos_predictions: {len(ys)}")
    print(f"pooled_positive_rate: {sum(ys) / len(ys):.6f}" if ys else "pooled_positive_rate: nan")
    print(f"pooled_accuracy: {a:.6f}")
    print(f"pooled_brier: {b:.6f}")
    print(f"pooled_log_loss: {ll:.6f}")
    print("Note: pooled metrics aggregate independent per-symbol OOS predictions; they are not a pooled-trained model.")


if __name__ == "__main__":
    main()
