"""Run PIT-safe OOS factor representation experiments on local 300308 data.

Variants:
- raw: the current four factors
- quadratic: add squared momentum/trend to capture non-monotonic effects
- standardized: fit winsorization + z-score on each training window only
- standardized_quadratic: standardized linear terms plus squared standardized
  momentum/trend terms

No future observations are used to fit scaling parameters.
"""
from __future__ import annotations

from math import exp
from statistics import mean, pstdev

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.validation import walk_forward_windows

FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
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


def winsor_bounds(values, lower=0.05, upper=0.95):
    s = sorted(values)
    def q(p):
        pos = (len(s) - 1) * p
        lo, hi = int(pos), min(int(pos) + 1, len(s) - 1)
        return s[lo] * (1 - (pos - lo)) + s[hi] * (pos - lo)
    return q(lower), q(upper)


def fit_scaler(train_x):
    bounds, params = [], []
    for j in range(len(train_x[0])):
        lo, hi = winsor_bounds([row[j] for row in train_x])
        clipped = [min(max(row[j], lo), hi) for row in train_x]
        m, s = mean(clipped), pstdev(clipped)
        bounds.append((lo, hi))
        params.append((m, s if s else 1.0))
    return bounds, params


def transform(rows, bounds, params):
    out = []
    for row in rows:
        z = []
        for j, value in enumerate(row):
            lo, hi = bounds[j]
            m, s = params[j]
            v = min(max(value, lo), hi)
            z.append((v - m) / s)
        out.append(z)
    return out


def features(rows, variant):
    base = [[float(r.factors[name]) for name in FACTORS] for r in rows]
    if variant in ("quadratic", "standardized_quadratic"):
        return [x + [x[0] ** 2, x[2] ** 2] for x in base]
    return base


def metrics(probabilities, labels):
    eps = 1e-15
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    logloss = -sum(y * __import__("math").log(max(p, eps)) + (1-y) * __import__("math").log(max(1-p, eps))
                 for p, y in zip(probabilities, labels)) / len(labels)
    return accuracy, brier, logloss


def main():
    store = LocalHistoricalStore("data")
    rows = build_local_factor_rows(store, "300308", factor_names=FACTORS, lookback=20)
    windows = walk_forward_windows(rows, train_size=TRAIN_SIZE, test_size=TEST_SIZE, step=STEP, gap=GAP)
    labels = [r.label for r in rows]
    variants = ("raw", "quadratic", "standardized", "standardized_quadratic")
    results = {v: [] for v in variants}

    for window in windows:
        train_rows = rows[window.train_start:window.train_end]
        test_rows = rows[window.test_start:window.test_end]
        train_y = labels[window.train_start:window.train_end]
        test_y = labels[window.test_start:window.test_end]

        for variant in variants:
            tx = features(train_rows, variant)
            vx = features(test_rows, variant)
            if variant.startswith("standardized"):
                bounds, params = fit_scaler(tx)
                tx, vx = transform(tx, bounds, params), transform(vx, bounds, params)
            results[variant].extend(zip(fit_predict(tx, train_y, vx), test_y))

    print(f"factor rows: {len(rows)}")
    print(f"walk-forward windows: {len(windows)}")
    print(f"walk-forward gap: {GAP} trading day (label embargo)")
    print(f"OOS predictions per model: {len(results['raw'])}")
    print()
    print("variant,accuracy,brier,log_loss")
    for variant in variants:
        ps = [p for p, _ in results[variant]]
        ys = [y for _, y in results[variant]]
        a, b, ll = metrics(ps, ys)
        print(f"{variant},{a:.6f},{b:.6f},{ll:.6f}")


if __name__ == "__main__":
    main()
