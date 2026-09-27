"""Import historical industry membership from CNINFO via AKShare.

This route does not require a Tushare token. AKShare exposes CNINFO's
p_stock2110 industry-change endpoint. We first filter to the SW industry
classification (008003), then construct effective intervals from successive
change dates.

PIT convention:
- effective_from: change date at 00:00 +08:00
- effective_to: next change date at 00:00 +08:00
- available_time: next calendar day at 16:00 +08:00

The available_time is deliberately conservative because CNINFO's response
does not expose a publication timestamp for each historical change row. It is
a project safety convention, not a claim about CNINFO's actual publication
time.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SW_STANDARD_CODE = "008003"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", action="append", required=True)
    p.add_argument("--start", default="20200101")
    p.add_argument("--end", default="20260927")
    p.add_argument("--output", default="data/industry/cninfo_sw1_membership.csv")
    p.add_argument("--raw-output", default="data/industry/cninfo_industry_change_raw.csv")
    return p.parse_args()


def _load_symbol(symbol: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak

    df = ak.stock_industry_change_cninfo(
        symbol=symbol, start_date=start, end_date=end
    )
    if df is None or df.empty:
        return pd.DataFrame()

    required = [
        "证券代码",
        "变更日期",
        "分类标准编码",
        "分类标准",
        "行业编码",
        "行业门类",
        "行业次类",
        "行业大类",
        "行业中类",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"{symbol}: missing CNINFO columns {missing}")

    df = df.copy()
    df = df[df["分类标准编码"].astype(str) == SW_STANDARD_CODE].copy()
    if df.empty:
        return df

    df["symbol"] = symbol
    df["change_date"] = pd.to_datetime(df["变更日期"], errors="coerce")
    df = df[df["change_date"].notna()].copy()
    df["industry_l1_name"] = df["行业门类"].astype("string").str.strip()
    df = df[df["industry_l1_name"].notna() & (df["industry_l1_name"] != "")].copy()
    return df


def _build_intervals(df: pd.DataFrame) -> pd.DataFrame:
    # The endpoint can contain multiple historical classification rows on the
    # same date. For our L1 experiment, the L1 name must be unique per date.
    grouped = (
        df.groupby(["symbol", "change_date"], as_index=False)["industry_l1_name"]
        .agg(lambda s: sorted(set(str(x) for x in s)))
    )
    conflicts = grouped[grouped["industry_l1_name"].map(len) > 1]
    if not conflicts.empty:
        raise RuntimeError(
            "Conflicting SW L1 memberships on the same effective date: "
            + conflicts.to_dict("records").__repr__()
        )

    grouped["industry_l1_name"] = grouped["industry_l1_name"].map(lambda x: x[0])
    grouped = grouped.sort_values(["symbol", "change_date"]).reset_index(drop=True)
    grouped["next_change_date"] = grouped.groupby("symbol")["change_date"].shift(-1)

    grouped["effective_from"] = (
        grouped["change_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"
    )
    grouped["effective_to"] = (
        grouped["next_change_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"
    )
    available_date = grouped["change_date"] + pd.Timedelta(days=1)
    grouped["available_time"] = (
        available_date.dt.strftime("%Y-%m-%d") + "T16:00:00+08:00"
    )
    grouped["industry_code"] = "SW1:" + grouped["industry_l1_name"]
    grouped["level"] = "l1"
    grouped["source"] = "cninfo"
    grouped["source_type"] = "cninfo_effective_date_conservative_availability"
    grouped["raw_ref"] = (
        "cninfo:p_stock2110:" + grouped["symbol"].astype(str)
        + ":" + grouped["change_date"].dt.strftime("%Y-%m-%d")
    )

    return grouped[
        [
            "symbol",
            "industry_code",
            "industry_l1_name",
            "level",
            "effective_from",
            "effective_to",
            "available_time",
            "source",
            "source_type",
            "raw_ref",
        ]
    ].rename(columns={"industry_l1_name": "industry_name"})


def main():
    args = parse_args()
    raw_frames = []
    membership_frames = []

    for symbol in args.symbol:
        raw = _load_symbol(symbol, args.start, args.end)
        if raw.empty:
            print(f"{symbol}: no SW industry-change rows")
            continue
        raw_frames.append(
            raw[
                [
                    "symbol",
                    "证券代码",
                    "变更日期",
                    "分类标准编码",
                    "分类标准",
                    "行业编码",
                    "行业门类",
                    "行业次类",
                    "行业大类",
                    "行业中类",
                ]
            ]
        )
        membership_frames.append(_build_intervals(raw))
        print(f"{symbol}: {len(raw)} SW industry-change rows")

    if not membership_frames:
        raise SystemExit("No SW industry membership data returned.")

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
