"""Download A-share daily history into the local PIT-safe store.

Example:
    python scripts/download_cn_stock_history.py --symbol 000001 \
        --start 20200101 --end 20260927 --root data

AKShare is an optional runtime dependency for this downloader.  The core
research package does not require a network client.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

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


def download_symbol(symbol: str, start: str, end: str, root: str, adjust: str = "", no_proxy: bool = False) -> int:
    try:
        import akshare as ak
    except ImportError as exc:
        raise SystemExit("AKShare is required only for the downloader; install it in the data-ingestion environment.") from exc

    previous_proxy = _clear_proxy_env() if no_proxy else None
    try:
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust=adjust,
            )
            source_name = "akshare:stock_zh_a_hist"
        except Exception as em_error:
            # Tencent is an independent A-share daily source in AKShare.
            # Use the exchange-qualified symbol expected by the Tencent endpoint.
            tx_symbol = ("sh" if symbol.startswith(("6", "68")) else "sz") + symbol
            try:
                df = ak.stock_zh_a_hist_tx(
                    symbol=tx_symbol,
                    start_date=start,
                    end_date=end,
                    adjust=adjust,
                )
                source_name = "akshare:stock_zh_a_hist_tx"
            except Exception as tx_error:
                raise RuntimeError(
                    "Both Eastmoney and Tencent historical sources failed. "
                    f"Eastmoney={type(em_error).__name__}: {em_error}; "
                    f"Tencent={type(tx_error).__name__}: {tx_error}"
                ) from tx_error
    finally:
        if previous_proxy is not None:
            _restore_proxy_env(previous_proxy)
    if df is None or df.empty:
        return 0

    # Normalize the two supported AKShare schemas into one internal schema.
    # Eastmoney returns Chinese column names; Tencent returns English names.
    if source_name == "akshare:stock_zh_a_hist":
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "股票代码": "symbol",
        }
        df = df.rename(columns=rename_map)
        if "symbol" not in df.columns:
            df["symbol"] = symbol
        required = {"date", "open", "close", "high", "low", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Eastmoney response missing columns after normalization: {sorted(missing)}"
            )
        amount_is_turnover = True
    else:
        # stock_zh_a_hist_tx returns date/open/close/high/low/amount.
        # In this Tencent interface, amount is trading volume in lots, not
        # turnover in currency. Convert lots to shares and do not fabricate
        # a monetary turnover field.
        required = {"date", "open", "close", "high", "low", "amount"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Tencent response missing columns: {sorted(missing)}"
            )
        df = df.copy()
        df["symbol"] = symbol
        df["volume"] = pd.to_numeric(df["amount"], errors="coerce") * 100.0
        df["turnover"] = None
        amount_is_turnover = False

    numeric_cols = ["open", "close", "high", "low", "volume"]
    for column in numeric_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df[numeric_cols].isna().any().any():
        bad = df.loc[df[numeric_cols].isna().any(axis=1), ["date"] + numeric_cols]
        raise ValueError(f"Historical response contains non-numeric required values: {bad.head(3).to_dict('records')}")

    # The source documents that same-day daily data should be fetched after close.
    # We model a conservative, explicit availability assumption of 16:00 Asia/Shanghai.
    availability = "16:00:00+08:00"
    records = []
    for row in df.to_dict("records"):
        date = pd.Timestamp(row["date"]).strftime("%Y-%m-%d")
        event_time = f"{date}T15:00:00+08:00"
        available_time = f"{date}T{availability}"
        records.append(HistoricalRecord(
            symbol=str(row["symbol"]).zfill(6),
            event_time=event_time,
            available_time=available_time,
            source=source_name,
            source_type="historical_vendor",
            value={
                "date": date,
                "open": float(row["开盘"]),
                "close": float(row["收盘"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "volume": float(row["volume"]),
                "amount": (float(row["amount"]) if amount_is_turnover else None),
                "adjust": adjust,
            },
            layer=DataLayer.CLEAN,
            asset_scope=AssetScope.CN_STOCK,
            quality="SOURCE_RETURNED",
        ))

    store = LocalHistoricalStore(root)
    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_payload = df.astype(object).where(pd.notna(df), None).to_dict("records")
    _, digest = store.write_raw_snapshot("cn_stock_daily", f"{symbol}-{snapshot_id}", raw_payload)
    records = [
        HistoricalRecord(
            symbol=r.symbol, event_time=r.event_time, available_time=r.available_time,
            source=r.source, source_type=r.source_type, value=r.value,
            layer=r.layer, asset_scope=r.asset_scope, revision=r.revision,
            raw_ref=digest, quality=r.quality,
        )
        for r in records
    ]
    return store.append_records("cn_stock_daily", records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--start", type=_parse_date, required=True)
    parser.add_argument("--end", type=_parse_date, required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("--adjust", choices=["", "qfq", "hfq"], default="")
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Temporarily ignore HTTP(S)/ALL proxy environment variables for the AKShare request.",
    )
    args = parser.parse_args()
    for symbol in args.symbol:
        count = download_symbol(symbol, args.start, args.end, args.root, args.adjust, args.no_proxy)
        print(f"{symbol}: stored {count} rows")


if __name__ == "__main__":
    main()
