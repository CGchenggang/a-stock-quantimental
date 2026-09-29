"""P14-A: deterministic information-layer audit over synthetic fixtures.

Builds representative fixture records from registered sources, runs them
through the full contract pipeline (provenance -> dedup -> conflict ->
normalize -> PIT selection -> freshness), and writes byte-identical JSON
artifacts plus a SHA256 manifest. No live data, no LLM, no network.

The fixture records cover the P13-O..P13-S research window only; the
virgin zone (>= 2026-09-23) is exercised by tests via fail-fast, never by
this audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astock_v2.information import (
    FRESHNESS_POLICIES,
    SOURCE_REGISTRY,
    RawInformationRecord,
    detect_conflicts,
    freshness_status,
    normalize,
    provenance_summary,
    select_asof,
)

SCHEMA_VERSION = "p14a-info-audit-1"

FIXTURES = [
    # macro PMI: initial release + later revision (late-arriving correction)
    {"source": "macro_pmi_cn", "source_id": "PMI_CN_2026M01",
     "source_category": "MACRO", "entity_id": "CN", "entity_type": "ECONOMY",
     "event_time": "2026-01-31T09:00:00+08:00",
     "available_time": "2026-02-01T09:30:00+08:00",
     "revision": 0, "ingested_at": "2026-02-01T10:00:00+08:00",
     "value": 50.1, "unit": "index", "freshness_policy_id": "macro_release_35d"},
    {"source": "macro_pmi_cn", "source_id": "PMI_CN_2026M01",
     "source_category": "MACRO", "entity_id": "CN", "entity_type": "ECONOMY",
     "event_time": "2026-01-31T09:00:00+08:00",
     "available_time": "2026-02-15T09:30:00+08:00",
     "revision": 1, "ingested_at": "2026-02-15T10:00:00+08:00",
     "value": 50.3, "unit": "index", "freshness_policy_id": "macro_release_35d"},
    # cross-source conflict on the same fact (kept, not resolved)
    {"source": "macro_cpi_cn", "source_id": "PMI_ALT_2026M01",
     "source_category": "MACRO", "entity_id": "CN", "entity_type": "ECONOMY",
     "event_time": "2026-01-31T09:00:00+08:00",
     "available_time": "2026-02-01T10:05:00+08:00",
     "revision": 0, "ingested_at": "2026-02-01T10:10:00+08:00",
     "value": 50.4, "unit": "index", "freshness_policy_id": "macro_release_35d"},
    # A-share market daily
    {"source": "cn_index_daily", "source_id": "CSI300_2026-03-02",
     "source_category": "A_SHARE_MARKET", "entity_id": "CSI300",
     "entity_type": "INDEX", "symbol": "000300",
     "event_time": "2026-03-02T15:00:00+08:00",
     "available_time": "2026-03-02T16:00:00+08:00",
     "revision": 0, "ingested_at": "2026-03-02T16:05:00+08:00",
     "value": 4123.45, "unit": "points",
     "freshness_policy_id": "market_daily"},
    # overseas market daily
    {"source": "us_index_daily", "source_id": "SPX_2026-03-02",
     "source_category": "OVERSEAS_MARKET", "entity_id": "SPX",
     "entity_type": "INDEX",
     "event_time": "2026-03-02T05:00:00+08:00",
     "available_time": "2026-03-02T06:00:00+08:00",
     "revision": 0, "ingested_at": "2026-03-02T06:10:00+08:00",
     "value": 5432.1, "unit": "points",
     "freshness_policy_id": "overseas_daily"},
    # company announcement (text content)
    {"source": "company_announcement", "source_id": "ANN_000001_2026-03-03",
     "source_category": "COMPANY", "entity_id": "000001",
     "entity_type": "LISTED_COMPANY", "symbol": "000001",
     "event_time": "2026-03-03T17:30:00+08:00",
     "available_time": "2026-03-03T19:00:00+08:00",
     "revision": 0, "ingested_at": "2026-03-03T19:10:00+08:00",
     "content": "Board approves the 2026 annual business plan (research fixture text).",
     "language": "zh", "freshness_policy_id": "announcement_72h"},
    # duplicate ingestion of the same announcement (dedup target)
    {"source": "company_announcement", "source_id": "ANN_000001_2026-03-03",
     "source_category": "COMPANY", "entity_id": "000001",
     "entity_type": "LISTED_COMPANY", "symbol": "000001",
     "event_time": "2026-03-03T17:30:00+08:00",
     "available_time": "2026-03-03T19:00:00+08:00",
     "revision": 0, "ingested_at": "2026-03-03T21:00:00+08:00",
     "content": "Board approves the 2026 annual business plan (research fixture text).",
     "language": "zh", "freshness_policy_id": "announcement_72h"},
]
DECISION_TIME = "2026-03-10T16:00:00+08:00"  # research zone, fixed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="data/industry/p14a")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = [RawInformationRecord(**fixture) for fixture in FIXTURES]
    conflicts = detect_conflicts(raw)
    research = normalize(raw)
    visible = select_asof(research, DECISION_TIME)

    freshness_rows = []
    for record in research:
        freshness_rows.append({
            "record_id": record.record_id,
            "freshness_policy_id": record.freshness_policy_id,
            "status": freshness_status(record, DECISION_TIME, FRESHNESS_POLICIES),
        })

    summary = {
        "schema_version": SCHEMA_VERSION,
        "decision_time": DECISION_TIME,
        "fixture_records": len(FIXTURES),
        "raw_records": len(raw),
        "research_records": len(research),
        "visible_at_decision_time": len(visible),
        "conflict_groups": len(conflicts),
        "registered_sources": sorted(SOURCE_REGISTRY),
        "freshness_policies": sorted(FRESHNESS_POLICIES),
        "provenance": provenance_summary(raw),
    }

    audit_path = out_dir / "research_information_audit.json"
    audit_path.write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "summary": summary,
            "conflicts": {
                "|".join(map(str, key)): sources
                for key, sources in conflicts.items()
            },
            "records": [r.as_dict() for r in research],
            "freshness": freshness_rows,
        }, sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "fixtures": "embedded deterministic fixtures in run_p14a_info_audit.py",
        },
        "outputs": {},
    }
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        data = path.read_bytes()
        manifest["outputs"][path.name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
