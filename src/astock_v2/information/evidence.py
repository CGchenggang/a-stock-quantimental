"""P14-E: production Evidence / Provenance / Bundle layer.

Consumes an already-resolved P14-D query result + P14-B authoritative
records to construct, freeze, persist, and verify Evidence Bundles.
P14-E is a pure consumer: PIT visibility, version selection, AND the
selection/rejection labels are resolved by the authorities and carried
by the result — nothing here re-derives any decision (REPAIR-002).

Authority chain (P14-E MUST NOT re-execute):

    P14-B RawStore         identity primitives (ingestion_id, hash)
    P14-A projection       RawIngestRecord -> RawInformationRecord
    P14-A pit              selection rule + its labels (resolve_selection)
    P14-D run_query        PIT visibility + version selection +
                           resolved selection/rejection state (emitted)
    P14-E (this module)    evidence / bundle / persistence / trace

FOUR-CLASS reverse trace taxonomy (frozen):
    REVERSE_TRACE_NOT_FOUND
    REVERSE_TRACE_AMBIGUOUS
    REVERSE_TRACE_IDENTITY_MISMATCH
    RAW_RECORD_CORRUPTED

Selection/rejection labels (frozen, defined in pit.py — the selection
authority — and re-exported here):
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

from .pit import (
    REJECTED_CANONICAL_TIEBREAK,
    REJECTED_LOWER_REVISION,
    REJECTED_REVISION_TIE_NOT_EARLIEST,
    SELECTED_CANONICAL_TIEBREAK,
    SELECTED_EARLIEST_ON_REVISION_TIE,
    SELECTED_HIGHEST_REVISION,
)
from .raw_store import RawIngestRecord

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

# Frozen selection/rejection vocabulary (P14E-P-007). The literals are
# DEFINED by the selection authority (pit.py) and re-exported here —
# P14-E only carries P14-D's resolved labels, it never classifies.
SELECTION_HIGHEST = SELECTED_HIGHEST_REVISION
SELECTION_EARLIEST_TIE = SELECTED_EARLIEST_ON_REVISION_TIE
SELECTION_CANONICAL = SELECTED_CANONICAL_TIEBREAK
REJECTED_LOWER = REJECTED_LOWER_REVISION
REJECTED_TIE_NOT_EARLIEST = REJECTED_REVISION_TIE_NOT_EARLIEST
REJECTED_CANONICAL = REJECTED_CANONICAL_TIEBREAK

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

def _identity_key(record: RawIngestRecord) -> tuple:
    return (record.source, record.source_id, record.revision,
            record.ingested_at)


def _proj_key(proj: dict) -> tuple:
    """Identity key of a P14-D provenance/selection projection — the same
    tuple :func:`_identity_key` yields for the originating raw record."""
    return (proj["source"], proj["source_record_id"], proj["revision"],
            proj["ingested_at"])


def create_bundle(query_result: dict,
                  authoritative_evidence_records: list[RawIngestRecord]) -> dict:
    """Build an EvidenceBundle from an already-resolved P14-D result.

    P14-E is a PURE CONSUMER of resolved state (REPAIR-002): PIT
    visibility, version selection, and the selection/rejection labels are
    all decided by the P14-D/P14-A authority and carried by query_result
    (`selection.selected` / `selection.rejected`). The authoritative
    lineage is never scanned for selection truth and no comparison here
    re-derives any decision. The authoritative records exist only to
    anchor evidence identity to P14-B (evidence_id) and to fail fast when
    the resolved state cites a record they do not contain.
    """
    # authority check: must be a fully-resolved P14-D result
    missing_keys = [k for k in ("query", "records", "excluded", "counts",
                                "result_id", "selection")
                    if k not in query_result]
    if missing_keys:
        raise ValueError(
            f"authority_violation: not a resolved P14-D result "
            f"(missing {missing_keys}); P14-E must not execute "
            f"PIT/version-selection")
    selection_state = query_result["selection"]
    missing_state = [k for k in ("selected", "rejected")
                     if k not in selection_state]
    if missing_state:
        raise ValueError(
            f"authority_violation: resolved result carries no "
            f"selection/rejection state (missing {missing_state}); "
            f"P14-E consumes P14-D's resolved decisions verbatim")

    records = list(authoritative_evidence_records)
    check_mutation(records)

    # evidence_id + provenance for every authoritative record
    ev_map: dict[tuple, dict] = {}
    rec_map: dict[tuple, RawIngestRecord] = {}
    for r in records:
        ev = evidence_from(r)
        check_provenance_complete(ev)
        k = _identity_key(r)
        ev_map[k] = ev
        rec_map[k] = r

    # resolved selection labels, keyed by P14-D provenance identity
    reason_by_key: dict[tuple, str] = {}
    for sel in selection_state["selected"]:
        if "selection_reason" not in sel:
            raise ValueError(
                "authority_violation: selected entry without "
                "selection_reason; result is not fully resolved")
        reason_by_key[_proj_key(sel)] = sel["selection_reason"]

    # evidence: 1:1 with result.records, labeled by the resolved state
    evidence: list[dict] = []
    for sel in query_result["records"]:
        k = _proj_key(sel)
        base = ev_map.get(k)
        if base is None:
            raise ValueError(
                f"identity_failure: P14-D selected record {k} not found "
                f"in authoritative records")
        if k not in reason_by_key:
            raise ValueError(
                f"authority_violation: selected record {k} is not covered "
                f"by the resolved selection state")
        ev = dict(base)
        ev["selection_reason"] = reason_by_key[k]
        evidence.append(ev)

    # candidate_trace: P14-D's resolved rejections, projected verbatim
    # (order preserved — the resolved state is emitted in frozen
    # deterministic order; this projection renames fields, never
    # reorders or re-classifies)
    candidate_trace: list[dict] = []
    for rej in selection_state["rejected"]:
        if "rejection_reason" not in rej:
            raise ValueError(
                "authority_violation: rejected entry without "
                "rejection_reason; result is not fully resolved")
        k = _proj_key(rej)
        if k not in rec_map:
            raise ValueError(
                f"identity_failure: rejected candidate {k} not found in "
                f"authoritative records")
        candidate_trace.append({
            "source": rej["source"],
            "source_id": rej["source_record_id"],
            "revision": rej["revision"],
            "available_time": rej["available_time"],
            "raw_payload_hash": rej["raw_payload_hash"],
            "ingested_at": rej["ingested_at"],
            "rejection_reason": rej["rejection_reason"],
        })

    evidence.sort(key=lambda e: (e["source"], e["source_id"], e["revision"]))

    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "query": query_result["query"],
        "as_of": query_result["query"]["as_of"],
        "result_id": query_result["result_id"],
        "evidence": evidence,
        "candidate_trace": candidate_trace,
        "exclusions": query_result["excluded"],
        "counts": {"evidence": len(evidence), "candidates": len(candidate_trace),
                   "exclusions": len(query_result["excluded"]),
                   "examined": query_result["counts"]["examined"]},
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
