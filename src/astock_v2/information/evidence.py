"""P14-E: production Evidence / Provenance / Bundle layer.

Consumes an already-resolved P14-D query result + P14-B authoritative
records to construct, freeze, persist, and verify Evidence Bundles.

Authority chain (P14-E MUST NOT re-execute):

    P14-B RawStore         identity primitives (ingestion_id, hash)
    P14-A projection       RawIngestRecord -> RawInformationRecord
    P14-D run_query        PIT visibility + version selection (resolved)
    P14-E (this module)    evidence / bundle / persistence / trace

FOUR-CLASS reverse trace taxonomy (frozen):
    REVERSE_TRACE_NOT_FOUND
    REVERSE_TRACE_AMBIGUOUS
    REVERSE_TRACE_IDENTITY_MISMATCH
    RAW_RECORD_CORRUPTED

FOUR-CLASS selection/rejection enums (frozen):
    SELECTED_HIGHEST_REVISION
    SELECTED_EARLIEST_ON_REVISION_TIE
    SELECTED_CANONICAL_TIEBREAK
    REJECTED_LOWER_REVISION
    REJECTED_REVISION_TIE_NOT_EARLIEST
    REJECTED_CANONICAL_TIEBREAK

Deterministic: no wall-clock, UUID, randomness, or environment value
enters any result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import RawInformationRecord, parse_boundary
from .raw_store import RawIngestRecord
from .research_query import ResearchQuery

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BUNDLE_SCHEMA_VERSION = "p14e-evidence-bundle-1"

IDENTITY_FIELDS = (
    "source", "source_id", "revision", "event_time",
    "available_time", "adapter_version", "raw_payload_hash", "ingestion_id",
)
EVIDENCE_FIELDS = IDENTITY_FIELDS + (
    "entity_id", "information_type", "ingested_at",
)

SELECTION_HIGHEST = "SELECTED_HIGHEST_REVISION"
SELECTION_EARLIEST_TIE = "SELECTED_EARLIEST_ON_REVISION_TIE"
SELECTION_CANONICAL = "SELECTED_CANONICAL_TIEBREAK"
REJECTED_LOWER = "REJECTED_LOWER_REVISION"
REJECTED_TIE_NOT_EARLIEST = "REJECTED_REVISION_TIE_NOT_EARLIEST"
REJECTED_CANONICAL = "REJECTED_CANONICAL_TIEBREAK"

TRACE_NOT_FOUND = "REVERSE_TRACE_NOT_FOUND"
TRACE_AMBIGUOUS = "REVERSE_TRACE_AMBIGUOUS"
TRACE_IDENTITY_MISMATCH = "REVERSE_TRACE_IDENTITY_MISMATCH"
TRACE_RAW_CORRUPTED = "RAW_RECORD_CORRUPTED"

EXCLUSION_NOT_YET_AVAILABLE = "NOT_YET_AVAILABLE"
EXCLUSION_OUTSIDE_AS_OF = "OUTSIDE_AS_OF"
EXCLUSION_UNRESOLVED = "UNRESOLVED_AVAILABILITY"


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Evidence construction
# ---------------------------------------------------------------------------

def evidence_from(record: RawIngestRecord) -> dict:
    """Build one Evidence dict from a P14-B authoritative record.

    Identity = 8 frozen fields → evidence_id.
    ingested_at is Audit-only (not in evidence_id)."""
    ev = {
        "source": record.source,
        "source_id": record.source_id,
        "revision": record.revision,
        "event_time": record.event_time,
        "available_time": record.available_time,
        "adapter_version": record.adapter_version,
        "raw_payload_hash": record.raw_payload_hash,
        "ingestion_id": record.ingestion_id,
        "entity_id": record.entity_id,
        "information_type": record.entity_type,
        "ingested_at": record.ingested_at,
    }
    identity = {k: ev[k] for k in IDENTITY_FIELDS}
    ev["evidence_id"] = _sha(canonical_json(identity))
    return ev


def check_provenance_complete(evidence: dict) -> None:
    """P14E-P-002: all 11 fields must exist; no defaults."""
    missing = [f for f in EVIDENCE_FIELDS
               if evidence.get(f) is None or evidence.get(f) == ""]
    if missing:
        raise ValueError(f"provenance incomplete, missing: {sorted(missing)}")


def check_mutation(records: list[RawIngestRecord]) -> None:
    """P14E-P-012: same (source, source_id, revision) with distinct
    raw_payload_hash → fail-fast (P14-B authority detects; we refuse)."""
    seen: dict[tuple, set] = {}
    for r in records:
        seen.setdefault((r.source, r.source_id, r.revision), set()).add(
            r.raw_payload_hash)
    for key, hashes in seen.items():
        if len(hashes) > 1:
            raise ValueError(
                f"mutation detected for lineage {key}: "
                f"{len(hashes)} distinct payload hashes")


# ---------------------------------------------------------------------------
# Bundle construction
# ---------------------------------------------------------------------------

def _selection_reason(selected, lineage_records) -> str:
    """Mechanical labeling of P14-D's already-resolved state."""
    others = [c for c in lineage_records if c is not selected]
    if not others:
        return SELECTION_HIGHEST
    if all(c.revision < selected.revision for c in others):
        return SELECTION_HIGHEST
    same_rev = [c for c in others if c.revision == selected.revision]
    if same_rev and all(c.available_time > selected.available_time
                        for c in same_rev):
        return SELECTION_EARLIEST_TIE
    return SELECTION_CANONICAL


