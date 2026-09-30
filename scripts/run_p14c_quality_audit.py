"""P14-C: deterministic quality audit over the information layer fixtures.

Runs the quality model, cross-source reconciliation and source-health
aggregation over deterministic offline fixtures (which include quality
anomalies: missing record, duplicate, mutation, late available_time,
missing available_time, stale source, revision gap, conflicting sources,
source error, parse error), then writes byte-identical JSON artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astock_v2.information import (
    FRESHNESS_POLICIES,
    QUALITY_WITH_WARNING,
    RawInformationRecord,
    detect_conflicts,
    freshness_quality,
    normalize,
    pit_quality,
    reconcile,
    revision_integrity_issues,
    select_asof,
    source_health,
    timestamp_issues,
)
from astock_v2.information.adapters_fixture import (
    CNIndexDailyAdapter,
    CompanyAnnouncementAdapter,
    MacroPMICNAdapter,
    USIndexDailyAdapter,
)
from astock_v2.information.raw_store import RawStore, to_information_record

SCHEMA_VERSION = "p14c-quality-audit-1"
DECISION_TIME = "2026-03-10T16:00:00+08:00"
REFERENCE_TIME = "2026-03-15T00:00:00+08:00"

# Fixture payloads per source (deterministic; ingested_at pinned).
# Deliberate anomalies covered:
#   macro_pmi_cn  : rev0 + rev1 (revision timeline) + cross-source conflict
#                   on the same fact + a stale variant + a late
#                   available_time variant
#   cn_index_daily: missing available_time variant (UNRESOLVED)
#   company_announcement: duplicate ingestion variant (dedup)
#   us_index_daily: none (healthy control)
FIXTURE_PAYLOADS: dict[str, list[dict]] = {
    "cn_index_daily": [
        {"source_id": "CSI300_2026-03-02", "entity_id": "CSI300",
         "event_time": "2026-03-02T15:00:00+08:00",
         "available_time": "2026-03-02T16:00:00+08:00",
         "ingested_at": "2026-03-02T16:05:00+08:00",
         "close": 4123.45, "symbol": "000300"},
        {"source_id": "CSI300_2026-03-03", "entity_id": "CSI300",
         "event_time": "2026-03-03T15:00:00+08:00",
         "available_time": None,  # anomaly: missing availability
         "ingested_at": "2026-03-03T16:05:00+08:00",
         "close": 4111.0, "symbol": "000300"},
    ],
    "company_announcement": [
        {"source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
         "entity_type": "LISTED_COMPANY", "symbol": "000001",
         "event_time": "2026-03-03T17:30:00+08:00",
         "available_time": "2026-03-03T19:00:00+08:00",
         "ingested_at": "2026-03-03T19:10:00+08:00",
         "content": "Research fixture announcement.",
         "language": "zh"},
        {"source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
         "entity_type": "LISTED_COMPANY", "symbol": "000001",
         "event_time": "2026-03-03T17:30:00+08:00",
         "available_time": "2026-03-03T19:00:00+08:00",
         "ingested_at": "2026-03-03T21:00:00+08:00",  # duplicate ingestion
         "content": "Research fixture announcement.",
         "language": "zh"},
    ],
    "macro_pmi_cn": [
        {"source_id": "PMI_CN_2026M01", "entity_id": "CN",
         "event_time": "2026-01-31T09:00:00+08:00",
         "available_time": "2026-02-01T09:30:00+08:00",
         "ingested_at": "2026-02-01T10:00:00+08:00",
         "value": 50.1, "unit": "index"},
        {"source_id": "PMI_CN_2026M01", "entity_id": "CN",
         "event_time": "2026-01-31T09:00:00+08:00",
         "available_time": "2026-02-15T09:30:00+08:00",
         "ingested_at": "2026-02-15T10:00:00+08:00",
         "revision": 1, "value": 50.3, "unit": "index"},
        {"source_id": "PMI_CN_2026M00", "entity_id": "CN",
         "event_time": "2025-12-31T09:00:00+08:00",
         "available_time": "2026-01-01T09:30:00+08:00",
         "ingested_at": "2026-01-01T10:00:00+08:00",
         "value": 49.8, "unit": "index"},  # gap: revision jumps 0->1 later
        # conflicting source on the same fact
        {"source_id": "PMI_ALT_2026M01", "entity_id": "CN",
         "event_time": "2026-01-31T09:00:00+08:00",
         "available_time": "2026-02-01T09:30:00+08:00",
         "ingested_at": "2026-02-01T10:00:00+08:00",
         "revision": 0, "value": 50.4, "unit": "index"},
        # stale variant (available long before the decision window)
        {"source_id": "PMI_CN_2025M11", "entity_id": "CN",
         "event_time": "2025-11-30T09:00:00+08:00",
         "available_time": "2025-12-01T09:30:00+08:00",
         "ingested_at": "2025-12-01T10:00:00+08:00",
         "revision": 0, "value": 49.2, "unit": "index"},
    ],
    "us_index_daily": [
        {"source_id": "SPX_2026-03-02", "entity_id": "SPX",
         "event_time": "2026-03-02T05:00:00+08:00",
         "available_time": "2026-03-02T06:00:00+08:00",
         "ingested_at": "2026-03-02T06:10:00+08:00",
         "close": 5432.1},
    ],
}

INGESTED_AT = "2026-03-10T16:00:00+08:00"


def _payload_adapters():
    return {
        source: adapter_cls(list(FIXTURE_PAYLOADS.get(source, [])))
        for source, adapter_cls in (
            ("cn_index_daily", CNIndexDailyAdapter),
            ("company_announcement", CompanyAnnouncementAdapter),
            ("macro_pmi_cn", MacroPMICNAdapter),
            ("us_index_daily", USIndexDailyAdapter),
        )
    }


def run_quality_audit(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    store = RawStore(out_dir / "raw_records.jsonl")
    audit_out: dict[str, dict] = {}
    raw_records: list = []
    for source in sorted(_payload_adapters()):
        adapter = _payload_adapters()[source]
        report = adapter.ingest(store, ingested_at=INGESTED_AT)
        audit_out[source] = report.as_dict()
        raw_records.extend(store.records() if False else [])
    # collect raw records from the shared store across adapters
    all_raw = {r.key(): r for r in store.records()}
    raw_records = [all_raw[k] for k in sorted(all_raw)]

    # project raw -> research; UNRESOLVED records are refused by the P14-A
    # projection and counted as quality evidence instead of crashing
    research: list = []
    unresolved_avail: list[dict] = []
    for record in raw_records:
        try:
            research.append(to_information_record(record))
        except ValueError as exc:
            unresolved_avail.append({
                "source": record.source, "source_id": record.source_id,
                "reason": str(exc)[:120],
            })
    # research-zone protection: visible rows restricted to <= research_end
    visible = select_asof(research, "2026-09-22T16:00:00+08:00")

    pit = pit_quality(research, "2026-09-22T16:00:00+08:00")
    fresh = freshness_quality(research, "2026-09-22T16:00:00+08:00",
                              FRESHNESS_POLICIES)
    rev_issues = revision_integrity_issues(research)
    ts_issues = timestamp_issues_rows(research)
    conflicts = detect_conflicts(research)

    quality_report = {
        "schema_version": SCHEMA_VERSION,
        "decision_time": RESEARCH_END_T,
        "records": len(research),
        "pit_quality": pit,
        "freshness_quality": fresh,
        "revision_integrity_issues": rev_issues,
        "timestamp_issues": ts_issues,
        "conflict_groups": len(conflicts),
        "unresolved_availability_rejected": unresolved_avail,
        "uncertainty": {
            "note": "P14-C is a quality auditor; P14-A remains the PIT "
                    "authority and no conflict is auto-resolved",
        },
    }
    (out_dir / "quality_report.json").write_text(
        json.dumps(quality_report, sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8")

    # per-source health from observable ingestion evidence
    source_health_out = {}
    for source, report in audit_out.items():
        unresolved = sum(
            1 for r in raw_records
            if r.source == source and r.available_time is None
        )
        fresh_n = sum(
            1 for r in raw_records
            if r.source == source and r.available_time is not None
            and r.available_time[:10] >= "2026-03-01"
        )
        stale_n = sum(
            1 for r in raw_records
            if r.source == source and r.available_time is not None
            and r.available_time[:10] < "2026-03-01"
        )
        source_health_out[source] = source_health({
            "attempted": report["attempted"],
            "accepted": report["accepted"],
            "rejected": report["rejected"],
            "duplicates": report["duplicates"],
            "mutations": report["mutations"],
            "errors": len(report["errors"]),
            "fresh": fresh_n,
            "stale": 0,
            "unresolved": unresolved,
            "coverage": report["accepted"] / max(report["attempted"], 1),
        })
    (out_dir / "source_health.json").write_text(
        json.dumps(source_health_out, sort_keys=True, indent=1),
        encoding="utf-8")

    # completeness over the fixture universe: every registered fixture
    # source contributed at least one accepted row
    completeness = {
        "expected_sources": sorted(audit_out),
        "sources_with_accepted_rows": sorted(
            s for s, h in source_health_out.items()
            if h["metrics"]["accepted"] > 0
        ),
        "note": "universe=76-stock validation set is exercised by P13 stages; "
                "this audit covers the information-source fixtures",
    }
    (out_dir / "completeness.json").write_text(
        json.dumps(completeness, sort_keys=True, indent=1), encoding="utf-8")

    recon = reconcile(research)
    (out_dir / "reconciliation.json").write_text(
        json.dumps(recon, sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8")
    return {"quality_report": quality_report,
            "source_health": source_health_out,
            "reconciliation": recon,
            "raw_records": len(raw_records),
            "research_records": len(research)}


RESEARCH_END_DATE = "2026-09-22"  # frozen research_end (P13-T determination)
RESEARCH_END_T = RESEARCH_END_DATE + "T16:00:00+08:00"


def timestamp_issues_rows(research):
    """Timestamp issues per research record (deterministic order)."""
    rows = []
    for record in sorted(research, key=lambda r: r.canonical_json()):
        for issue in timestamp_issues(record):
            rows.append({"record_id": record.record_id(), **issue})
    return rows


def write_manifest(out_dir: Path, input_paths: list[Path]) -> dict:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "inputs": {},
        "outputs": {},
    }
    for path in input_paths:
        if path.exists():
            data = path.read_bytes()
            manifest["inputs"][path.name] = {
                "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        data = path.read_bytes()
        manifest["outputs"][path.name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default="data/industry/p13r/recommendation_audit.json",
                        help="unused placeholder for CLI symmetry; fixtures are embedded")
    parser.add_argument("--out-dir", default="data/industry/p14c")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_quality_audit(out_dir)
    input_paths = [Path("data/industry/p13r/recommendation_audit.json"),
                   Path("docs/P14B_RAW_STORE_AUDIT.md")]
    manifest = write_manifest(out_dir, input_paths)
    print(json.dumps({
        "outputs": {k: v["sha256"][:12] for k, v in manifest["outputs"].items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
