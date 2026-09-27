"""Import historical SW1 membership from Tushare.

Optional fallback for symbols whose CNINFO history does not expose SW
membership. Tushare's index_member_all provides historical 申万 L1/L2/L3
membership with in_date/out_date.

PIT convention:
- effective_from: in_date 00:00 +08:00
- effective_to: out_date 00:00 +08:00
- available_time: in_date + 1 calendar day at 16:00 +08:00

The availability timestamp is deliberately conservative. Tushare does not
provide the original publication timestamp for each historical membership
record, so this is a project safety convention rather than a claim about the
actual publication time.

Never commit TUSHARE_TOKEN or generated data files.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", action="append", required=True)
    p.add_argument("--output", default="data/industry/tushare_sw1_membership.csv")
    p.add_argument("--raw-output", default="data/industry/tushare_index_member_all_raw.csv")
    return p.parse_args()


def _ts_code(symbol: str) -> str:
    symbol = symbol.strip()
    if len(symbol) != 6 or not symbol.isdigit():
        raise ValueError(f"Invalid A-share symbol: {symbol!r}")
    return f"{symbol}.{'SH' if symbol.startswith('6') else 'SZ'}"


def _build_intervals(df: pd.DataFrame) -> pd.DataFrame:
    # index_member_all repeats L1 membership for L2/L3 rows. Collapse to
    # unique L1 intervals and reject conflicting L1 classifications.
    grouped = (
        df.groupby(["symbol", "in_date", "out_date"], dropna=False, as_index=False)
        .agg(
            l1_code=("l1_code", lambda s: sorted(set(str(x) for x in s if pd.notna(x)))),
            l1_name=("l1_name", lambda s: sorted(set(str(x) for x in s if pd.notna(x)))),
        )
    )

    conflicts = grouped[
        grouped["l1_code"].map(len).gt(1) | grouped["l1_name"].map(len).gt(1)
    ]
    if not conflicts.empty:
        raise RuntimeError(
            "Conflicting Tushare SW1 memberships on the same effective interval: "
            + conflicts.to_dict("records").__repr__()
        )

    grouped["l1_code"] = grouped["l1_code"].map(lambda x: x[0])
    grouped["l1_name"] = grouped["l1_name"].map(lambda x: x[0])
    grouped = grouped.sort_values(["symbol", "in_date", "out_date"], na_position="last")

    grouped["effective_from"] = (
        grouped["in_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"
    )
    grouped["effective_to"] = grouped["out_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"

    available_date = grouped["in_date"] + pd.Timedelta(days=1)
    grouped["available_time"] = (
        available_date.dt.strftime("%Y-%m-%d") + "T16:00:00+08:00"
    )
    grouped["industry_code"] = "SW1:" + grouped["l1_name"]
    grouped["level"] = "l1"
    grouped["source"] = "tushare"
    grouped["source_type"] = "tushare_index_member_all_conservative_availability"
    grouped["raw_ref"] = (
        "tushare:index_member_all:" + grouped["symbol"].astype(str)
        + ":" + grouped["in_date"].dt.strftime("%Y-%m-%d")
    )

    return grouped[
        [
            "symbol", "industry_code", "l1_name", "level", "effective_from",
            "effective_to", "available_time", "source", "source_type", "raw_ref",
        ]
    ].rename(columns={"l1_name": "industry_name"})


def _load_symbol(pro, symbol: str) -> pd.DataFrame:
    ts_code = _ts_code(symbol)
    df = pro.index_member_all(ts_code=ts_code, is_new="N")
    if df is None or df.empty:
        return pd.DataFrame()

    required = [
        "l1_code", "l1_name", "l2_code", "l2_name", "l3_code", "l3_name",
        "ts_code", "name", "in_date", "out_date", "is_new",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"{symbol}: missing Tushare columns {missing}")

    df = df.copy()
    df["symbol"] = symbol
    df["in_date"] = pd.to_datetime(df["in_date"], format="%Y%m%d", errors="coerce")
    df["out_date"] = pd.to_datetime(
        df["out_date"].replace("", pd.NA), format="%Y%m%d", errors="coerce"
    )
    df["l1_name"] = df["l1_name"].astype("string").str.strip()
    df["l1_code"] = df["l1_code"].astype("string").str.strip()
    df = df[
        df["in_date"].notna()
        & df["l1_name"].notna()
        & (df["l1_name"] != "")
    ].copy()
    return df


def main():
    args = parse_args()
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "TUSHARE_TOKEN is required for this optional fallback; "
            "do not commit it to the repository."
        )

    try:
        import tushare as ts
    except ImportError as exc:
        raise SystemExit(
            "The optional 'tushare' package is not installed in the active environment."
        ) from exc

    pro = ts.pro_api(token)
    raw_frames = []
    membership_frames = []

    for symbol in args.symbol:
        raw = _load_symbol(pro, symbol)
        if raw.empty:
            print(f"{symbol}: no historical SW membership rows")
            continue

        raw_frames.append(raw)
        membership_frames.append(_build_intervals(raw))
        print(f"{symbol}: {len(raw)} raw Tushare SW membership rows")

    if not membership_frames:
        raise SystemExit("No Tushare SW1 membership data returned.")

    raw_out = pd.concat(raw_frames, ignore_index=True)
    membership_out = pd.concat(membership_frames, ignore_index=True)

    out_path = Path(args.output)
    raw_path = Path(args.raw_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    raw_out.to_csv(raw_path, index=False, encoding="utf-8-sig")
    membership_out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"raw rows: {len(raw_out)} -> {raw_path}")
    print(f"membership rows: {len(membership_out)} -> {out_path}")


if __name__ == "__main__":
    main()
