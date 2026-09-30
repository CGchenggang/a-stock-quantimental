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
    FRESH,
    FRESHNESS_POLICIES,
    MISSING_POLICY,
    STALE,
    UNKNOWN,
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
from astock_v2.information.adapters import AdapterMetadata
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

# R1-1/R5/Production: what the completeness contract expects per source.
# EXPECTED_CONTRACT is frozen a priori and INDEPENDENT of the fixture
# payloads: it defines what the source contract says SHOULD exist. The
# delta between this contract and the actual ingested records reveals
# missing entities/dates. company_announcement has an extra expected
# date (2026-03-04) that the fixture does not provide -> UNEXPECTED_MISSING
# evidence in the audit.
#
# Production (Contract §8.2/§8.3): EXPECTED_ABSENCE is declared ONLY via
# expected_absence_pairs (X ⊆ E x D, enforced fail-fast by
# astock_v2.information.expected_contract). Boolean control keys
# (expected_absence / expected_empty) and fixture-control fields are
# structurally rejected. us_index_daily declares (SPX, 2026-03-03) absent:
# the pair is not required and is reported as EXPECTED_ABSENCE evidence
# without touching the coverage denominator.
EXPECTED_CONTRACT = {
    "cn_index_daily": {
        "expected_entities": ["CSI300"],
        "expected_dates": ["2026-03-02", "2026-03-03"],
    },
    "company_announcement": {
        "expected_entities": ["000001"],
        "expected_dates": ["2026-03-03", "2026-03-04"],
    },
    "macro_pmi_cn": {
        "expected_entities": ["CN"],
        "expected_dates": ["2026-01-31", "2025-12-31"],
    },
    "us_index_daily": {
        "expected_entities": ["SPX"],
        "expected_dates": ["2026-03-02", "2026-03-03"],
        "expected_absence_pairs": [["SPX", "2026-03-03"]],
    },
    "broken_source": {
        "expected_entities": ["NONE"],
        "expected_dates": [],
    },
    "parse_failure_source": {
        "expected_entities": ["CN"],
        "expected_dates": ["2026-03-01"],
    },
    "source_empty_source": {
        "expected_entities": [],
        "expected_dates": [],
    },
}

