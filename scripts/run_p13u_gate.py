"""P13-U: virgin holdout data accumulation & integrity gate.

Data-integrity gate, NOT a research stage. It reads the local price store
and the P13-O audit only to answer: what is frozen research_end/virgin_start,
how many virgin trading days have accumulated, is the virgin zone complete,
has any virgin date been consumed by the research pipeline, and has P13-T
reached its minimum/recommended execution conditions.

It never computes performance metrics (accuracy/brier/returns/...) over the
virgin zone and never emits recommendations. Frozen boundaries are module
constants; they can only change by editing this file (auditable), never by
following the latest data date.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESEARCH_END = "2026-09-22"   # frozen: last OOS decision day consumed by research
VIRGIN_START = "2026-09-23"   # frozen: first possible virgin trading day
MINIMUM_TRADING_DAYS = 20     # one walk-forward test window
RECOMMENDED_TRADING_DAYS = 60 # statistically meaningful window

STATUS_ACCUMULATING = "ACCUMULATING"
STATUS_READY_MINIMUM = "READY_MINIMUM"
STATUS_READY_RECOMMENDED = "READY_RECOMMENDED"
STATUS_BLOCKED = "BLOCKED"

CONTAMINATION_MESSAGE = "VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE"

# research products whose decision_time fields are scanned for contamination
RESEARCH_ARTIFACTS = (
    "data/industry/p13r/recommendation_audit.json",
    "data/industry/p13s/research_reports.json",
)


def assert_research_zone(dates, virgin_start: str = VIRGIN_START) -> None:
    """Fail fast if any research input carries a virgin-zone decision date.

    Research pipelines (P13-O/P/Q/R analysis entry points) call this on every
    decision_time they load. Virgin holdout rows may only be consumed by an
    explicit future P13-T evaluation, which must bypass this guard knowingly.
    """
    offending = sorted(d for d in dates if str(d)[:10] >= virgin_start)
    if offending:
        raise ValueError(
            f"{CONTAMINATION_MESSAGE}: decision dates >= {virgin_start} "
            f"received by a research pipeline: {offending[:5]}"
            + (" ..." if len(offending) > 5 else "")
        )


def load_universe(path: str) -> list[str]:
    return [line.strip().zfill(6) for line in open(path, encoding="utf-8-sig") if line.strip()]


def consumed_dates_from_audit(audit: dict) -> set[str]:
    """Decision dates actually consumed by P13-O/P/Q/R/S.

    The P13-O audit is the single source from which every later stage
    (P13-P incremental models, P13-Q calibration, P13-R policies, P13-S
    reports) derived its rows, so its decision-date set is the authoritative
    consumed boundary.
    """
    return {
        r["decision_time"][:10]
        for r in audit["predictions"]
    }


def artifact_contamination(paths: list[Path], virgin_start: str) -> dict[str, list[str]]:
    """Scan research artifacts for any decision_time inside the virgin zone."""
    found: dict[str, list[str]] = {}

    def walk(node, hits):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("decision_time", "data_available_time") and isinstance(value, str):
                    if value[:10] >= virgin_start:
                        hits.add(value[:10])
                else:
                    walk(value, hits)
        elif isinstance(node, list):
            for item in node:
                walk(item, hits)

    for path in paths:
        if not path.exists():
            continue
        hits: set[str] = set()
        try:
            walk(json.loads(path.read_text(encoding="utf-8")), hits)
        except (json.JSONDecodeError, OSError):
            continue
        if hits:
            found[str(path)] = sorted(hits)
    return found


def sha256_of(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_virgin_zone(store_dir: Path, universe: list[str], audit: dict,
                     research_end: str, virgin_start: str) -> dict:
    """Scan the price store for trading dates after research_end.

    Only existence/completeness is inspected; no price value is aggregated
    into any research metric.
    """
    universe_set = set(universe)
    consumed = consumed_dates_from_audit(audit)
    by_date: dict[str, set[str]] = defaultdict(set)
    for path in store_dir.glob("*.jsonl"):
        symbol = path.stem
        if symbol not in universe_set:
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                event_time = json.loads(line).get("event_time", "")
                day = event_time[:10]
                if day > research_end:
                    by_date[day].add(symbol)

    missing_days = sorted(d for d in by_date if consumed & {d})
    virgin_days = sorted(d for d in by_date if d not in consumed)
    coverage = []
    for day in virgin_days:
        observed = by_date[day]
        coverage.append({
            "date": day,
            "expected_symbols": len(universe),
            "observed_symbols": len(observed),
            "missing_symbols": sorted(universe_set - observed),
        })
    return {
        "consumed_dates_in_virgin_zone": missing_days,
        "virgin_trading_days": virgin_days,
        "coverage": coverage,
    }


def gate_status(days: int, contaminated: bool) -> str:
    if contaminated:
        return STATUS_BLOCKED
    if days >= RECOMMENDED_TRADING_DAYS:
        return STATUS_READY_RECOMMENDED
    if days >= MINIMUM_TRADING_DAYS:
        return STATUS_READY_MINIMUM
    return STATUS_ACCUMULATING


def build_gate_report(store_dir: Path, universe: list[str], audit: dict,
                      artifact_paths: list[Path]) -> dict:
    zone = scan_virgin_zone(store_dir, universe, audit, RESEARCH_END, VIRGIN_START)
    consumed_in_zone = zone["consumed_dates_in_virgin_zone"]
    artifact_hits = artifact_contamination(artifact_paths, VIRGIN_START)
    contaminated = bool(consumed_in_zone) or bool(artifact_hits)
    days = len(zone["virgin_trading_days"])
    latest = max((r["decision_time"][:10] for r in audit["predictions"]), default="")
    latest_data = max(
        (c["date"] for c in zone["coverage"]), default=None
    )
    missing_dates = [
        c["date"] for c in zone["coverage"] if c["missing_symbols"]
    ]
    return {
        "research_end": RESEARCH_END,
        "virgin_start": VIRGIN_START,
        "latest_research_consumed_date": latest,
        "latest_available_data_date": latest_data,
        "virgin_trading_days": days,
        "gate_status": gate_status(days, contaminated),
        "contamination_detected": contaminated,
        "contamination_details": {
            "consumed_dates_in_virgin_zone": consumed_in_zone,
            "research_artifacts_touching_virgin_zone": artifact_hits,
        },
        "missing_dates_with_missing_symbols": missing_dates,
        "minimum_trading_days": MINIMUM_TRADING_DAYS,
        "recommended_trading_days": RECOMMENDED_TRADING_DAYS,
        "p13_t_executable_minimum": days >= MINIMUM_TRADING_DAYS and not contaminated,
        "p13_t_executable_recommended": days >= RECOMMENDED_TRADING_DAYS and not contaminated,
        "coverage": zone["coverage"],
        "research_only": True,
        "note": "P13-U inspects existence/completeness only; no performance "
                "metric is computed over the virgin zone.",
    }


def frozen_manifest(paths: dict[str, str]) -> dict:
    return {
        "research_end": RESEARCH_END,
        "virgin_start": VIRGIN_START,
        "minimum_trading_days": MINIMUM_TRADING_DAYS,
        "recommended_trading_days": RECOMMENDED_TRADING_DAYS,
        "frozen_hashes": {
            name: sha256_of(Path(path)) for name, path in paths.items()
        },
        "boundary_rule": "research_end is the research consumption boundary; "
                         "it never follows the latest data date",
    }


def write_manifest(out_dir: Path, output_paths: list[Path]) -> dict:
    outputs = {}
    for path in sorted(set(output_paths)):
        if path.is_file():
            rel = str(path.relative_to(out_dir)).replace("\\", "/")
            data = path.read_bytes()
            outputs[rel] = {"sha256": hashlib.sha256(data).hexdigest(),
                            "size": len(data)}
    manifest = {
        "generated_for": "P13-U",
        "outputs": outputs,
        "note": "no dynamic timestamp; deterministic artifact",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default="data/industry/p13o/oos_predictions_76.json")
    parser.add_argument("--universe", default="data/industry/validation_universe_76.txt")
    parser.add_argument("--store", default="data/clean/cn_stock_daily")
    parser.add_argument("--out-dir", default="data/industry/p13u")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    universe = load_universe(args.universe)
    with open(args.audit, encoding="utf-8") as f:
        audit = json.load(f)

    artifact_paths = [Path(p) for p in RESEARCH_ARTIFACTS]
    report = build_gate_report(Path(args.store), universe, audit, artifact_paths)

    analysis_config = {
        "universe_file": args.universe,
        "audit_file": args.audit,
        "store": args.store,
        "frozen_constants": {
            "RESEARCH_END": RESEARCH_END,
            "VIRGIN_START": VIRGIN_START,
            "MINIMUM_TRADING_DAYS": MINIMUM_TRADING_DAYS,
            "RECOMMENDED_TRADING_DAYS": RECOMMENDED_TRADING_DAYS,
        },
        "research_artifacts_scanned": [str(p) for p in artifact_paths],
    }
    (out_dir / "analysis_config.json").write_text(
        json.dumps(analysis_config, sort_keys=True, indent=1), encoding="utf-8"
    )
    (out_dir / "virgin_gate.json").write_text(
        json.dumps({"gate_status": report["gate_status"],
                    "virgin_trading_days": report["virgin_trading_days"],
                    "p13_t_executable_minimum": report["p13_t_executable_minimum"],
                    "p13_t_executable_recommended": report["p13_t_executable_recommended"],
                    "research_only": True},
                   sort_keys=True, indent=1),
        encoding="utf-8",
    )
    (out_dir / "coverage.json").write_text(
        json.dumps(report["coverage"], sort_keys=True, indent=1), encoding="utf-8"
    )
    (out_dir / "integrity_report.json").write_text(
        json.dumps({k: v for k, v in report.items() if k != "coverage"},
                   sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    frozen_paths = {
        "universe_file": args.universe,
        "p13o_audit": args.audit,
        "p13q_calibration_registry": "data/industry/p13q/calibration_registry.json",
        "p13r_policy_registry": "data/industry/p13r/decision_policy_registry.json",
        "p13r_analysis_config_cost_risk": "data/industry/p13r/analysis_config.json",
        "p13s_report_schema": "data/industry/p13s/report_schema.json",
        "p13t_determination": "docs/P13T_RESEARCH_PLAN.md",
    }
    (out_dir / "frozen_manifest.json").write_text(
        json.dumps(frozen_manifest(frozen_paths), sort_keys=True, indent=1),
        encoding="utf-8",
    )
    write_manifest(out_dir, [
        out_dir / "analysis_config.json",
        out_dir / "virgin_gate.json",
        out_dir / "coverage.json",
        out_dir / "integrity_report.json",
        out_dir / "frozen_manifest.json",
    ])
    print(f"gate_status={report['gate_status']} "
          f"virgin_trading_days={report['virgin_trading_days']} "
          f"contamination={report['contamination_detected']}")


if __name__ == "__main__":
    main()
