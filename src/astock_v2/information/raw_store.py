"""P14-B: immutable raw ingestion store for the information layer.

Sits between source adapters and the P14-A contract:

    source adapter -> RawIngestRecord -> RawStore -> P14-A normalize

Invariants:

- Immutability: stored records are never updated or deleted. The store
  grows append-only.
- Idempotency: re-ingesting the same (source, source_id, revision) with
  the same raw payload yields exactly one logical record; the replay is
  recorded in the ingestion audit as DUPLICATE.
- No silent overwrite: the same key re-ingested with a DIFFERENT payload
  is flagged RAW_MUTATION_DETECTED; the original record is preserved and
  the incoming payload is recorded as a rejected attempt.
- Revision history: the key includes revision, so revision 1 never
  overwrites revision 0. PIT visibility stays the job of the P14-A layer.
- Provenance: every stored record keeps the full raw payload, its hash,
  the adapter version and the ingestion timestamp (deterministic in
  fixtures; runtime metadata is never mixed into the payload identity).

Raw storage is NOT research admissibility: invalid, unresolved,
duplicate, conflicting records all live here, and only provenance-valid
records may later pass through the P14-A contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import RawInformationRecord, hashlib_sha256

ACCEPTED = "ACCEPTED"
DUPLICATE = "DUPLICATE"
RAW_MUTATION_DETECTED = "RAW_MUTATION_DETECTED"


def canonical_payload_hash(raw_payload: dict) -> str:
    """Deterministic SHA256 of the canonical raw payload.

    Same (source, source_id, revision, payload) -> same hash; any payload
    difference is detectable. No random UUIDs or runtime timestamps.
    """
    canonical = json.dumps(raw_payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RawIngestRecord:
    """Immutable raw ingestion record (handoff §4 contract).

    ``raw_payload`` is the canonical representation of what the adapter
    actually received from the source — kept verbatim so a later audit can
    verify what normalization did to it. ``ingested_at`` is when THIS
    system stored the data; it is never used as available_time.
    """

    source: str
    source_id: str
    source_category: str
    entity_id: str
    entity_type: str
    event_time: str
    available_time: str | None
    revision: int
    ingested_at: str
    raw_payload: dict
    adapter_version: str
    symbol: str | None = None
    content: str | None = None
    value: float | None = None
    unit: str | None = None
    currency: str | None = None
    quality_status: str = "OK"
    availability_status: str = "RESOLVED"
    raw_payload_hash: str = field(init=False)
    ingestion_id: str = field(init=False)

    def __post_init__(self):
        for name in ("source", "source_id", "entity_id", "entity_type",
                     "event_time", "ingested_at", "adapter_version"):
            if not getattr(self, name):
                raise ValueError(f"raw ingest record requires {name}")
        if int(self.revision) < 0:
            raise ValueError("revision must be non-negative")
        # Availability semantics are derived at construction, never patched
        # onto the frozen object afterwards: a record without a reliable
        # available_time is UNRESOLVED and can never pass PIT admissibility.
        if self.available_time is None:
            object.__setattr__(self, "quality_status", "UNRESOLVED")
            object.__setattr__(self, "availability_status",
                               "available_time_unresolved")
        else:
            object.__setattr__(self, "availability_status", "RESOLVED")
        object.__setattr__(self, "raw_payload_hash", canonical_payload_hash(self.raw_payload))
        object.__setattr__(
            self, "ingestion_id",
            hashlib_sha256("|".join([
                self.source, self.source_id, str(self.revision),
                self.raw_payload_hash, self.adapter_version,
            ])),
        )

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        return out

    def key(self) -> tuple[str, str, int]:
        return (self.source, self.source_id, self.revision)


class RawStore:
    """Append-only raw record store plus a durable ingestion attempt audit.

    Two distinct append-only files:

    - ``path`` (raw_records.jsonl): one line per ACCEPTED canonical record.
    - ``audit_path`` (raw_ingestion_audit.jsonl): one durable event per
      ingestion attempt — ACCEPTED, DUPLICATE and RAW_MUTATION_DETECTED —
      so rejected/replayed attempts remain auditable across restarts.

    The audit file is the durable record of every attempt; the in-memory
    list is only a cache of it.
    """

    def __init__(self, path: Path, audit_path: Path | None = None):
        self.path = Path(path)
        self.audit_path = (
            Path(audit_path) if audit_path
            else self.path.parent / "raw_ingestion_audit.jsonl"
        )
        self._records: dict[tuple[str, str, int], RawIngestRecord] = {}
        self._outcomes: list[dict] = []
        self._load_records()
        self._load_audit()

    def _load_records(self):
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            fields = entry["record"]
            # raw_payload_hash / ingestion_id are deterministic init=False
            # fields; drop the serialized copies, __post_init__ recomputes.
            fields.pop("raw_payload_hash", None)
            fields.pop("ingestion_id", None)
            record = RawIngestRecord(**fields)
            self._records[record.key()] = record

    def _load_audit(self):
        if not self.audit_path.exists():
            return
        for line in self.audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            self._outcomes.append(json.loads(line))

    def _append_audit(self, event: dict):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")

    def audit_event(self, event: dict):
        """Durably record an ingestion attempt that produced no canonical
        record (adapter-level parse/source failures)."""
        self._append_audit(event)
        self._outcomes.append(event)

    def put(self, record: RawIngestRecord) -> str:
        """Store one raw record; returns ACCEPTED / DUPLICATE /
        RAW_MUTATION_DETECTED (append-only, never overwrites). Every
        attempt — accepted, replayed or mutated — is durably audited."""
        key = record.key()
        current = self._records.get(key)
        if current is None:
            outcome = ACCEPTED
        elif current.raw_payload_hash == record.raw_payload_hash:
            outcome = DUPLICATE
        else:
            outcome = RAW_MUTATION_DETECTED
        event = {
            "outcome": outcome,
            "source": record.source,
            "source_id": record.source_id,
            "revision": record.revision,
            "incoming_raw_payload_hash": record.raw_payload_hash,
            "stored_raw_payload_hash": (
                current.raw_payload_hash if current is not None else None
            ),
            "ingestion_id": record.ingestion_id,
            "adapter_version": record.adapter_version,
        }
        if outcome == ACCEPTED:
            self._records[key] = record
            self._append(record, outcome)
        self._append_audit(event)
        self._outcomes.append(event)
        return outcome

    def _append(self, record: RawIngestRecord, outcome: str):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(
                {"record": record.as_dict(), "outcome": outcome},
                sort_keys=True, ensure_ascii=False,
            ) + "\n")

    def records(self) -> list[RawIngestRecord]:
        return [self._records[key] for key in sorted(self._records)]

    def outcomes(self) -> list[dict]:
        """All ingestion attempt events, including those persisted by
        earlier RawStore instances on the same files."""
        return list(self._outcomes)


def to_information_record(record: RawIngestRecord) -> RawInformationRecord:
    """Project a raw ingest record onto the P14-A contract.

    available_time may be None (unresolved at the source); the P14-A model
    requires it, so unresolved availability is represented as an empty
    string plus quality_status=UNRESOLVED — such records cannot pass PIT
    admissibility and never silently inherit event_time or ingested_at.
    """
    available = record.available_time or ""
    quality = record.quality_status
    if not available:
        quality = "UNRESOLVED"
    # Preserve the source's freshness policy so P14-C quality audits can
    # compute real FRESH/STALE/UNRESOLVED evidence from P14-A policies.
    from .registry import spec_for
    spec = spec_for(record.source)
    policy_id = spec.freshness_policy_id if spec else None
    return RawInformationRecord(
        source=record.source,
        source_id=record.source_id,
        source_category=record.source_category,
        entity_id=record.entity_id,
        entity_type=record.entity_type,
        event_time=record.event_time,
        available_time=available,
        revision=record.revision,
        ingested_at=record.ingested_at,
        symbol=record.symbol,
        content=record.content,
        value=record.value,
        unit=record.unit,
        currency=record.currency,
        quality_status=quality,
        freshness_policy_id=policy_id,
        metadata={
            "raw_payload_hash": record.raw_payload_hash,
            "ingestion_id": record.ingestion_id,
            "adapter_version": record.adapter_version,
            "availability_status": record.availability_status,
        },
    )
