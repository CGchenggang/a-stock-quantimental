"""P14-B: ingestion audit over the deterministic fixture adapters.

Runs every registered fixture adapter through the immutable raw store and
the P14-A normalization, then writes a per-source ingestion report and a
SHA256 manifest. Fully deterministic: fixtures pin ingested_at, no
timestamps or randomness anywhere.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astock_v2.information import normalize, select_asof
from astock_v2.information.adapters_fixture import (
    CNIndexDailyAdapter,
    CompanyAnnouncementAdapter,
    MacroPMICNAdapter,
    USIndexDailyAdapter,
)
from astock_v2.information.raw_store import RawStore, to_information_record

FIXTURE_PAYLOADS: dict[str, list[dict]] = {
    "cn_index_daily": [
        {"source_id": "CSI300_2026-03-02", "entity_id": "CSI300",
         "event_time": "2026-03-02T15:00:00+08:00",
         "available_time": "2026-03-02T16:00:00+08:00",
         "ingested_at": "2026-03-02T16:05:00+08:00",
         "close": 4123.45, "symbol": "000300"},
    ],
    "company_announcement": [
        {"source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
         "event_time": "2026-03-03T17:30:00+08:00",
         "available_time": "2026-03-03T19:00:00+08:00",
         "ingested_at": "2026-03-03T19:10:00+08:00",
         "content": "Research fixture announcement.",
         "symbol": "000001"},
    ],
    "macro_pmi_cn": [
        {"source_id": "PMI_CN_2026M01", "entity_id": "CN",
         "event_time": "2026-01-31T09:00:00+08:00",
         "available_time": "2026-02-01T09:30:00+08:00",
         "ingested_at": "2026-02-01T10:00:00+08:00",
         "value": 50.1},
    ],
    "us_index_daily": [
        {"source_id": "SPX_2026-03-02", "entity_id": "SPX",
         "event_time": "2026-03-02T05:00:00+08:00",
         "available_time": "2026-03-02T06:00:00+08:00",
         "ingested_at": "2026-03-02T06:10:00+08:00",
         "close": 5432.1},
    ],
}


def run_ingestion(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    store = RawStore(out_dir / "raw_records.jsonl")
    audit: dict[str, dict] = {}
    research_records = []
    adapters = {
        "cn_index_daily": CNIndexDailyAdapter,
        "company_announcement": CompanyAnnouncementAdapter,
        "macro_pmi_cn": MacroPMICNAdapter,
        "us_index_daily": USIndexDailyAdapter,
    }
    for source in sorted(FIXTURE_PAYLOADS):
        # fresh adapter instance carrying this run's deterministic payloads
        adapter = adapters[source](list(FIXTURE_PAYLOADS[source]))
        report = adapter.ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
        audit[source] = report.as_dict()
    research = normalize([to_information_record(r) for r in store.records()])
    (out_dir / "normalized_records.json").write_text(
        json.dumps([r.as_dict() for r in research], sort_keys=True, indent=1,
                   ensure_ascii=False),
        encoding="utf-8",
    )
    visible = select_asof(research, "2026-03-10T16:00:00+08:00")
    audit_summary = {
        "schema_version": "p14b-ingestion-audit-1",
        "sources": audit,
        "raw_records_stored": len(store.records()),
        "normalized_records": len(research),
        "visible_at_decision_time": len(visible),
        "decision_time": "2026-03-10T16:00:00+08:00",
    }
    (out_dir / "ingestion_audit.json").write_text(
        json.dumps(audit_summary, sort_keys=True, indent=1), encoding="utf-8"
    )
    return audit_summary


def write_manifest(out_dir: Path) -> dict:
    manifest = {"generated_for": "P14-B", "files": {}}
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "manifest.json" or path.name == "raw_records.jsonl":
            continue
        data = path.read_bytes()
        manifest["files"][path.name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        }
    raw = out_dir / "raw_records.jsonl"
    if raw.exists():
        data = raw.read_bytes()
        manifest["files"]["raw_records.jsonl"] = {
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="data/industry/p14b")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = run_ingestion(out_dir)
    manifest = write_manifest(out_dir)
    print(json.dumps(summary, sort_keys=True, indent=1))
    print(f"manifest files: {len(manifest['files'])}")


if __name__ == "__main__":
    main()
