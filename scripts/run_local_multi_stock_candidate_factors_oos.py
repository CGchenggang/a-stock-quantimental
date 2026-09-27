"""Strict OOS comparison of candidate OHLCV factors across local stocks.

The baseline is the existing four-factor model. Candidates are added one at a
time and as a small pre-specified pack. Every test window uses a train-rate
probability baseline fitted only on that window's training labels.
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
    logloss = -sum(y * log(max(p, eps)) + (1-y) * log(max(1-p, eps)) for p, y in zip(ps, ys)) / len(ys)
    return accuracy, brier, logloss


def factor_sets():
    return {
        "baseline": BASE,
        **{name: BASE + (name,) for name in CANDIDATES},
        "candidate_pack": BASE + CANDIDATES,
    }


def evaluate(store, symbol, factor_names):
    rows = list(build_local_factor_rows(store, symbol, factor_names=factor_names, lookback=20))
    windows = walk_forward_windows(rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP)
    model, base = [], []
    for w in windows:
        train = rows[w.train_start:w.train_end]
        test = rows[w.test_start:w.test_end]
        ty = [r.label for r in train]
        yy = [r.label for r in test]
        tx = [[float(r.factors[n]) for n in factor_names] for r in train]
        xx = [[float(r.factors[n]) for n in factor_names] for r in test]
        model.extend(zip(fit_predict(tx, ty, xx), yy))
        rate = sum(ty) / len(ty)
        base.extend(zip([rate] * len(yy), yy))
    mp, ys = zip(*model)
    bp, _ = zip(*base)
    ma, mb, ml = metrics(mp, ys)
    ba, bb, bl = metrics(bp, ys)
    return len(rows), len(windows), len(ys), (ma, mb, ml), (ba, bb, bl)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()
    store = LocalHistoricalStore(args.root)
    sets = factor_sets()
    pooled = {name: [[], []] for name in sets}
    print("model,symbol,factor_rows,windows,oos_predictions,accuracy,brier,log_loss,baseline_accuracy,baseline_brier,baseline_log_loss,accuracy_delta,brier_delta,log_loss_delta")
    for name, factor_names in sets.items():
        for symbol in args.symbol:
            rows, windows, n, model_m, base_m = evaluate(store, symbol, factor_names)
            ma, mb, ml = model_m
            ba, bb, bl = base_m
            print(f"{name},{symbol},{rows},{windows},{n},{ma:.6f},{mb:.6f},{ml:.6f},{ba:.6f},{bb:.6f},{bl:.6f},{ma-ba:.6f},{mb-bb:.6f},{ml-bl:.6f}")
            # Re-run at the same deterministic settings only for pooled summary.
            # The first evaluation above remains the per-symbol report.
            rows_data = list(build_local_factor_rows(store, symbol, factor_names=factor_names, lookback=20))
            windows_data = walk_forward_windows(rows_data, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP)
            for w in windows_data:
                train = rows_data[w.train_start:w.train_end]
                test = rows_data[w.test_start:w.test_end]
                ty = [r.label for r in train]
                yy = [r.label for r in test]
                tx = [[float(r.factors[n]) for n in factor_names] for r in train]
                xx = [[float(r.factors[n]) for n in factor_names] for r in test]
                ps = fit_predict(tx, ty, xx)
                rate = sum(ty) / len(ty)
                pooled[name][0].extend(ps)
                pooled[name][1].extend(yy)
        ps, ys = pooled[name]
        base = []
        # Pooled baseline must preserve each window's train-rate; reconstruct it
        # from the same windows rather than using pooled test labels.
        for symbol in args.symbol:
            rows_data = list(build_local_factor_rows(store, symbol, factor_names=factor_names, lookback=20))
            for w in walk_forward_windows(rows_data, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP):
                ty = [r.label for r in rows_data[w.train_start:w.train_end]]
                yy = [r.label for r in rows_data[w.test_start:w.test_end]]
                base.extend([sum(ty) / len(ty)] * len(yy))
        ma, mb, ml = metrics(ps, ys)
        ba, bb, bl = metrics(base, ys)
        print(f"POOLED,{name},-,-,{len(ys)}, {ma:.6f},{mb:.6f},{ml:.6f},{ba:.6f},{bb:.6f},{bl:.6f},{ma-ba:.6f},{mb-bb:.6f},{ml-bl:.6f}".replace(", "," ,"))
    print("Note: all models are independently trained per symbol; pooled rows aggregate independent OOS predictions.")
    print("Candidates are fixed before seeing their OOS results; this script is a diagnostic, not a production-model selector.")


if __name__ == "__main__":
    main()
