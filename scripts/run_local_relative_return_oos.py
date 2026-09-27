"""Strict OOS experiment for stock-relative-to-index returns.

Protocol: 252 train / 20 test / 20 step / 1 trading-row label embargo.

Variants:
  baseline: existing four stock factors.
  sh000300: baseline + stock-minus-CSI-300 5/20-day returns.
  sz399006: baseline + stock-minus-ChiNext 5/20-day returns.
  sh000001: baseline + stock-minus-Shanghai Composite 5/20-day returns.
  all_indices: baseline + all three relative-return families.

Each variant is evaluated on the same paired sample for a stock. The
train-rate probability baseline is fitted independently inside each
walk-forward training window. All stock/index inputs are local PIT-filtered
history; no realtime cache is used.
"""
from __future__ import annotations

import argparse
from math import exp, log

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.relative_context import build_stock_relative_context_map
from astock_v2.validation import walk_forward_windows

STOCK_FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
INDEX_SYMBOLS = ("sh000300", "sz399006", "sh000001")
RELATIVE_FAMILIES = {
    symbol: tuple(f"relative_{symbol}_return_{h}" for h in (5, 20))
    for symbol in INDEX_SYMBOLS
}
TRAIN_SIZE, TEST_SIZE, STEP, GAP = 252, 20, 20, 1


def sigmoid(x: float) -> float:
    if x >= 0:
        z = exp(-x)
        return 1.0 / (1.0 + z)
    z = exp(x)
    return z / (1.0 + exp(x))


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
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    logloss = -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(probabilities, labels)
    ) / len(labels)
    return accuracy, brier, logloss


def evaluate_symbol(store, symbol, context_map, variant):
    rows = []
    for row in build_local_factor_rows(
        store, symbol, factor_names=STOCK_FACTORS, lookback=20
    ):
        context = context_map.get(row.decision_time)
        if context is None:
            continue

        if variant == "baseline":
            extra = {}
        elif variant in INDEX_SYMBOLS:
            extra = {k: context[k] for k in RELATIVE_FAMILIES[variant]}
        elif variant == "all_indices":
            extra = {
                k: context[k]
                for index_symbol in INDEX_SYMBOLS
                for k in RELATIVE_FAMILIES[index_symbol]
            }
        else:
            raise ValueError(f"unknown variant: {variant}")

        rows.append((row, {**row.factors, **extra}))

    windows = walk_forward_windows(
        rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP
    )
    predictions = []
    baselines = []

    factor_names = list(STOCK_FACTORS)
    if variant in INDEX_SYMBOLS:
        factor_names += list(RELATIVE_FAMILIES[variant])
    elif variant == "all_indices":
        factor_names += [
            k for index_symbol in INDEX_SYMBOLS for k in RELATIVE_FAMILIES[index_symbol]
        ]

    for window in windows:
        train_rows = rows[window.train_start:window.train_end]
        test_rows = rows[window.test_start:window.test_end]
        train_y = [r[0].label for r in train_rows]
        test_y = [r[0].label for r in test_rows]
        train_x = [[float(r[1][name]) for name in factor_names] for r in train_rows]
        test_x = [[float(r[1][name]) for name in factor_names] for r in test_rows]
        model_ps = fit_predict(train_x, train_y, test_x)
        train_rate = sum(train_y) / len(train_y)
        base_ps = [train_rate] * len(test_y)
        predictions.extend(zip(model_ps, test_y))
        baselines.extend(zip(base_ps, test_y))

    ps = [p for p, _ in predictions]
    ys = [y for _, y in predictions]
    bps = [p for p, _ in baselines]
    a, b, ll = metrics(ps, ys)
    ba, bb, bll = metrics(bps, ys)
    return {
        "symbol": symbol,
        "variant": variant,
        "factor_rows": len(rows),
        "windows": len(windows),
        "oos_predictions": len(ys),
        "positive_rate": sum(ys) / len(ys),
        "accuracy": a,
        "brier": b,
        "log_loss": ll,
        "baseline_accuracy": ba,
        "baseline_brier": bb,
        "baseline_log_loss": bll,
        "accuracy_delta": a - ba,
        "brier_delta": b - bb,
        "log_loss_delta": ll - bll,
        "predictions": predictions,
        "baselines": baselines,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    store = LocalHistoricalStore(args.root)
    variants = ("baseline", *INDEX_SYMBOLS, "all_indices")
    results = []

    for symbol in args.symbol:
        context_map = build_stock_relative_context_map(
            store, symbol, INDEX_SYMBOLS, lookback=20
        )
        for variant in variants:
            results.append(evaluate_symbol(store, symbol, context_map, variant))

    print(
        "variant,symbol,factor_rows,windows,oos_predictions,positive_rate,"
        "accuracy,brier,log_loss,baseline_accuracy,baseline_brier,baseline_log_loss,"
        "accuracy_delta,brier_delta,log_loss_delta"
    )
    for r in results:
        print(
            f"{r['variant']},{r['symbol']},{r['factor_rows']},{r['windows']},{r['oos_predictions']},"
            f"{r['positive_rate']:.6f},{r['accuracy']:.6f},{r['brier']:.6f},{r['log_loss']:.6f},"
            f"{r['baseline_accuracy']:.6f},{r['baseline_brier']:.6f},{r['baseline_log_loss']:.6f},"
            f"{r['accuracy_delta']:.6f},{r['brier_delta']:.6f},{r['log_loss_delta']:.6f}"
        )

    print()
    print(
        "pooled_variant,pooled_oos_predictions,pooled_accuracy,pooled_brier,pooled_log_loss,"
        "pooled_baseline_accuracy,pooled_baseline_brier,pooled_baseline_log_loss,"
        "pooled_accuracy_delta,pooled_brier_delta,pooled_log_loss_delta"
    )
    for variant in variants:
        selected = [r for r in results if r["variant"] == variant]
        pooled = [pair for r in selected for pair in r["predictions"]]
        base = [pair for r in selected for pair in r["baselines"]]
        ps = [p for p, _ in pooled]
        ys = [y for _, y in pooled]
        bps = [p for p, _ in base]
        a, b, ll = metrics(ps, ys)
        ba, bb, bll = metrics(bps, ys)
        print(
            f"{variant},{len(ys)},{a:.6f},{b:.6f},{ll:.6f},"
            f"{ba:.6f},{bb:.6f},{bll:.6f},{a-ba:.6f},{b-bb:.6f},{ll-bll:.6f}"
        )


if __name__ == "__main__":
    main()
