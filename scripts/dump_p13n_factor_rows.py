"""Dump one stock's PIT factor rows to JSON for P13-N equality checks.

The dump is deterministic: rows are keyed by decision_time with exact float
values, so before/after runs can be compared byte-for-byte.
"""
from __future__ import annotations

import argparse
import json

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("--out", required=True)
    parser.add_argument("--lookback", type=int, default=20)
    args = parser.parse_args()

    store = LocalHistoricalStore(args.root)
    rows = build_local_factor_rows(store, args.symbol, lookback=args.lookback)
    payload = {
        "symbol": args.symbol,
        "lookback": args.lookback,
        "factor_rows": len(rows),
        "rows": [
            {
                "decision_time": row.decision_time,
                "factors": row.factors,
                "label": row.label,
                "next_return": row.next_return,
                "source_event_time": row.source_event_time,
            }
            for row in rows
        ],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=1)
    print(f"symbol={args.symbol} factor_rows={len(rows)} out={args.out}")


if __name__ == "__main__":
    main()
