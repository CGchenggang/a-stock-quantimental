"""Check point-in-time coverage of a normalized P13-M industry CSV."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from astock_v2.industry import (
    admissible_industry,
    coverage_start,
    load_industry_membership_csv,
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--symbol", action="append")
    p.add_argument("--backtest-start", help="ISO date/time, e.g. 2020-01-01T00:00:00+08:00")
    p.add_argument("--decision-time", help="ISO date/time used for PIT admissibility")
    return p.parse_args()


def main():
    args = parse_args()
    memberships = load_industry_membership_csv(Path(args.input))
    starts = coverage_start(memberships)

    symbols = args.symbol or sorted(starts)
    print("P13-M industry coverage")
    for symbol in symbols:
        start = starts.get(symbol)
        if start is None:
            print(f"{symbol}: NO_COVERAGE")
            continue

        status = "OK"
        if args.backtest_start:
            backtest_start = datetime.fromisoformat(args.backtest_start)
            if start > backtest_start:
                status = "PARTIAL_COVERAGE"
        print(f"{symbol}: coverage_start={start.isoformat()} status={status}")

        if args.decision_time:
            decision_time = datetime.fromisoformat(args.decision_time)
            event_time = backtest_start if args.backtest_start else start
            match = admissible_industry(memberships, symbol, event_time, decision_time)
            if match is None:
                print(f"  PIT: no admissible membership at event={event_time.isoformat()}")
            else:
                print(
                    f"  PIT: {match.industry_code} {match.industry_name} "
                    f"effective_from={match.effective_from.isoformat()} "
                    f"available_time={match.available_time.isoformat()}"
                )


if __name__ == "__main__":
    main()
