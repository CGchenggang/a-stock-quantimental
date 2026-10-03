"""P14-D: PIT-safe research information query layer (production).

Answers exactly one question: given a research query (entity +
information_type + as_of), what information was already AVAILABLE at
that point in time — reproducibly, auditably, and traceably.

Authority reuse (nothing here redefines upstream semantics):

- P14-A ``parse_boundary`` / ``visible_revisions``: PIT admissibility
  (available_time <= as_of, inclusive) and deterministic version
  selection per (source, source_id) lineage.
- P14-C taxonomy: UNRESOLVED_AVAILABILITY is reused verbatim for records
  whose available_time is missing — no second anomaly vocabulary.
- P13-U ``assert_research_zone``: any as_of at/after the frozen virgin
  boundary (2026-09-23) fails fast; the query layer is a research entry
  point.

This layer performs information retrieval ONLY. It produces no
prediction, ranking, recommendation, or trading decision.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from astock_v2.research_boundary import assert_research_zone

from .models import RawInformationRecord, parse_boundary
from .pit import resolve_selection, visible_revisions

EXCLUSION_NOT_YET_AVAILABLE = "NOT_YET_AVAILABLE"
EXCLUSION_OUTSIDE_AS_OF = "OUTSIDE_AS_OF"
# Reused from the P14-C missingness taxonomy — deliberately not redefined.
EXCLUSION_UNRESOLVED_AVAILABILITY = "UNRESOLVED_AVAILABILITY"

#: provenance carried by every visible record (Contract §9)
PROVENANCE_FIELDS = (
    "source", "source_record_id", "entity_id", "information_type",
    "event_time", "available_time", "revision", "ingested_at",
    "adapter_version", "raw_payload_hash", "ingestion_id",
)


@dataclass(frozen=True)
class ResearchQuery:
    """Minimal research query (Contract §5): entity + information_type +
    as_of, with an optional source scope. No other fields exist."""

    entity: str
    information_type: str
    as_of: str
    source: str | None = None

    def __post_init__(self):
        for name in ("entity", "information_type", "as_of"):
            if not getattr(self, name):
                raise ValueError(f"research query requires {name}")
        # as_of must be a timezone-aware ISO timestamp (P14-A parse rule).
        parse_boundary(self.as_of)
        # P13-U guard: research queries may never target the virgin zone.
        assert_research_zone([self.as_of])

    def as_dict(self) -> dict:
        return {
            "entity": self.entity,
            "information_type": self.information_type,
            "as_of": self.as_of,
            "source": self.source,
        }


def _provenance(record: RawInformationRecord) -> dict:
    """Contract §9 provenance projection; every field serves
    PIT/audit/reproducibility."""
    meta = record.metadata or {}
    return {
        "source": record.source,
        "source_record_id": record.source_id,
        "entity_id": record.entity_id,
        "information_type": record.entity_type,
        "event_time": record.event_time,
        "available_time": record.available_time,
        "revision": record.revision,
        "ingested_at": record.ingested_at,
        "adapter_version": meta.get("adapter_version"),
        "raw_payload_hash": meta.get("raw_payload_hash"),
        "ingestion_id": meta.get("ingestion_id"),
    }


def _in_scope(record: RawInformationRecord, query: ResearchQuery) -> bool:
    if record.entity_id != query.entity:
        return False
    if record.entity_type != query.information_type:
        return False
    if query.source is not None and record.source != query.source:
        return False
    return True


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def run_query(records: list[RawInformationRecord],
              query: ResearchQuery) -> dict:
    """Execute a PIT-safe research query; returns the Contract §9 result.

    Deterministic: same records + same query -> byte-identical result.
    No runtime timestamp, UUID, randomness, or environment value enters
    the result.
    """
    visible: list[RawInformationRecord] = []
    excluded: list[dict] = []
    as_of = parse_boundary(query.as_of)

    for record in sorted(records, key=lambda r: r.canonical_json()):
        if not _in_scope(record, query):
            reason = EXCLUSION_OUTSIDE_AS_OF
        else:
            # P14-C taxonomy reuse: unavailable or unresolvable
            # availability can never establish visibility.
            try:
                available = parse_boundary(record.available_time)
            except ValueError:
                excluded.append({
                    "source": record.source,
                    "source_id": record.source_id,
                    "reason": EXCLUSION_UNRESOLVED_AVAILABILITY,
                    "available_time": record.available_time,
                })
                continue
            if available > as_of:
                reason = EXCLUSION_NOT_YET_AVAILABLE
            else:
                visible.append(record)
                continue
        excluded.append({
            "source": record.source,
            "source_id": record.source_id,
            "reason": reason,
            "available_time": record.available_time,
        })
    excluded.sort(key=lambda e: (e["source"], e["source_id"], e["reason"]))

    # P14-A authority: per-lineage deterministic version selection (latest
    # admissible revision; ties by earliest available_time then canonical
    # json). Different source_ids are distinct information events.
    selected = visible_revisions(visible, query.as_of)
    provenance = [_provenance(selected[key]) for key in sorted(selected)]
    provenance.sort(key=lambda p: (
        p["source"], p["source_record_id"], p["available_time"],
        p["revision"], _canonical(p)))

    # Resolved selection/rejection state (REPAIR-002): the selection
    # authority labels its own decision at resolution time — the winner
    # of every lineage with its selection_reason, and every visible
    # non-selected record with its rejection_reason. PIT-excluded records
    # are NOT selection rejections; they stay in `excluded`. P14-E
    # consumes these labels verbatim and never re-derives them.
    selected_pairs, rejected_pairs = resolve_selection(visible, selected)
    selection_state = {
        "selected": [
            {**_provenance(record), "selection_reason": reason}
            for record, reason in selected_pairs],
        "rejected": [
            {**_provenance(record), "rejection_reason": reason}
            for record, reason in rejected_pairs],
    }
    selection_state["selected"].sort(key=lambda p: (
        p["source"], p["source_record_id"], p["available_time"],
        p["revision"], _canonical(p)))
    selection_state["rejected"].sort(key=lambda p: (
        p["source"], p["source_record_id"], p["revision"],
        p["available_time"], _canonical(p)))

    counts = {
        "visible": len(provenance),
        "excluded": len(excluded),
        "examined": len(records),
    }
    result = {
        "query": query.as_dict(),
        "records": provenance,
        "excluded": excluded,
        "selection": selection_state,
        "counts": counts,
    }
    result["result_id"] = hashlib.sha256(_canonical(result).encode("utf-8")).hexdigest()
    return result
