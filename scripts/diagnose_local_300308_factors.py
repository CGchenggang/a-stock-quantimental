"""Diagnose factor distributions and univariate label relationships on local 300308 data.

This is a research diagnostic, not an OOS model benchmark. It describes the
local sample so factor definitions can be improved before adding complexity.
"""
from __future__ import annotations

from math import sqrt
from statistics import mean, median, pstdev

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows

FACTORS = ("momentum", "volatility", "trend", "volume_ratio")


def corr(xs, ys):
    if len(xs) != len(ys) or not xs:
        return 0.0
    mx, my = mean(xs), mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denom = sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    return 0.0 if denom == 0 else sum(x * y for x, y in zip(dx, dy)) / denom


def describe(values):
    ordered = sorted(values)
    q = lambda p: ordered[int((len(ordered) - 1) * p)]
    return {
        "mean": mean(values),
        "median": median(values),
        "std": pstdev(values),
        "q05": q(0.05),
        "q95": q(0.95),
        "min": ordered[0],
        "max": ordered[-1],
    }


def bucket_report(values, labels, buckets=5):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = []
    for b in range(buckets):
        lo = b * len(order) // buckets
        hi = (b + 1) * len(order) // buckets
        idx = order[lo:hi]
        rate = sum(labels[i] for i in idx) / len(idx)
        out.append((b + 1, len(idx), rate))
    return out


def main():
    store = LocalHistoricalStore("data")
    rows = build_local_factor_rows(store, "300308", factor_names=FACTORS, lookback=20)
    if len(rows) < 300:
        raise SystemExit(f"Only {len(rows)} usable factor rows; at least 300 are required.")

    labels = [row.label for row in rows]
    print(f"factor rows: {len(rows)}")
    print(f"positive label rate: {mean(labels):.6f}")
    print()
    print("factor,mean,median,std,q05,q95,min,max,corr_label")
    for name in FACTORS:
        values = [row.factors[name] for row in rows]
        d = describe(values)
        print(
            f"{name},{d['mean']:.6f},{d['median']:.6f},{d['std']:.6f},"
            f"{d['q05']:.6f},{d['q95']:.6f},{d['min']:.6f},{d['max']:.6f},"
            f"{corr(values, labels):.6f}"
        )

    print()
    print("factor,bucket,count,positive_rate")
    for name in FACTORS:
        values = [row.factors[name] for row in rows]
        for bucket, count, rate in bucket_report(values, labels):
            print(f"{name},{bucket},{count},{rate:.6f}")


if __name__ == "__main__":
    main()
