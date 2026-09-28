"""Instrumented profile of the P13-M pooled industry context builder.

Measures setup stage timings (membership load, record load, PIT state build,
historical membership precompute) and runs the pooled decision-day loop under
cProfile. This is a diagnostic companion to run_local_industry_relative_oos.py
and changes no production semantics.
"""
from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import time

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.industry_loader import load_industry_memberships
from astock_v2.industry_relative import (
    _build_pit_return_state,
    _historical_membership_maps,
    _membership_schedule,
    build_universe_industry_relative_context_maps,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe-file", required=True)
    parser.add_argument("--membership", required=True)
    parser.add_argument("--root", default="data")
    args = parser.parse_args()

    universe = tuple(
        line.strip().zfill(6)
        for line in open(args.universe_file, encoding="utf-8-sig")
        if line.strip() and not line.lstrip().startswith("#")
    )

    t0 = time.perf_counter()
    memberships = load_industry_memberships(args.membership)
    t1 = time.perf_counter()
    print(f"stage membership_load seconds={t1 - t0:.2f} rows={len(memberships)}", flush=True)

    store = LocalHistoricalStore(args.root)
    all_records = {symbol: store.read_records("cn_stock_daily", symbol) for symbol in universe}
    t2 = time.perf_counter()
    n_records = sum(len(v) for v in all_records.values())
    print(f"stage record_load seconds={t2 - t1:.2f} symbols={len(all_records)} records={n_records}", flush=True)

    schedules = {
        symbol: _membership_schedule([m for m in memberships if m.symbol == symbol])
        for symbol in universe
    }
    t3 = time.perf_counter()
    print(f"stage membership_schedules seconds={t3 - t2:.2f}", flush=True)

    state = _build_pit_return_state(all_records)
    t4 = time.perf_counter()
    print(f"stage pit_state_build seconds={t4 - t3:.2f}", flush=True)

    event_days = sorted(
        {record.event_time[:10] for records in all_records.values() for record in records}
    )
    historical = {
        symbol: _historical_membership_maps(schedules[symbol], event_days)
        for symbol in universe
    }
    t5 = time.perf_counter()
    print(f"stage historical_memberships seconds={t5 - t4:.2f} event_days={len(event_days)}", flush=True)

    profiler = cProfile.Profile()
    profiler.enable()
    result = build_universe_industry_relative_context_maps(
        store, args.membership, universe, lookback=20
    )
    profiler.disable()
    t6 = time.perf_counter()
    targets = sum(1 for v in result.values() if v)
    total_rows = sum(len(v) for v in result.values())
    print(f"stage pooled_build_seconds={t6 - t5:.2f} targets_with_context={targets} total_context_rows={total_rows}", flush=True)

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("tottime").print_stats(25)
    print(stream.getvalue(), flush=True)


if __name__ == "__main__":
    main()
