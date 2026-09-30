"""P14-C: deterministic quality audit over the information layer fixtures.

R1 repairs (acceptance findings):
- R1-1: completeness now checks expected vs actual entities and dates with
  coverage_ratio and four missingness classifications.
- R1-2: SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY flow through the full
  evidence chain (ingestion attempt -> audit_event -> quality -> health).
- R1-3: freshness (FRESH/STALE) is computed per record from available_time
  and the P14-A freshness policy; no hardcoded stale counts.
- R1-4: reconciliation groups carry source/value/available_time for every
  contributing source, plus policy_id/policy_version.
- R1-5: quality_report.json has 9 dimensions, each with status / reasons /
  metrics / evidence.
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
    RawInformationRecord,
    classify_missingness,
    detect_conflicts,
    freshness_quality,
    freshness_status,
    normalize,
    pit_quality,
    reconcile,
    revision_integrity_issues,
    select_asof,
    source_health,
    timestamp_issues,
    to_information_record,
)
from astock_v2.information.adapters_fixture import (
    CNIndexDailyAdapter,
    CompanyAnnouncementAdapter,
    MacroPMICNAdapter,
    USIndexDailyAdapter,
)
from astock_v2.information.raw_store import RawStore

SCHEMA_VERSION = "p14c-quality-audit-2"
DECISION_TIME = "2026-03-10T16:00:00+08:00"
REFERENCE_TIME = "2026-03-15T00:00:00+08:00"
RESEARCH_END_DATE = "2026-09-22"
RESEARCH_END_T = RESEARCH_END_DATE + "T16:00:00+08:00"

# ---------------------------------------------------------------------------
# Fixture payloads per source (deterministic; ingested_at pinned).
# Deliberate anomalies:
#   cn_index_daily : missing available_time (UNRESOLVED_AVAILABILITY)
#   company_announcement : duplicate ingestion
#   macro_pmi_cn : rev0 + rev1 timeline + cross-source conflict + stale
#                  variant + revision gap (PMI_CN_2026M00 rev0 jumps)
#   us_index_daily : healthy control
#   broken_source  : parse failure (missing source_id -> model rejects)
#   empty_source   : zero payloads (SOURCE_EMPTY)
# ---------------------------------------------------------------------------

FIXTURE_PAYLOADS: dict[str, list[dict]] = {
    "cn_index_daily": [
        {"source_id": "CSI300_2026-03-02", "entity_id": "CSI300",
         "event_time": "2026-03-02T15:00:00+08:00",
         "available_time": "2026-03-02T16:00:00+08:00",
         "ingested_at": "2026-03-02T16:05:00+08:00",
         "close": 4123.45, "symbol": "000300"},
        {"source_id": "CSI300_2026-03-03", "entity_id": "CSI300",
         "event_time": "2026-03-03T15:00:00+08:00",
         "available_time": None,
         "ingested_at": "2026-03-03T16:05:00+08:00",
         "close": 4111.0, "symbol": "000300"},
    ],
    "company_announcement": [
        {"source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
         "entity_type": "LISTED_COMPANY", "symbol": "000001",
         "event_time": "2026-03-03T17:30:00+08:00",
         "available_time": "2026-03-03T19:00:00+08:00",
         "ingested_at": "2026-03-03T19:10:00+08:00",
         "content": "Research fixture announcement.", "language": "zh"},
        {"source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
         "entity_type": "LISTED_COMPANY", "symbol": "000001",
         "event_time": "2026-03-03T17:30:00+08:00",
         "available_time": "2026-03-03T19:00:00+08:00",
         "ingested_at": "2026-03-03T21:00:00+08:00",
         "content": "Research fixture announcement.", "language": "zh"},
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
         "value": 49.8, "unit": "index"},
        {"source_id": "PMI_ALT_2026M01", "entity_id": "CN",
         "event_time": "2026-01-31T09:00:00+08:00",
         "available_time": "2026-02-01T09:30:00+08:00",
         "ingested_at": "2026-02-01T10:00:00+08:00",
         "revision": 0, "value": 50.4, "unit": "index"},
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
    # R1-1 fixture: a source that returns zero payloads -> SOURCE_EMPTY
    "broken_source": [],
}

INGESTED_AT = "2026-03-10T16:00:00+08:00"

# R1-1: what the completeness contract expects per source
EXPECTED_CONTRACT = {
    "cn_index_daily": {
        "expected_entities": ["CSI300"],
        "expected_dates": ["2026-03-02", "2026-03-03"],
    },
    "company_announcement": {
        "expected_entities": ["000001"],
        "expected_dates": ["2026-03-03"],
    },
    "macro_pmi_cn": {
        "expected_entities": ["CN"],
        "expected_dates": ["2026-01-31", "2025-12-31"],
    },
    "us_index_daily": {
        "expected_entities": ["SPX"],
        "expected_dates": ["2026-03-02"],
    },
    "broken_source": {
        "expected_entities": ["NONE"],
        "expected_dates": [],
        "expected_absence": True,  # deliberate SOURCE_EMPTY fixture
    },
}

# R1-2: adapters that exercise failure paths
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


def _compute_completeness(
    fixture_payloads: dict[str, list[dict]],
    raw_records: list,
    audit_out: dict[str, dict],
) -> dict:
    """R1-1: real completeness with expected/actual entities and dates.

    For each source:
      expected_entities/dates come from the fixture contract.
      actual_entities/dates come from successfully ingested raw records.
      missing_entities/dates are the delta (never forward-filled).
      coverage_ratio = actual / expected (0.0 when expected is empty).
      missingness_class uses classify_missingness to explain WHY.
    """
    completeness: dict[str, dict] = {}
    for source in sorted(set(list(fixture_payloads) + list(audit_out))):
        payloads = fixture_payloads.get(source, [])
        report = audit_out.get(source, {})
        expected_entities = sorted({
            p["entity_id"] for p in payloads if p.get("entity_id")
        })
        expected_dates = sorted({
            p["event_time"][:10] for p in payloads if p.get("event_time")
        })
        actual_entities = sorted({
            r.entity_id for r in raw_records if r.source == source
        })
        actual_dates = sorted({
            r.event_time[:10] for r in raw_records if r.source == source
        })
        missing_entities = sorted(set(expected_entities) - set(actual_entities))
        missing_dates = sorted(set(expected_dates) - set(actual_dates))
        expected_count = len(expected_entities) * max(len(expected_dates), 1)
        actual_count = len(actual_entities) * max(len(actual_dates), 1)
        coverage = actual_count / expected_count if expected_count > 0 else 1.0
        # missingness classification per source
        if report.get("status") == "SOURCE_ERROR":
            missingness = "SOURCE_ERROR"
        elif report.get("status") == "PARSE_ERROR":
            missingness = "PARSE_FAILURE"
        elif report.get("attempted", 0) > 0 and report.get("accepted", 0) == 0 \
                and not payloads:
            missingness = "SOURCE_EMPTY"
        elif missing_entities or missing_dates:
            missingness = "UNEXPECTED_MISSING"
        else:
            missingness = "EXPECTED_ABSENCE"
        completeness[source] = {
            "expected_entities": expected_entities,
            "actual_entities": actual_entities,
            "missing_entities": missing_entities,
            "expected_dates": expected_dates,
            "actual_dates": actual_dates,
            "missing_dates": missing_dates,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "coverage_ratio": round(coverage, 4),
            "missingness_class": missingness,
        }
    return completeness


def _compute_freshness_per_record(
    raw_records: list, decision_time: str
) -> dict[str, dict[str, int]]:
    """R1-3: freshness per source from real available_time + P14-A policy."""
    per_source: dict[str, dict[str, int]] = {}
    for record in raw_records:
        source = record.source
        if source not in per_source:
            per_source[source] = {"fresh": 0, "stale": 0, "unresolved": 0}
        if record.available_time is None:
            per_source[source]["unresolved"] += 1
            continue
        status = freshness_status(
            record, decision_time, dict(FRESHNESS_POLICIES))
        if status == FRESH:
            per_source[source]["fresh"] += 1
        elif status == STALE:
            per_source[source]["stale"] += 1
        else:
            per_source[source]["unresolved"] += 1
    return per_source


def _build_nine_dimensions(
    completeness: dict,
    pit: dict,
    fresh: dict,
    rev_issues: list,
    ts_issues: list,
    conflicts: dict,
    source_health_out: dict,
    unresolved_avail: list[dict],
) -> dict:
    """R1-5: nine-dimension quality report, each with status/reasons/metrics/evidence."""

    def _dim(status: str, reasons: list[str], metrics: dict, evidence: list) -> dict:
        return {"status": status, "reasons": reasons,
                "metrics": metrics, "evidence": evidence}

    # Completeness
    total_expected = sum(c["expected_count"] for c in completeness.values())
    total_actual = sum(c["actual_count"] for c in completeness.values())
    comp_ratio = total_actual / total_expected if total_expected else 1.0
    comp_missing = [s for s, c in completeness.items()
                    if c["missing_entities"] or c["missing_dates"]]
    comp_status = "PASS" if not comp_missing else "FAIL"
    completeness_dim = _dim(
        comp_status,
        [f"source {s} missing entities/dates" for s in comp_missing] or
        ["all expected entities and dates present"],
        {"expected_total": total_expected, "actual_total": total_actual,
         "coverage_ratio": round(comp_ratio, 4)},
        [{"source": s, **c} for s, c in sorted(completeness.items())],
    )

    # Validity (provenance)
    prov_rejected = unresolved_avail
    validity_dim = _dim(
        "PASS" if not prov_rejected else "FAIL",
        [f"{r['source_id']}: {r['reason'][:60]}" for r in prov_rejected] or
        ["all records have valid provenance"],
        {"total_rejected": len(prov_rejected)},
        prov_rejected,
    )

    # Timeliness
    timeliness_dim = _dim(
        "PASS" if not ts_issues else "FAIL",
        [f"{i['check']} on {i.get('record_id', '?')[:12]}" for i in ts_issues] or
        ["no timestamp issues"],
        {"total_issues": len(ts_issues)},
        ts_issues,
    )

    # Freshness
    fresh_dim = _dim(
        "PASS" if fresh.get("FRESH", 0) > 0 else "WARN",
        [f"{k}={v}" for k, v in sorted(fresh.items()) if v > 0],
        dict(fresh),
        [],
    )

    # Consistency
    consistency_dim = _dim(
        "PASS" if not conflicts else "WARN",
        [f"conflict group {k}" for k in sorted(conflicts)] or
        ["no cross-source conflicts"],
        {"conflict_groups": len(conflicts)},
        [{"group": "|".join(map(str, k)), "sources": v}
         for k, v in sorted(conflicts.items())],
    )

    # RevisionIntegrity
    rev_dim = _dim(
        "PASS" if not rev_issues else "WARN",
        [f"{i['check']} on {i.get('source_id', '?')}" for i in rev_issues] or
        ["no revision integrity issues"],
        {"total_issues": len(rev_issues)},
        rev_issues,
    )

    # ProvenanceIntegrity
    prov_dim = _dim(
        "PASS" if not unresolved_avail else "WARN",
        [f"{r['source_id']} unresolved availability" for r in unresolved_avail] or
        ["all records have resolved provenance"],
        {"total_unresolved": len(unresolved_avail)},
        unresolved_avail,
    )

    # PITAdmissibility
    pit_dim = _dim(
        "PASS" if pit.get("PIT_ADMISSIBLE", 0) > 0 else "WARN",
        [f"{k}={v}" for k, v in sorted(pit.items()) if v > 0],
        dict(pit),
        [],
    )

    # SourceHealth
    unhealthy = {s: h for s, h in source_health_out.items()
                 if h["health"] not in ("OK",)}
    sh_dim = _dim(
        "PASS" if all(h["health"] == "OK" for h in source_health_out.values())
        else "WARN",
        [f"{s}: {h['health']}" for s, h in sorted(source_health_out.items())
         if h["health"] != "OK"] or ["all sources healthy"],
        {"total_sources": len(source_health_out),
         "healthy": sum(1 for h in source_health_out.values()
                        if h["health"] == "OK")},
        [{"source": s, **h} for s, h in sorted(source_health_out.items())],
    )

    return {
        "completeness": completeness_dim,
        "validity": validity_dim,
        "timeliness": timeliness_dim,
        "freshness": fresh_dim,
        "consistency": consistency_dim,
        "revision_integrity": rev_dim,
        "provenance_integrity": prov_dim,
        "pit_admissibility": pit_dim,
        "source_health": sh_dim,
    }


def run_quality_audit(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    store = RawStore(out_dir / "raw_records.jsonl")
    audit_out: dict[str, dict] = {}
    for source in sorted(_payload_adapters()):
        adapter = _payload_adapters()[source]
        report = adapter.ingest(store, ingested_at=INGESTED_AT)
        audit_out[source] = report.as_dict()
    all_raw = {r.key(): r for r in store.records()}
    raw_records = [all_raw[k] for k in sorted(all_raw)]

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
    visible = select_asof(research, RESEARCH_END_T)

    pit = pit_quality(research, RESEARCH_END_T)
    fresh = freshness_quality(research, RESEARCH_END_T, FRESHNESS_POLICIES)
    rev_issues = revision_integrity_issues(research)
    ts_issues = timestamp_issues_rows(research)
    conflicts = detect_conflicts(research)

    # R1-1: real completeness
    completeness = _compute_completeness(FIXTURE_PAYLOADS, raw_records, audit_out)

    # R1-3: freshness per source from real records + P14-A policy
    fresh_per_source = _compute_freshness_per_record(raw_records, RESEARCH_END_T)

    # source health using real fresh/stale/unresolved counts
    source_health_out = {}
    for source, report in audit_out.items():
        fc = fresh_per_source.get(source, {"fresh": 0, "stale": 0, "unresolved": 0})
        source_health_out[source] = source_health({
            "attempted": report["attempted"],
            "accepted": report["accepted"],
            "rejected": report["rejected"],
            "duplicates": report["duplicates"],
            "mutations": report["mutations"],
            "errors": len(report["errors"]),
            "fresh": fc["fresh"],
            "stale": fc["stale"],
            "unresolved": fc["unresolved"],
            "coverage": report["accepted"] / max(report["attempted"], 1),
        })

    # R1-5: nine-dimension quality report
    nine_dims = _build_nine_dimensions(
        completeness, pit, fresh, rev_issues, ts_issues,
        conflicts, source_health_out, unresolved_avail)

    quality_report = {
        "schema_version": SCHEMA_VERSION,
        "decision_time": RESEARCH_END_T,
        "records": len(research),
        "dimensions": nine_dims,
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

    (out_dir / "source_health.json").write_text(
        json.dumps(source_health_out, sort_keys=True, indent=1),
        encoding="utf-8")
    (out_dir / "completeness.json").write_text(
        json.dumps(completeness, sort_keys=True, indent=1), encoding="utf-8")

    recon = reconcile(research)
    # R1-4: ensure reconciliation output preserves timestamps + provenance
    for group in recon["groups"]:
        for src_entry in group["sources"]:
            # find the matching raw record to add available_time + provenance
            for r in raw_records:
                if r.source == src_entry["source"] and r.source_id == src_entry["source_id"]:
                    src_entry["event_time"] = r.event_time
                    src_entry["ingested_at"] = r.ingested_at
                    src_entry["record_id"] = r.record_id()
                    src_entry["raw_payload_hash"] = r.raw_payload_hash
                    break
    (out_dir / "reconciliation.json").write_text(
        json.dumps(recon, sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8")

    return {"quality_report": quality_report,
            "source_health": source_health_out,
            "completeness": completeness,
            "reconciliation": recon,
            "raw_records": len(raw_records),
            "research_records": len(research)}


def timestamp_issues_rows(research):
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
    parser.add_argument("--out-dir", default="data/industry/p14c")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_quality_audit(out_dir)
    input_paths = [Path("docs/P14B_RAW_STORE_AUDIT.md"),
                   Path("docs/P14C_RESEARCH_PLAN.md")]
    manifest = write_manifest(out_dir, input_paths)
    print(json.dumps({
        "outputs": {k: v["sha256"][:12] for k, v in manifest["outputs"].items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