# R1-2/R3-2/R5: adapters that exercise isolated failure paths (deterministic)
# Each anomaly semantic is carried by exactly ONE source:
#   broken_source          -> SOURCE_ERROR (fetch always raises)
#   parse_failure_source   -> PARSE_FAILURE (parse always fails)
#   source_empty_source    -> SOURCE_EMPTY (fetch returns zero payloads)
#   company_announcement   -> UNEXPECTED_MISSING (contract expects 03-04
#                             but only 03-03 ingested)
#   broken_source + EXPECTED_CONTRACT.expected_absence -> EXPECTED_ABSENCE
class BrokenSourceAdapter(MacroPMICNAdapter):
    """Always raises a fetch error -> SOURCE_ERROR in the audit chain."""

    metadata = AdapterMetadata(
        source="broken_source",
        source_category="MACRO",
        adapter_version="broken_source_adapter@1",
        timestamp_semantics="N/A (always fails)",
        revision_semantics="N/A",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def fetch(self):
        raise RuntimeError("deterministic fixture: source is broken")


class ParseFailureAdapter(MacroPMICNAdapter):
    """Returns a payload that passes fetch but fails parse (missing source_id)."""

    metadata = AdapterMetadata(
        source="parse_failure_source",
        source_category="MACRO",
        adapter_version="parse_failure_adapter@1",
        timestamp_semantics="N/A (parse always fails)",
        revision_semantics="N/A",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def fetch(self):
        return [{"entity_id": "CN", "event_time": "2026-03-01T09:00:00+08:00",
                 "available_time": "2026-03-01T10:00:00+08:00",
                 "ingested_at": "2026-03-01T10:00:00+08:00", "value": 51.0}]

    def parse(self, payload):
        raise ValueError("deterministic fixture: missing source_id triggers parse failure")


class SourceEmptyAdapter(MacroPMICNAdapter):
    """Fetch succeeds but returns zero payloads -> SOURCE_EMPTY evidence."""

    metadata = AdapterMetadata(
        source="source_empty_source",
        source_category="MACRO",
        adapter_version="source_empty_adapter@1",
        timestamp_semantics="N/A (source is healthy but returns no data)",
        revision_semantics="N/A",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def fetch(self):
        return []


# R1-2: adapters that exercise failure paths
def _payload_adapters():
    adapters = {
        source: adapter_cls(list(FIXTURE_PAYLOADS.get(source, [])))
        for source, adapter_cls in (
            ("cn_index_daily", CNIndexDailyAdapter),
            ("company_announcement", CompanyAnnouncementAdapter),
            ("macro_pmi_cn", MacroPMICNAdapter),
            ("us_index_daily", USIndexDailyAdapter),
            ("broken_source", BrokenSourceAdapter),
            ("parse_failure_source", ParseFailureAdapter),
            ("source_empty_source", SourceEmptyAdapter),
        )
    }
    return adapters


def _compute_completeness(
    contract: dict[str, dict],
    raw_records: list,
    audit_out: dict[str, dict],
) -> dict:
    """Production completeness (Contract §8/§9), via
    astock_v2.information.expected_contract.ExpectedContract.

    - The expected universe (E, D, X) comes from EXPECTED_CONTRACT, frozen
      a priori, never from actual payloads (EXP-001..004).
    - R = P - X; expected_count = |R|; actual_count = |A ∩ R|; coverage is
      1.0 when R is empty (§9.2). Declared absences never reduce coverage.
    - Source-level missingness class (§7.1), frozen priority:
        1. SOURCE_EMPTY   — adapter fetch succeeded and returned zero
                            payloads (EMPTY_SUCCESS status)
        2. SOURCE_ERROR   — adapter fetch raised
        3. PARSE_FAILURE  — adapter parse raised (PARSE_ERROR status)
        4. UNEXPECTED_MISSING — a required pair (in R) was not delivered
        5. EXPECTED_ABSENCE   — every required pair was delivered but some
                            contract-declared absent pairs remain unobserved
        6. NONE           — no missing observation exists; EXPECTED_ABSENCE
                            is a pair-level declaration, never a label for
                            "everything is fine"
      Observation-evidence classes take precedence over contract-derived
      classes because a failed fetch/parse is itself an observed anomaly.
    - Each entry carries the Type C declaration provenance (§16.4) for its
      expected_absence_pairs; observation-only fields never appear there.
    """
    from astock_v2.information.expected_contract import ExpectedContract

    completeness: dict[str, dict] = {}
    all_sources = sorted(set(list(contract) + list(audit_out)))
    for source in all_sources:
        entry = ExpectedContract(source, contract.get(source, {}))
        actual_pairs = {
            (r.entity_id, r.event_time[:10])
            for r in raw_records if r.source == source
        }
        comp = entry.completeness(actual_pairs)
        report = audit_out.get(source, {})
        if report.get("status") == "EMPTY_SUCCESS":
            missingness = "SOURCE_EMPTY"
        elif report.get("status") == "SOURCE_ERROR":
            missingness = "SOURCE_ERROR"
        elif report.get("status") == "PARSE_ERROR":
            missingness = "PARSE_FAILURE"
        else:
            missingness = entry.source_missingness_class(actual_pairs)
        completeness[source] = {
            **comp,
            "missingness_class": missingness,
            "expected_absence_evidence": entry.declaration_provenance(),
        }
    return completeness


def _compute_freshness_per_record(
    research_records: list, decision_time: str
) -> dict[str, dict[str, int]]:
    """R1-3: freshness per source from real available_time + P14-A policy.

    Computed on the P14-A research records (not raw ingest records), since
    RawInformationRecord carries freshness_policy_id. Unresolved records
    (available_time=None) are counted before the projection and merged here.
    """
    per_source: dict[str, dict[str, int]] = {}
    for record in research_records:
        source = record.source
        if source not in per_source:
            per_source[source] = {"fresh": 0, "stale": 0, "unresolved": 0}
        if record.freshness_policy_id is None:
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
    completeness = _compute_completeness(EXPECTED_CONTRACT, raw_records, audit_out)

    # R1-3: freshness per source from real records + P14-A policy
    fresh_per_source = _compute_freshness_per_record(research, RESEARCH_END_T)

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
                    src_entry["ingestion_id"] = r.ingestion_id
                    src_entry["raw_payload_hash"] = r.raw_payload_hash
                    src_entry["provenance"] = {
                        "source": r.source, "source_id": r.source_id,
                        "ingested_at": r.ingested_at,
                        "adapter_version": r.adapter_version,
                    }
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
