"""Export historical industry membership for selected stocks via Tushare.

Requires TUSHARE_TOKEN in the environment. The project uses a conservative PIT
convention: a membership becomes admissible at 16:00 on its effective date.
This is a safety convention, not the vendor publication timestamp.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", action="append", required=True)
    p.add_argument("--output", default="data/industry/tushare_sw_membership.csv")
    p.add_argument("--level", choices=["l1", "l2", "l3"], default="l1")
    return p.parse_args()


def main():
    args = parse_args()
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN is required; do not commit it to the repository.")

    import tushare as ts

    pro = ts.pro_api(token)
    frames = []
    level_cols = {
        "l1": ("l1_code", "l1_name"),
        "l2": ("l2_code", "l2_name"),
        "l3": ("l3_code", "l3_name"),
    }
    code_col, name_col = level_cols[args.level]

    for symbol in args.symbol:
        ts_code = f"{symbol}.{'SH' if symbol.startswith('6') else 'SZ'}"
        df = pro.index_member_all(ts_code=ts_code)
        if df is None or df.empty:
            print(f"{symbol}: no membership rows")
            continue

        cols = [code_col, name_col, "ts_code", "name", "in_date", "out_date"]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise RuntimeError(f"{symbol}: missing columns {missing}")

        part = df[cols].copy()
        part["symbol"] = symbol
        part["level"] = args.level
        part["source"] = "tushare"
        part["source_type"] = "vendor_effective_date"
        part["industry_code"] = part[code_col].astype(str)
        part["industry_name"] = part[name_col].astype(str)
        part["effective_from"] = pd.to_datetime(part["in_date"], format="%Y%m%d")
        part["effective_to"] = pd.to_datetime(part["out_date"].replace("", pd.NA), format="%Y%m%d", errors="coerce")
        part["available_time"] = part["effective_from"].dt.strftime("%Y-%m-%d") + "T16:00:00+08:00"
        part["raw_ref"] = "tushare:index_member_all:" + part["ts_code"].astype(str) + ":" + part["industry_code"].astype(str)
        frames.append(part[[
            "symbol", "industry_code", "industry_name", "level",
            "effective_from", "effective_to", "available_time",
            "source", "source_type", "raw_ref"
        ]])
        print(f"{symbol}: {len(part)} rows")

    if not frames:
        raise SystemExit("No industry membership data returned.")

    out = pd.concat(frames, ignore_index=True)
    out["effective_from"] = pd.to_datetime(out["effective_from"]).dt.strftime("%Y-%m-%dT00:00:00+08:00")
    out["effective_to"] = pd.to_datetime(out["effective_to"], errors="coerce").dt.strftime("%Y-%m-%dT00:00:00+08:00")
    out = out.sort_values(["symbol", "effective_from", "industry_code"])
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"stored {len(out)} rows -> {args.output}")


if __name__ == "__main__":
    main()