def _rejection_reason(candidate, winner) -> str:
    if candidate.revision < winner.revision:
        return REJECTED_LOWER
    if candidate.revision == winner.revision:
        if candidate.available_time > winner.available_time:
            return REJECTED_TIE_NOT_EARLIEST
        return REJECTED_CANONICAL
    return REJECTED_LOWER


def create_bundle(query_result: dict,
                  authoritative_evidence_records: list[RawIngestRecord]) -> dict:
    """Build an EvidenceBundle from an already-resolved P14-D result.

    P14E-P-006: consumes query_result as-is; never re-executes PIT.
    P14E-P-008: candidate_trace is pure bookkeeping of P14-D's decisions.
    """
    # authority check: must be a resolved result
    missing_keys = [k for k in ("query", "records", "excluded", "counts",
                                "result_id") if k not in query_result]
    if missing_keys:
        raise ValueError(
            f"authority_violation: not a resolved P14-D result "
            f"(missing {missing_keys}); P14-E must not execute "
            f"PIT/version-selection")

    records = list(authoritative_evidence_records)
    check_mutation(records)

    # evidence_id + provenance for every candidate
    ev_map: dict[tuple, dict] = {}
    for r in records:
        ev = evidence_from(r)
        check_provenance_complete(ev)
        ev_map[(r.source, r.source_id, r.revision, r.ingested_at)] = ev

    # P14-D resolved: which records were selected
    selected_set = {
        (r["source"], r["source_record_id"], r["revision"], r["ingested_at"])
        for r in query_result["records"]}

    evidence: list[dict] = []
    candidate_trace: list[dict] = []
    lineages: dict[tuple, list] = {}
    for r in records:
        lineages.setdefault((r.source, r.source_id), []).append(r)

    for lineage_key in sorted(lineages):
        lin = lineages[lineage_key]
        # winner = the record whose (source, source_id, rev, ingested_at)
        # is in selected_set AND in this lineage
        winners = [r for r in lin
                   if (r.source, r.source_id, r.revision, r.ingested_at)
                   in selected_set]
        if not winners:
            continue  # fully excluded lineage
        winner = winners[0]
        reason = _selection_reason(winner, lin)
        ev = dict(ev_map[(winner.source, winner.source_id,
                          winner.revision, winner.ingested_at)])
        ev["selection_reason"] = reason
        evidence.append(ev)
        # candidates = all non-winners in this lineage
        for cand in lin:
            if cand is winner:
                continue
            candidate_trace.append({
                "source": cand.source, "source_id": cand.source_id,
                "revision": cand.revision,
                "available_time": cand.available_time,
                "raw_payload_hash": cand.raw_payload_hash,
                "ingested_at": cand.ingested_at,
                "rejection_reason": _rejection_reason(cand, winner),
            })

    evidence.sort(key=lambda e: (e["source"], e["source_id"], e["revision"]))
    candidate_trace.sort(key=lambda t: (t["source"], t["source_id"],
                                        t["revision"], t["available_time"],
                                        t["raw_payload_hash"]))
    seen: set = set()
    unique_trace = []
    for t in candidate_trace:
        k = (t["source"], t["source_id"], t["revision"],
             t["available_time"], t["raw_payload_hash"])
        if k not in seen:
            seen.add(k)
            unique_trace.append(t)

    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "query": query_result["query"],
        "as_of": query_result["query"]["as_of"],
        "result_id": query_result["result_id"],
        "evidence": evidence,
        "candidate_trace": unique_trace,
        "exclusions": query_result["excluded"],
        "counts": {"evidence": len(evidence), "candidates": len(unique_trace),
                   "exclusions": len(query_result["excluded"]),
                   "examined": len(records)},
    }
    bundle["bundle_id"] = _sha(canonical_json(bundle))
    return bundle


