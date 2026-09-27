"""Download CN index daily history into the local PIT-safe store.

Examples:
    python scripts/download_cn_index_history.py --symbol sh000300 --start 20200101 --end 20260927 --root data
    python scripts/download_cn_index_history.py --symbol sh000300 --symbol sz399006 --symbol sh000001 --start 20200101 --end 20260927 --root data

The downloader uses the same explicit post-close availability convention as
the stock downloader: event_time=15:00 and available_time=16:00 Asia/Shanghai.
This is a conservative research assumption, not a claim about the vendor's
publication timestamp.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

import pandas as pd

from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore


def _parse_date(value: str) -> str:
    datetime.strptime(value, "%Y%m%d")
    return value


def _clear_proxy_env() -> dict[str, str | None]:
    names = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    previous = {name: os.environ.get(name) for name in names}
    for name in names:
        os.environ.pop(name, None)
    return previous


def _restore_proxy_env(previous: dict[str, str | None]) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def download_symbol(
    symbol: str,
    start: str,
    end: str,
    root: str,
    no_proxy: bool = False,
) -> int:
    try:
        import akshare as ak
    except ImportError as exc:
        raise SystemExit(
            "AKShare is required only for the downloader; install it in the data-ingestion environment."
        ) from exc

    symbol = symbol.strip().lower()
    if len(symbol) != 8 or symbol[:2] not in {"sh", "sz"} or not symbol[2:].isdigit():
        raise ValueError(
            f"index symbol must be exchange-qualified, for example sh000300 or sz399006: {symbol!r}"
        )

    previous_proxy = _clear_proxy_env() if no_proxy else None
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
    except Exception as exc:
        raise RuntimeError(
            f"AKShare stock_zh_index_daily failed for {symbol}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    finally:
        if previous_proxy is not None:
            _restore_proxy_env(previous_proxy)

    if df is None or df.empty:
        return 0

    required = {"date", "open", "close", "high", "low", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Index response missing columns: {sorted(missing)}; columns={list(df.columns)}"
        )

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    start_ts = pd.Timestamp(datetime.strptime(start, "%Y%m%d"))
    end_ts = pd.Timestamp(datetime.strptime(end, "%Y%m%d"))
    df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].sort_values("date").reset_index(drop=True)
    if df.empty:
        return 0

    numeric_cols = ["open", "close", "high", "low", "volume"]
    for column in numeric_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df[numeric_cols].isna().any().any():
        bad = df.loc[df[numeric_cols].isna().any(axis=1), ["date"] + numeric_cols]
        raise ValueError(
            f"Index response contains non-numeric required values: "
            f"{bad.head(3).to_dict('records')}"
        )

    store = LocalHistoricalStore(root)
    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_payload = df.astype(object).where(pd.notna(df), None).to_dict("records")
    _, digest = store.write_raw_snapshot(
        "cn_index_daily", f"{symbol}-{snapshot_id}", raw_payload
    )

    records: list[HistoricalRecord] = []
    for row in df.to_dict("records"):
        date = pd.Timestamp(row["date"]).strftime("%Y-%m-%d")
        records.append(
            HistoricalRecord(
                symbol=symbol,
                event_time=f"{date}T15:00:00+08:00",
                available_time=f"{date}T16:00:00+08:00",
                source="akshare:stock_zh_index_daily",
                source_type="historical_vendor",
                value={
                    "date": date,
                    "open": float(row["open"]),
                    "close": float(row["close"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "volume": float(row["volume"]),
                    "amount": (
                        float(row["amount"])
                        if "amount" in row and pd.notna(row["amount"])
                        else None
                    ),
                },
                layer=DataLayer.CLEAN,
                asset_scope=AssetScope.CN_INDEX,
                quality="SOURCE_RETURNED",
                raw_ref=digest,
            )
        )

    return store.append_records("cn_index_daily", records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--start", type=_parse_date, required=True)
    parser.add_argument("--end", type=_parse_date, required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Temporarily ignore HTTP(S)/ALL proxy environment variables for the AKShare request.",
    )
    args = parser.parse_args()

    for symbol in args.symbol:
        count = download_symbol(
            symbol,
            args.start,
            args.end,
            args.root,
            args.no_proxy,
        )
        print(f"{symbol}: stored {count} rows")


if __name__ == "__main__":
    main()
