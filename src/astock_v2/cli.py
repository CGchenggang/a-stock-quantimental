"""V2 CLI entrypoint with explicit legacy compatibility boundary."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .backtest.engine import evaluate_signals


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


def main() -> None:
    parser = argparse.ArgumentParser("astock-v2")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    demo = sub.add_parser("demo")
    demo.add_argument("symbol")

    backtest = sub.add_parser("backtest")
    backtest.add_argument("--csv", required=True)

    args = parser.parse_args()
    if args.cmd == "init":
        _init_workspace()
    elif args.cmd == "demo":
        _demo(args.symbol)
    elif args.cmd == "backtest":
        _backtest(args.csv)


if __name__ == "__main__":
    main()
