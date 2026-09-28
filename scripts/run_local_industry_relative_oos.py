"""Strict OOS experiment for PIT-safe stock-relative-to-SW1-industry returns.

Variants are evaluated on the same rows for each stock:
  baseline
  baseline + industry_relative_return_5
  baseline + industry_relative_return_20
  baseline + both industry-relative returns

Protocol: 252 train / 20 test / 20 step / 1 trading-row gap.
The industry benchmark is reconstructed from the supplied local universe;
membership is evaluated at each decision boundary using the PIT-safe
historical membership file.
"""
from __future__ import annotations

import argparse
from math import log

import numpy as np

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.industry_relative import (
    build_stock_industry_relative_context_map,
    build_universe_industry_relative_context_maps,
)
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.validation import walk_forward_windows

STOCK_FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
INDUSTRY_FACTORS = ("industry_relative_return_5", "industry_relative_return_20")
TRAIN_SIZE, TEST_SIZE, STEP, GAP = 252, 20, 20, 1


def fit_predict(train_x, train_y, test_x, epochs: int = 500, lr: float = 0.05):
    """Fit the same logistic model with vectorized NumPy gradients.

    This preserves the original unregularized 500-epoch gradient-descent
    protocol while avoiding Python-level sample/feature loops.
    """
    x_train = np.asarray(train_x, dtype=np.float64)
    y_train = np.asarray(train_y, dtype=np.float64)
    x_test = np.asarray(test_x, dtype=np.float64)
    n = float(len(x_train))
    w = np.zeros(x_train.shape[1], dtype=np.float64)
    b = 0.0

    for _ in range(epochs):
        logits = b + x_train @ w
        q = np.empty_like(logits)
        positive = logits >= 0
        q[positive] = 1.0 / (1.0 + np.exp(-logits[positive]))
        exp_logits = np.exp(logits[~positive])
        q[~positive] = exp_logits / (1.0 + exp_logits)
        error = q - y_train
        w -= lr * (x_train.T @ error) / n
        b -= lr * float(error.sum()) / n

    test_logits = b + x_test @ w
    test_q = np.empty_like(test_logits)
    positive = test_logits >= 0
    test_q[positive] = 1.0 / (1.0 + np.exp(-test_logits[positive]))
    exp_test = np.exp(test_logits[~positive])
    test_q[~positive] = exp_test / (1.0 + exp_test)
    return test_q.tolist()


def metrics(probabilities, labels):
    if not labels:
        return float("nan"), float("nan"), float("nan")
    eps = 1e-15
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    logloss = -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(probabilities, labels)
    ) / len(labels)
    return accuracy, brier, logloss


def _variants():
    return {
        "baseline": STOCK_FACTORS,
        "industry_5": STOCK_FACTORS + ("industry_relative_return_5",),
        "industry_20": STOCK_FACTORS + ("industry_relative_return_20",),
        "industry_5_20": STOCK_FACTORS + INDUSTRY_FACTORS,
    }


def _factor_rows(store, context_map, symbol):
    stock_rows = build_local_factor_rows(
        store, symbol, factor_names=STOCK_FACTORS, lookback=20
    )
    # Keep all variants on exactly the same paired sample.  A baseline row is
    # included only when the industry context exists, so variant deltas do not
    # mix different observation populations.
    rows = []
    for row in stock_rows:
        context = context_map.get(row.decision_time)
        if context is None:
            continue
        rows.append((row, {**row.factors, **context}))
    return rows


def evaluate(rows, factor_names):
    windows = walk_forward_windows(
        rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP
    )
    predictions = []
    baselines = []
    for window in windows:
        train = rows[window.train_start:window.train_end]
        test = rows[window.test_start:window.test_end]
        train_y = [item[0].label for item in train]
        test_y = [item[0].label for item in test]
        train_x = [[float(item[1][name]) for name in factor_names] for item in train]
        test_x = [[float(item[1][name]) for name in factor_names] for item in test]
        model_ps = fit_predict(train_x, train_y, test_x)
        train_rate = sum(train_y) / len(train_y)
        predictions.extend(zip(model_ps, test_y))
        baselines.extend(zip([train_rate] * len(test_y), test_y))

    ps = [p for p, _ in predictions]
    ys = [y for _, y in predictions]
    bps = [p for p, _ in baselines]
    a, b, ll = metrics(ps, ys)
    ba, bb, bll = metrics(bps, ys)
    return {
        "factor_rows": len(rows),
        "windows": len(windows),
        "oos_predictions": len(ys),
        "positive_rate": sum(ys) / len(ys) if ys else float("nan"),
        "accuracy": a,
        "brier": b,
        "log_loss": ll,
        "baseline_accuracy": ba,
        "baseline_brier": bb,
        "baseline_log_loss": bll,
        "accuracy_delta": a - ba if ys else float("nan"),
        "brier_delta": b - bb if ys else float("nan"),
        "log_loss_delta": ll - bll if ys else float("nan"),
        "predictions": predictions,
        "baselines": baselines,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--universe-file", required=True,
                        help="Text file with one six-digit stock symbol per line.")
    parser.add_argument("--membership", required=True,
                        help="PIT-safe SW1 membership CSV.")
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    universe = tuple(
        line.strip().zfill(6)
        for line in open(args.universe_file, encoding="utf-8-sig")
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not universe:
        raise SystemExit("universe file is empty")

    store = LocalHistoricalStore(args.root)
    variants = _variants()
    results = []
    requested_symbols = tuple(dict.fromkeys(args.symbol))
    if len(requested_symbols) == 1:
        # A single-stock benchmark only needs the exact target-specific context.
        # Avoid building the full pooled universe context when --symbol is used
        # once; the target-specific builder applies the same PIT semantics with
        # an exact industry-code candidate reduction.
        symbol = requested_symbols[0]
        context_map = build_stock_industry_relative_context_map(
            store, args.membership, symbol, tuple(universe), lookback=20
        )
        context_maps = {symbol: context_map}
    else:
        context_maps = build_universe_industry_relative_context_maps(
            store, args.membership, tuple(universe), lookback=20
        )

    for symbol in requested_symbols:
        rows = _factor_rows(store, context_maps.get(symbol, {}), symbol)
        for variant, factor_names in variants.items():
            result = evaluate(rows, factor_names)
            result["symbol"] = symbol
            result["variant"] = variant
            results.append(result)

    print(
        "variant,symbol,factor_rows,windows,oos_predictions,positive_rate,"
        "accuracy,brier,log_loss,baseline_accuracy,baseline_brier,baseline_log_loss,"
        "accuracy_delta,brier_delta,log_loss_delta"
    )
    for r in results:
        print(
            f"{r['variant']},{r['symbol']},{r['factor_rows']},{r['windows']},"
            f"{r['oos_predictions']},{r['positive_rate']:.6f},{r['accuracy']:.6f},"
            f"{r['brier']:.6f},{r['log_loss']:.6f},{r['baseline_accuracy']:.6f},"
            f"{r['baseline_brier']:.6f},{r['baseline_log_loss']:.6f},"
            f"{r['accuracy_delta']:.6f},{r['brier_delta']:.6f},"
            f"{r['log_loss_delta']:.6f}"
        )

    print()
    print(
        "pooled_variant,pooled_oos_predictions,pooled_accuracy,pooled_brier,"
        "pooled_log_loss,pooled_baseline_accuracy,pooled_baseline_brier,"
        "pooled_baseline_log_loss,pooled_accuracy_delta,pooled_brier_delta,"
        "pooled_log_loss_delta"
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
