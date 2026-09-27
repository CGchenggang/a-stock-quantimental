"""Strict OOS label-horizon experiment on local 300308 data.

The factor inputs remain the existing four 20-day factors. Only the label
horizon changes to test whether the current next-day target is mismatched to
the factor information horizon.

For horizon h, label(t)=1 when close[t+h] > close[t]. The walk-forward gap
is set to h trading observations so training labels cannot overlap the test
period. This is a research experiment, not a production model.
"""
from __future__ import annotations

from math import exp, log
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.validation import walk_forward_windows

FACTORS = ("momentum", "volatility", "trend", "volume_ratio")
TRAIN_SIZE, TEST_SIZE, STEP = 252, 20, 20
HORIZONS = (1, 5, 10)


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


def build_horizon_rows(base_rows, horizon):
    closes = [None] * len(base_rows)
    # source_event_time is aligned with the factor observation date.
    # Recover next-horizon close from the already available next_return chain
    # is not sufficient for h>1, so this experiment is built from raw records
    # below instead.
    raise RuntimeError("unused helper")


def metrics(probabilities, labels):
    eps = 1e-15
    accuracy = sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, labels)) / len(labels)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)
    logloss = -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(probabilities, labels)
    ) / len(labels)
    return accuracy, brier, logloss


def main():
    store = LocalHistoricalStore("data")
    base = build_local_factor_rows(
        store, "300308", factor_names=FACTORS, lookback=20
    )
    records = store.read_records("cn_stock_daily", "300308")
    ordered = sorted(records, key=lambda r: (r.event_time, r.revision))
    event_times = sorted({r.event_time for r in ordered})
    by_event = {}
    for record in ordered:
        by_event.setdefault(record.event_time, []).append(record)

    # Build the same PIT-safe factor values as local_pipeline, but attach
    # future labels at each requested trading horizon.
    factor_by_event = {row.source_event_time: row for row in base}
    horizons = {}
    for horizon in HORIZONS:
        rows = []
        for i, event_time in enumerate(event_times):
            row = factor_by_event.get(event_time)
            target_i = i + horizon
            if row is None or target_i >= len(event_times):
                continue
            current = max(by_event[event_time], key=lambda r: r.revision)
            target = max(by_event[event_times[target_i]], key=lambda r: r.revision)
            current_close = float(current.value["close"])
            target_close = float(target.value["close"])
            if current_close <= 0:
                continue
            label = int(target_close / current_close - 1.0 > 0)
            rows.append((row, label))
        horizons[horizon] = rows

    print(f"base factor rows: {len(base)}")
    print()
    print("horizon,walk_forward_gap,oos_predictions,positive_rate,accuracy,brier,log_loss")

    for horizon in HORIZONS:
        pairs = horizons[horizon]
        rows = [x[0] for x in pairs]
        labels = [x[1] for x in pairs]
        windows = walk_forward_windows(
            rows,
            train_size=TRAIN_SIZE,
            test_size=TEST_SIZE,
            step=STEP,
            gap=horizon,
        )
        predictions = []
        for window in windows:
            train_rows = rows[window.train_start:window.train_end]
            test_rows = rows[window.test_start:window.test_end]
            train_y = labels[window.train_start:window.train_end]
            test_y = labels[window.test_start:window.test_end]
            train_x = [[float(r.factors[name]) for name in FACTORS] for r in train_rows]
            test_x = [[float(r.factors[name]) for name in FACTORS] for r in test_rows]
            predictions.extend(zip(fit_predict(train_x, train_y, test_x), test_y))

        ps = [p for p, _ in predictions]
        ys = [y for _, y in predictions]
        a, b, ll = metrics(ps, ys)
        rate = sum(ys) / len(ys) if ys else float("nan")
        print(
            f"{horizon},{horizon},{len(ys)},{rate:.6f},"
            f"{a:.6f},{b:.6f},{ll:.6f}"
        )


if __name__ == "__main__":
    main()
