"""Run the P13-N benchmark with an in-process peak-RSS sampler."""
from __future__ import annotations

import runpy
import sys
import threading
import time

import psutil

peak = [0]
stop = threading.Event()


def sample():
    proc = psutil.Process()
    while not stop.is_set():
        try:
            peak[0] = max(peak[0], proc.memory_info().rss)
        except psutil.Error:
            pass
        time.sleep(0.05)


def main():
    sys.argv = ["run_local_industry_relative_oos.py"] + sys.argv[1:]
    watcher = threading.Thread(target=sample, daemon=True)
    watcher.start()
    start = time.perf_counter()
    try:
        runpy.run_path(
            "scripts/run_local_industry_relative_oos.py", run_name="__main__"
        )
    finally:
        stop.set()
        watcher.join()
        print(
            f"\nwall_seconds={time.perf_counter() - start:.1f} "
            f"peak_rss_mb={peak[0] // 1048576}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
