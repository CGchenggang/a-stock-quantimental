"""Strict OOS comparison of candidate OHLCV factors across local stocks.

The baseline is the existing four-factor model. Candidates are added one at a
time and as a fixed small pack. Every test window uses a train-rate probability
baseline fitted only on that window's training labels.
"""
from __future__ import annotations

import argparse
from math import exp, log

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.validation import walk_forward_windows

BASE = ("momentum", "volatility", "trend", "volume_ratio")
CANDIDATES = ("close_to_high", "close_to_low", "range_ratio", "close_location")
TRAIN_SIZE, TEST_SIZE, STEP, GAP = 252, 20, 20, 1


def sigmoid(x):
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


def metrics(ps, ys):
    eps = 1e-15
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(ps, ys)) / len(ys)
    brier = sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)
    logloss = -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(ps, ys)
    ) / len(ys)
    return accuracy, brier, logloss


def factor_sets():
    return {
        "baseline": BASE,
        **{name: BASE + (name,) for name in CANDIDATES},
        "candidate_pack": BASE + CANDIDATES,
    }


def evaluate(store, symbol, factor_names):
    rows = list(build_local_factor_rows(store, symbol, factor_names=factor_names, lookback=20))
    windows = walk_forward_windows(
        rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP
    )
    model_pairs, baseline_pairs = [], []
    for window in windows:
        train = rows[window.train_start:window.train_end]
        test = rows[window.test_start:window.test_end]
        train_y = [r.label for r in train]
        test_y = [r.label for r in test]
        train_x = [[float(r.factors[name]) for name in factor_names] for r in train]
        test_x = [[float(r.factors[name]) for name in factor_names] for r in test]
        model_pairs.extend(zip(fit_predict(train_x, train_y, test_x), test_y))
        train_rate = sum(train_y) / len(train_y)
        baseline_pairs.extend(zip([train_rate] * len(test_y), test_y))

    model_ps = [p for p, _ in model_pairs]
    labels = [y for _, y in model_pairs]
    baseline_ps = [p for p, _ in baseline_pairs]
    return len(rows), len(windows), model_ps, labels, baseline_ps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    store = LocalHistoricalStore(args.root)
    sets = factor_sets()
    pooled = {}

    print(
        "model,symbol,factor_rows,windows,oos_predictions,accuracy,brier,log_loss,"
        "baseline_accuracy,baseline_brier,baseline_log_loss,"
        "accuracy_delta,brier_delta,log_loss_delta"
    )

    for name, factor_names in sets.items():
        pooled_model, pooled_y, pooled_base = [], [], []
        for symbol in args.symbol:
            rows, windows, model_ps, labels, baseline_ps = evaluate(
                store, symbol, factor_names
            )
            ma, mb, ml = metrics(model_ps, labels)
            ba, bb, bl = metrics(baseline_ps, labels)
            print(
                f"{name},{symbol},{rows},{windows},{len(labels)},"
                f"{ma:.6f},{mb:.6f},{ml:.6f},"
                f"{ba:.6f},{bb:.6f},{bl:.6f},"
                f"{ma-ba:.6f},{mb-bb:.6f},{ml-bl:.6f}"
            )
            pooled_model.extend(model_ps)
            pooled_y.extend(labels)
            pooled_base.extend(baseline_ps)

        ma, mb, ml = metrics(pooled_model, pooled_y)
        ba, bb, bl = metrics(pooled_base, pooled_y)
        print(
            f"POOLED,{name},-,-,{len(pooled_y)},"
            f"{ma:.6f},{mb:.6f},{ml:.6f},"
            f"{ba:.6f},{bb:.6f},{bl:.6f},"
            f"{ma-ba:.6f},{mb-bb:.6f},{ml-bl:.6f}"
        )

    print(
        "Note: all models are independently trained per symbol; pooled rows aggregate "
        "independent OOS predictions."
    )
    print(
        "Candidates were fixed before inspecting their OOS results; this is a diagnostic "
        "experiment, not a production-model selector."
    )


if __name__ == "__main__":
    main()
