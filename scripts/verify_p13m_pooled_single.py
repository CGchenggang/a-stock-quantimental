"""Verify that pooled P13-M context maps equal independent single-stock builds.

Reads a context JSON dumped by run_local_industry_relative_oos.py --context-out,
rebuilds each requested symbol's context with the independent single-stock
builder, and requires exact equality of decision times and factor values.
Exit code 0 means pooled == single for every symbol checked.
"""
from __future__ import annotations

import argparse
import json

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.industry_relative import build_stock_industry_relative_context_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True,
                        help="Context JSON dumped by run_local_industry_relative_oos.py.")
    parser.add_argument("--universe-file", required=True)
    parser.add_argument("--membership", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("--symbol", action="append", required=True)
    args = parser.parse_args()

    universe = tuple(
        line.strip().zfill(6)
        for line in open(args.universe_file, encoding="utf-8-sig")
        if line.strip() and not line.lstrip().startswith("#")
    )
    with open(args.context, encoding="utf-8") as f:
        pooled_maps = json.load(f)

    store = LocalHistoricalStore(args.root)
    failures = []
    checked = 0
    for symbol in args.symbol:
        symbol = symbol.strip().lstrip("\ufeff").zfill(6)
        single = build_stock_industry_relative_context_map(
            store, args.membership, symbol, universe, lookback=20
        )
        pooled = pooled_maps.get(symbol, {})
        checked += 1
        if pooled.keys() != single.keys():
            only_single = sorted(set(single) - set(pooled))[:3]
            only_pooled = sorted(set(pooled) - set(single))[:3]
            failures.append(
                f"{symbol}: decision_time keys differ "
                f"(pooled={len(pooled)}, single={len(single)}, "
                f"only_single={only_single}, only_pooled={only_pooled})"
            )
            continue
        mismatched = [
            decision_time
            for decision_time in single
            if pooled[decision_time] != single[decision_time]
        ]
        if mismatched:
            first = mismatched[0]
            failures.append(
                f"{symbol}: {len(mismatched)} factor rows differ; "
                f"first={first} pooled={pooled[first]} single={single[first]}"
            )
        else:
            print(f"OK {symbol} decision_days={len(single)} pooled==single")

    if failures:
        for line in failures:
            print(f"MISMATCH {line}")
        raise SystemExit(1)
    print(f"pooled_single_check=PASS symbols={checked}")


if __name__ == "__main__":
    main()
