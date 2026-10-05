"""R4-C: deterministic 76-stock research validation loop.

Engineering validation over the frozen universe — NOT a statistical
holdout evaluation and NOT P13-T. It orchestrates the accepted R4-B batch
(which orchestrates the accepted R4-A runs); it computes nothing new:

    frozen universe (sorted, BOM-safe loader)
      -> explicit as_of set (research zone; virgin as_ofs fail fast
         per-target via the accepted assert_research_zone guard — this
         module adds NO date logic of its own)
      -> run_research_batch(...)               [R4-B, accepted]
      -> data completeness: expected vs observed symbols (observed =
         symbols with authoritative P14-B records after the batch's
         idempotent pre-ingestion; missing symbols are REPORTED, never
         silently skipped — status becomes DATA_INCOMPLETE)
      -> validation result {validation_id, status, run_parameters,
         results[], summary, manifest}
      -> deterministic manifest with a content digest; identical inputs
         (any input order) -> identical results and manifest

Scope guards: no second PIT/selection/evidence surface, no registry
writes (P13-Q/P13-R are never touched), no wall-clock, no randomness.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .research_batch import run_research_batch
from .research_run import _sha

DEFAULT_UNIVERSE_FILE = Path("data") / "industry" / "validation_universe_76.txt"


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def load_universe(path: str | Path = DEFAULT_UNIVERSE_FILE) -> dict:
    """Load the frozen validation universe (utf-8-sig: BOM-safe; blank
    lines ignored; duplicates collapsed; order-insensitive identity)."""
    raw = Path(path).read_text(encoding="utf-8-sig").splitlines()
    symbols = sorted({line.strip() for line in raw if line.strip()})
    if not symbols:
        raise ValueError(f"universe file {path} contains no symbols")
    return {"universe_id": "universe-" + _sha("|".join(symbols))[:16],
            "symbols": symbols}


def _observed_symbols(raw_store) -> set:
    """Symbols that have authoritative P14-B records (data inventory over
    the accepted store — this is NOT research selection; all research
    visibility remains the P14-D query inside each run)."""
    return {r.symbol for r in raw_store.records() if r.symbol}


def run_validation(symbols: Sequence[str], as_ofs: Sequence[str], *,
                   historical_store=None, raw_store,
                   ingested_at: str | None = None,
                   lookback: int = 20) -> dict:
    """Run one deterministic validation batch over the universe.

    One call to the accepted R4-B runner for the whole (symbols x as_ofs)
    cross product; per-target failure isolation is inherited from it.
    Completeness is reported explicitly: a universe symbol without any
    authoritative record is MISSING_DATA and flips the validation status
    to DATA_INCOMPLETE — it is never silently skipped.
    """
    symbols = sorted({str(s) for s in symbols})
    as_ofs = sorted({str(a) for a in as_ofs})
    if not symbols or not as_ofs:
        raise ValueError("validation requires symbols and as_ofs")
    universe_id = "universe-" + _sha("|".join(symbols))[:16]

    batch = run_research_batch(symbols, as_ofs,
                               historical_store=historical_store,
                               raw_store=raw_store, ingested_at=ingested_at,
                               lookback=lookback)

    observed = _observed_symbols(raw_store)
    missing = sorted(set(symbols) - observed)

    results: list[dict] = []
    actions: dict = {}
    for entry in batch["results"]:
        if entry["status"] == "OK":
            run = entry["run"]
            action = run["recommendation"]["action"]
            actions[action] = actions.get(action, 0) + 1
            results.append({
                "symbol": entry["symbol"], "as_of": entry["as_of"],
                "status": "OK", "run_id": run["run_id"],
                "result_id": run["result_id"], "bundle_id": run["bundle_id"],
                "record_id": run["recommendation"]["record_id"],
                "action": action, "evidence_ids": run["evidence_ids"],
                "error": None,
            })
        else:
            results.append({
                "symbol": entry["symbol"], "as_of": entry["as_of"],
                "status": "FAILED", "run_id": None, "result_id": None,
                "bundle_id": None, "record_id": None, "action": None,
                "evidence_ids": [], "error": entry["error"],
            })
    results.sort(key=lambda r: (r["symbol"], r["as_of"]))

    ok = sum(1 for r in results if r["status"] == "OK")
    failed = len(results) - ok
    summary = {
        "expected": len(symbols),
        "observed": len(set(symbols) & observed),
        "total": len(results), "ok": ok, "failed": failed,
        "missing_data": len(missing),
        "no_action": actions.get("NO_ACTION", 0),
        "research": actions.get("RESEARCH", 0),
        "hold": actions.get("HOLD", 0),
    }
    validation_id = "r4c-" + _sha("|".join(
        ["r4c", universe_id, *as_ofs, f"lookback={lookback}",
         ingested_at or ""]))[:16]
    status = "OK" if not missing else "DATA_INCOMPLETE"

    manifest = {
        "validation_id": validation_id,
        "status": status,
        "universe": {"universe_id": universe_id, "symbols": symbols},
        "as_ofs": as_ofs,
        "run_parameters": {"lookback": lookback, "ingested_at": ingested_at},
        "completeness": {
            "expected": summary["expected"],
            "observed": summary["observed"],
            "missing": missing,
            "coverage": (round(summary["observed"] / summary["expected"], 4)
                         if summary["expected"] else 0.0),
        },
        "counts": {"total": summary["total"], "ok": summary["ok"],
                   "failed": summary["failed"],
                   "missing_data": summary["missing_data"],
                   "no_action": summary["no_action"],
                   "research": summary["research"],
                   "hold": summary["hold"]},
        "per_result_identity": [
            {"symbol": r["symbol"], "as_of": r["as_of"],
             "status": r["status"], "run_id": r["run_id"],
             "result_id": r["result_id"], "bundle_id": r["bundle_id"],
             "record_id": r["record_id"], "action": r["action"]}
            for r in results],
    }
    manifest["content_digest"] = _sha(_canonical(manifest))

    return {
        "validation_id": validation_id,
        "status": status,
        "universe": {"universe_id": universe_id, "symbols": symbols},
        "as_ofs": as_ofs,
        "run_parameters": {"lookback": lookback, "ingested_at": ingested_at},
        "results": results,
        "summary": summary,
        "manifest": manifest,
    }
