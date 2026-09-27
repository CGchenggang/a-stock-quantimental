"""Import historical SW industry membership from AKShare or a local official SW XLS.

The local XLS path is useful when the official SWResearch download is reachable
in a browser but not from Python due to local TLS/proxy differences.

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
        "--input",
        help="Local official SW history XLS, e.g. data/industry/StockClassifyUse_stock.xls",
    )
    p.add_argument(
        "--output", default="data/industry/sw_official_sw1_membership.csv"
    )
    p.add_argument(
        "--raw-output",
        default="data/industry/sw_official_industry_history_raw.csv",
    )
    return p.parse_args()


def _normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "start_date", "industry_code", "update_time"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"SW history missing columns: {missing}")

    out = df.copy()
    out["symbol"] = out["symbol"].astype("string").str.strip().str.zfill(6)
    out["industry_code"] = (
        out["industry_code"].astype("string").str.strip().str.zfill(6)
    )
    out["start_date"] = pd.to_datetime(out["start_date"], errors="coerce")
    out["update_time"] = pd.to_datetime(out["update_time"], errors="coerce")
    out = out[out["start_date"].notna() & out["industry_code"].notna()].copy()
    return out


def _load_history(input_path: Path | None) -> tuple[pd.DataFrame, str, str]:
    if input_path is not None:
        if not input_path.exists():
            raise FileNotFoundError(f"SW history XLS not found: {input_path}")
        df = pd.read_excel(
            input_path,
            dtype={"股票代码": "string", "行业代码": "string"},
        )
        rename = {
            "股票代码": "symbol",
            "计入日期": "start_date",
            "行业代码": "industry_code",
            "更新日期": "update_time",
        }
        missing = sorted(set(rename) - set(df.columns))
        if missing:
            raise RuntimeError(f"Local SW XLS missing columns: {missing}")
        return (
            _normalize_history(df.rename(columns=rename)),
            "official_sw_xls",
            f"local_xls:{input_path.as_posix()}",
        )

    import akshare as ak

    df = ak.stock_industry_clf_hist_sw()
    if df is None or df.empty:
        raise RuntimeError("AKShare returned no SW industry history.")

    return (
        _normalize_history(df),
        "akshare_sw",
        "akshare_stock_industry_clf_hist_sw",
    )


def _build_intervals(
    df: pd.DataFrame,
    source: str = "test",
    source_type: str = "test",
) -> pd.DataFrame:
    columns = [
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
    if df.empty:
        return pd.DataFrame(columns=columns)

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
    # The historical source supplies codes but no stable historical Chinese
    # L1-name field. Keep the code as the normalized name to avoid joining a
    # potentially mismatched current-name table.
    grouped["industry_name"] = grouped["industry_code"]
    grouped["level"] = "l1"
    grouped["source"] = source
    grouped["source_type"] = source_type
    grouped["raw_ref"] = (
        source_type
        + ":"
        + grouped["symbol"].astype(str)
        + ":"
        + grouped["start_date"].dt.strftime("%Y-%m-%d")
    )

    return grouped[columns]


def main():
    args = parse_args()
    history, source, source_type = _load_history(
        Path(args.input) if args.input else None
    )

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
    membership_out = _build_intervals(raw_out, source, source_type)

    out_path = Path(args.output)
    raw_path = Path(args.raw_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    raw_out.to_csv(raw_path, index=False, encoding="utf-8-sig")
    membership_out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"symbols: {sorted(requested)}")
    print(f"source: {source}")
    print(f"raw rows: {len(raw_out)} -> {raw_path}")
    print(f"membership rows: {len(membership_out)} -> {out_path}")
    print("coverage_start:")
    for symbol, group in membership_out.groupby("symbol"):
        print(f"  {symbol}: {group['effective_from'].min()}")


if __name__ == "__main__":
    main()
