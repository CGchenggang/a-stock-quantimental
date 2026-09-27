"""V2 CLI entrypoint with explicit legacy compatibility boundary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .backtest.engine import evaluate_signals
from .orchestration import collect_legacy_outputs


def _init_workspace() -> None:
    for path in (
        "data/raw",
        "data/cache",
        "data/pit",
        "workspace/runs",
        "workspace/models",
        "workspace/reports",
    ):
        Path(path).mkdir(parents=True, exist_ok=True)
    print("initialized")


def _demo(symbol: str) -> None:
    print({
        "symbol": symbol,
        "status": "research-packet-scaffold-ready",
        "migration_boundary": "v2",
        "legacy_fallback": "available",
    })


def _backtest(csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    print(evaluate_signals(df))


def _load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError("legacy snapshot JSON must contain an object")
    return value


def _legacy_snapshot(morning_path: str | None, pre_market_path: str | None) -> None:
    morning = _load_json(morning_path) if morning_path else None
    pre_market = _load_json(pre_market_path) if pre_market_path else None
    result = collect_legacy_outputs(morning=morning, pre_market=pre_market)
    print(json.dumps(result, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser("astock-v2")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    demo = sub.add_parser("demo")
    demo.add_argument("symbol")

    backtest = sub.add_parser("backtest")
    backtest.add_argument("--csv", required=True)

    legacy = sub.add_parser(
        "legacy-snapshot",
        help="normalize existing V1 morning/pre-market JSON without treating it as realtime",
    )
    legacy.add_argument("--morning", default=None)
    legacy.add_argument("--pre-market", dest="pre_market", default=None)

    args = parser.parse_args()
    if args.cmd == "init":
        _init_workspace()
    elif args.cmd == "demo":
        _demo(args.symbol)
    elif args.cmd == "backtest":
        _backtest(args.csv)
    elif args.cmd == "legacy-snapshot":
        _legacy_snapshot(args.morning, args.pre_market)


if __name__ == "__main__":
    main()
