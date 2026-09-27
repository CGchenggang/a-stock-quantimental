"""Import historical SW industry membership from AKShare's native SW endpoint.

AKShare's stock_industry_clf_hist_sw reads the official申万历史个股行业分类
file and returns each stock's historical industry-code changes. This importer
normalizes those changes to PIT-safe SW level-1 intervals.

PIT convention:
- effective_from: start_date at 00:00 +08:00
- effective_to: next start_date at 00:00 +08:00
- available_time: start_date + 1 calendar day at 16:00 +08:00

The available_time is a conservative project convention because the source
file does not expose a publication timestamp.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", action="append", required=True)
    p.add_argument("--start", default="19900101")
    p.add_argument("--end", default="20991231")
    p.add_argument(
        "--output", default="data/industry/sw_official_sw1_membership.csv"
    )
    p.add_argument("--raw-output", default="data/industry/sw_official_industry_history_raw.csv")
    return p.parse_args()


def _load_history() -> pd.DataFrame:
    import akshare as ak

    df = ak.stock_industry_clf_hist_sw()
    if df is None or df.empty:
        raise RuntimeError("AKShare returned no SW industry history.")

    required = {"symbol", "start_date", "industry_code", "update_time"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"AKShare SW history missing columns: {missing}")

    out = df.copy()
    out["symbol"] = out["symbol"].astype("string").str.strip().str.zfill(6)
    out["industry_code"] = (
        out["industry_code"].astype("string").str.strip().str.zfill(6)
    )
    out["start_date"] = pd.to_datetime(out["start_date"], errors="coerce")
    out["update_time"] = pd.to_datetime(out["update_time"], errors="coerce")
    out = out[out["start_date"].notna() & out["industry_code"].notna()].copy()
    return out


def _build_intervals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "industry_code",
                "industry_name",
                "level",
                "effective_from",
                "effective_to",
                "available_time",
                "source",
                "source_type",
                "raw_ref",
            ]
        )

    work = df.copy()
    work["l1_code"] = work["industry_code"].str[:2] + "0000"

    # Multiple rows can share a start date in source revisions. For the L1
    # experiment, a single stock/date must resolve to exactly one L1 code.
    grouped = (
        work.groupby(["symbol", "start_date"], as_index=False)["l1_code"]
        .agg(lambda s: sorted(set(str(x) for x in s)))
    )
    conflicts = grouped[grouped["l1_code"].map(len) > 1]
    if not conflicts.empty:
        raise RuntimeError(
            "Conflicting SW L1 memberships on the same effective date: "
            + conflicts.to_dict("records").__repr__()
        )

    grouped["l1_code"] = grouped["l1_code"].map(lambda x: x[0])
    grouped = grouped.sort_values(["symbol", "start_date"]).reset_index(drop=True)
    grouped["next_start_date"] = grouped.groupby("symbol")["start_date"].shift(-1)

    grouped["effective_from"] = (
        grouped["start_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"
    )
    grouped["effective_to"] = (
        grouped["next_start_date"].dt.strftime("%Y-%m-%d") + "T00:00:00+08:00"
    )
    available_date = grouped["start_date"] + pd.Timedelta(days=1)
    grouped["available_time"] = (
        available_date.dt.strftime("%Y-%m-%d") + "T16:00:00+08:00"
    )

    grouped["industry_code"] = "SW1:" + grouped["l1_code"]
    # The official history endpoint supplies codes but no stable historical
    # Chinese L1-name field. Use the code as the normalized name rather than
    # joining a potentially mismatched current-name table.
    grouped["industry_name"] = grouped["industry_code"]
    grouped["level"] = "l1"
    grouped["source"] = "akshare_sw"
    grouped["source_type"] = "akshare_stock_industry_clf_hist_sw"
    grouped["raw_ref"] = (
        "akshare:stock_industry_clf_hist_sw:"
        + grouped["symbol"].astype(str)
        + ":"
        + grouped["start_date"].dt.strftime("%Y-%m-%d")
    )

    return grouped[
        [
            "symbol",
            "industry_code",
            "industry_name",
            "level",
            "effective_from",
            "effective_to",
            "available_time",
            "source",
            "source_type",
            "raw_ref",
        ]
    ]


def main():
    args = parse_args()
    history = _load_history()

    requested = {str(s).strip().zfill(6) for s in args.symbol}
    history = history[history["symbol"].isin(requested)].copy()

    if args.start:
        start = pd.to_datetime(args.start)
        history = history[history["start_date"] >= start].copy()
    if args.end:
        end = pd.to_datetime(args.end)
        history = history[history["start_date"] <= end].copy()

    if history.empty:
        raise SystemExit("No requested SW industry history returned.")

    raw_out = history.sort_values(["symbol", "start_date"]).reset_index(drop=True)
    membership_out = _build_intervals(raw_out)

    out_path = Path(args.output)
    raw_path = Path(args.raw_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    raw_out.to_csv(raw_path, index=False, encoding="utf-8-sig")
    membership_out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"symbols: {sorted(requested)}")
    print(f"raw rows: {len(raw_out)} -> {raw_path}")
    print(f"membership rows: {len(membership_out)} -> {out_path}")
    print("coverage_start:")
    for symbol, group in membership_out.groupby("symbol"):
        print(f"  {symbol}: {group['effective_from'].min()}")


if __name__ == "__main__":
    main()
