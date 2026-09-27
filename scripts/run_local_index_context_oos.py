"""Strict OOS experiment: stock OHLCV factors plus common index-state variables.

Protocol is fixed before observing results:
252 train / 20 test / 20 step / 1 trading-row label embargo.
Baseline is the existing four stock factors. Market variants add:
  B: CSI 300 state
  C: ChiNext state
  D: Shanghai Composite state
  E: all three index states

The train-rate probability baseline is fitted independently inside each
walk-forward window. Index variables are PIT-filtered at the stock decision
time and are not fetched from realtime caches.
"""
from __future__ import annotations

import argparse
from math import exp, log

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.market_context import build_market_context_map
from astock_v2.validation import walk_forward_windows

STOCK_FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
INDEX_SYMBOLS = ("sh000300", "sz399006", "sh000001")
INDEX_FAMILIES = {
    "sh000300": tuple(f"sh000300_{name}" for name in ("return_5", "return_20", "close_vs_sma20", "volatility_20")),
    "sz399006": tuple(f"sz399006_{name}" for name in ("return_5", "return_20", "close_vs_sma20", "volatility_20")),
    "sh000001": tuple(f"sh000001_{name}" for name in ("return_5", "return_20", "close_vs_sma20", "volatility_20")),
}
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
        elif variant == "sh000300":
            extra = {k: context[k] for k in INDEX_FAMILIES["sh000300"]}
        elif variant == "sz399006":
            extra = {k: context[k] for k in INDEX_FAMILIES["sz399006"]}
        elif variant == "sh000001":
            extra = {k: context[k] for k in INDEX_FAMILIES["sh000001"]}
        elif variant == "all_indices":
            extra = {}
            for family in INDEX_SYMBOLS:
                extra.update({k: context[k] for k in INDEX_FAMILIES[family]})
        else:
            raise ValueError(f"unknown variant: {variant}")
        rows.append((row, {**row.factors, **extra}))

    windows = walk_forward_windows(
        rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP
    )
    predictions = []
    baselines = []

    factor_names = list(STOCK_FACTORS)
    if variant == "sh000300":
        factor_names += list(INDEX_FAMILIES["sh000300"])
    elif variant == "sz399006":
        factor_names += list(INDEX_FAMILIES["sz399006"])
    elif variant == "sh000001":
        factor_names += list(INDEX_FAMILIES["sh000001"])
    elif variant == "all_indices":
        factor_names += [k for family in INDEX_SYMBOLS for k in INDEX_FAMILIES[family]]

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
    context_map = build_market_context_map(store, INDEX_SYMBOLS, lookback=20)
    variants = ("baseline", "sh000300", "sz399006", "sh000001", "all_indices")
    results = [
        evaluate_symbol(store, symbol, context_map, variant)
        for variant in variants
        for symbol in args.symbol
    ]

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
    print("pooled_variant,pooled_oos_predictions,pooled_accuracy,pooled_brier,pooled_log_loss,"
          "pooled_baseline_accuracy,pooled_baseline_brier,pooled_baseline_log_loss,"
          "pooled_accuracy_delta,pooled_brier_delta,pooled_log_loss_delta")
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