def freeze_bundle(bundle: dict) -> dict:
    """FREEZE: canonical bytes locked; any later change is detectable."""
    return json.loads(canonical_json(bundle))


def validate_bundle(bundle: dict, result: dict) -> None:
    """P14E-006 mapping closure: exact 1:1 result ↔ evidence."""
    got = sorted((e["source"], e["source_id"], e["revision"], e["ingestion_id"])
                 for e in bundle["evidence"])
    want = sorted((r["source"], r["source_record_id"], r["revision"],
                   r["ingestion_id"]) for r in result["records"])
    if got != want:
        raise ValueError("mapping closure violated: result ↔ evidence not 1:1")
    if bundle["result_id"] != result["result_id"]:
        raise ValueError("result_id linkage broken")


# ---------------------------------------------------------------------------
# Reverse trace (FOUR-CLASS)
# ---------------------------------------------------------------------------

_RAW_ROW_REQUIRED = ("source", "source_id", "revision", "event_time",
                     "available_time", "raw_payload_hash", "ingestion_id")


class ReverseTraceError(ValueError):
    def __init__(self, cls: str, message: str):
        if cls not in (TRACE_NOT_FOUND, TRACE_AMBIGUOUS,
                       TRACE_IDENTITY_MISMATCH, TRACE_RAW_CORRUPTED):
            raise ValueError(f"unknown reverse-trace class {cls!r}")
        super().__init__(f"{cls}: {message}")
        self.cls = cls


def load_raw_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            raise ReverseTraceError(TRACE_RAW_CORRUPTED,
                                    "raw row is not valid JSON")
    return rows


def reverse_trace_resolve(evidence: dict, raw_rows: list[dict]) -> dict:
    """FOUR-CLASS authoritative resolution."""
    parsed = []
    for row in raw_rows:
        if isinstance(row, str):
            try:
                row = json.loads(row)
            except json.JSONDecodeError:
                raise ReverseTraceError(TRACE_RAW_CORRUPTED,
                                        "raw row is not valid JSON")
        rec = row.get("record", row) if isinstance(row, dict) else None
        if not isinstance(rec, dict) or any(
                rec.get(f) in (None, "") for f in _RAW_ROW_REQUIRED):
            raise ReverseTraceError(TRACE_RAW_CORRUPTED,
                                    "raw row missing required fields")
        parsed.append(row)
    matches = [row for row in parsed
               if row["record"]["ingestion_id"] == evidence["ingestion_id"]
               and row["record"]["raw_payload_hash"] == evidence["raw_payload_hash"]]
    if len(matches) == 0:
        raise ReverseTraceError(TRACE_NOT_FOUND,
                                "no authoritative row matches")
    if len(matches) > 1:
        raise ReverseTraceError(TRACE_AMBIGUOUS,
                                f"{len(matches)} rows match")
    rec = matches[0]["record"]
    for field in ("source", "source_id", "revision", "event_time",
                  "available_time"):
        if rec[field] != evidence[field]:
            raise ReverseTraceError(TRACE_IDENTITY_MISMATCH,
                                    f"field {field} mismatch")
    return rec
