"""R4-B: deterministic Research Agent Batch Runner.

Pure orchestration over the accepted R4-A research run — no new research
logic, no second PIT rule, no second ledger:

    universe (symbols x as_ofs)
      -> sorted, deduplicated (symbol, as_of) targets
      -> ONE idempotent pre-ingestion of all target symbols
         (R3-A adapter -> P14-B RawStore), so every run in the batch sees
         the SAME store state — sequential ingestion inside the run loop
         would make each run's examined set depend on batch position and
         break replay;
      -> run_research(...) per target          [R4-A, accepted]
      -> per-target failure isolation          (a failed target is recorded
        with its error; the batch continues — exceptions are never
        swallowed, they are captured and reported)
      -> batch result {batch_id, run_parameters, results[], summary}
      -> append_batch_to_ledger(...)           [existing ledger, one append
        per successful target, carrying evidence identity]

Determinism: targets are deduplicated and sorted by (symbol, as_of), so
input order cannot change the batch result; the pre-ingestion makes the
store state uniform before the first run; every run is the deterministic
R4-A run (no wall-clock, no randomness). batch_id is derived from the
sorted targets and each target's outcome identity. Batch results are
deterministic given (targets, lookback, ingested-at) and the P14-B store
content.

Scope: the runner only orchestrates. Visibility, selection, exclusion and
evidence remain the accepted P14-D/P14-E authorities; the virgin-zone
guard rides on each run's ResearchQuery (assert_research_zone) — a target
with a virgin as_of fails fast and is recorded as FAILED while the rest
of the batch proceeds.
"""
from __future__ import annotations

from typing import Sequence

from ..information.adapters import CNStockQuoteHistoricalAdapter
from .research_run import _sha, append_to_ledger, run_research


def run_research_batch(symbols: Sequence[str], as_ofs: Sequence[str], *,
                       historical_store=None, raw_store,
                       ingested_at: str | None = None,
                       lookback: int = 20) -> dict:
    """Run one deterministic research batch over symbols x as_ofs.

    Every (symbol, as_of) pair is one independent R4-A research run with
    its own research boundary; a failure in one target is recorded and
    never contaminates the others. Targets are deduplicated and sorted by
    (symbol, as_of) — input order is irrelevant by construction. When a
    historical store is supplied, ALL target symbols are pre-ingested
    idempotently before the first run.
    """
    targets = sorted({(str(symbol), str(as_of))
                      for symbol in symbols for as_of in as_ofs})
    if historical_store is not None:
        if not ingested_at:
            raise ValueError(
                "ingested_at is required when ingesting from a historical "
                "store (deterministic batches pin the ingestion timestamp)")
        batch_symbols = sorted({symbol for symbol, _ in targets})
        adapter = CNStockQuoteHistoricalAdapter(
            historical_store, symbols=batch_symbols, ingested_at=ingested_at)
        adapter.ingest(raw_store, ingested_at)

    results: list[dict] = []
    for symbol, as_of in targets:
        try:
            run = run_research(symbol, as_of, raw_store=raw_store,
                               lookback=lookback)
            results.append({"symbol": symbol, "as_of": as_of,
                            "status": "OK", "run": run, "error": None})
        except Exception as exc:  # noqa: BLE001 - isolated + reported
            results.append({"symbol": symbol, "as_of": as_of,
                            "status": "FAILED", "run": None,
                            "error": f"{type(exc).__name__}: {exc}"})

    identity = "|".join(
        [f"lookback={lookback}"]
        + [f"{r['symbol']}|{r['as_of']}|"
           + (r["run"]["run_id"] if r["status"] == "OK" else "FAILED")
           for r in results])
    actions: dict[str, int] = {}
    for r in results:
        if r["status"] == "OK":
            action = r["run"]["recommendation"]["action"]
            actions[action] = actions.get(action, 0) + 1

    return {
        "batch_id": _sha(identity)[:16],
        "run_parameters": {
            "symbols": sorted({s for s, _ in targets}),
            "as_ofs": sorted({a for _, a in targets}),
            "lookback": lookback,
            "ingested_at": ingested_at,
        },
        "results": results,
        "summary": {
            "targets": len(results),
            "ok": sum(1 for r in results if r["status"] == "OK"),
            "failed": sum(1 for r in results if r["status"] == "FAILED"),
            "actions": dict(sorted(actions.items())),
        },
    }


def append_batch_to_ledger(batch_result: dict, ledger,
                           ingested_at: str) -> list[dict]:
    """Append every successful batch target to the existing ledger via the
    existing R4-A append path; failed targets have nothing to append."""
    events = []
    for r in batch_result["results"]:
        if r["status"] == "OK":
            events.append(append_to_ledger(r["run"], ledger, ingested_at))
    return events
