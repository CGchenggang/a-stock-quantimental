"""Canonical information record model for the P14 information layer.

Field semantics (the contract):

- ``event_time``: when the event actually happened / applies. Never a PIT
  criterion by itself.
- ``available_time``: when a market participant could first obtain the
  information. The ONLY time used for PIT admissibility
  (``available_time <= decision_time``, inclusive).
- ``source``: where the record came from (answers "where from?").
- ``source_id``: which record/event inside that source (answers "which
  one?"). Together with ``source`` and ``revision`` it forms the
  deduplication key.
- ``entity_id`` / ``entity_type``: what the information is about.
- ``symbol``: optional security identifier when the entity is a listed
  instrument.
- ``content`` / ``value``: textual body or numeric measurement. At least
  one must be present.
- ``revision``: monotonically increasing correction counter of the same
  (source, source_id) fact. A higher revision with a later available_time
  is a late-arriving correction, never a backfill of the past.
- ``ingested_at``: when our pipeline stored the record. Provenance bookkeeping
  only; never used for PIT or freshness decisions.
- ``quality_status``: ``OK`` / ``UNRESOLVED`` / ``INVALID``. Only ``OK``
  records may enter the PIT-safe research layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

QUALITY_OK = "OK"
QUALITY_UNRESOLVED = "UNRESOLVED"
QUALITY_INVALID = "INVALID"
QUALITY_STATUSES = (QUALITY_OK, QUALITY_UNRESOLVED, QUALITY_INVALID)

SCHEMA_VERSION = "p14a-information-1"

REQUIRED_FIELDS = (
    "source", "source_id", "entity_id", "entity_type",
    "event_time", "available_time",
)


def parse_boundary(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"timestamp must include an explicit timezone: {value!r}")
    return dt


@dataclass(frozen=True)
class RawInformationRecord:
    source: str
    source_id: str
    source_category: str
    entity_id: str
    entity_type: str
    event_time: str
    available_time: str
    revision: int = 0
    ingested_at: str = ""
    symbol: str | None = None
    content: str | None = None
    value: float | None = None
    unit: str | None = None
    currency: str | None = None
    language: str | None = None
    quality_status: str = QUALITY_OK
    freshness_policy_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        for name in REQUIRED_FIELDS:
            if not getattr(self, name):
                raise ValueError(f"information record requires {name}")
        if int(self.revision) < 0:
            raise ValueError("revision must be non-negative")
        if self.quality_status not in QUALITY_STATUSES:
            raise ValueError(f"unknown quality_status: {self.quality_status}")
        parse_boundary(self.event_time)
        parse_boundary(self.available_time)
        if self.content is None and self.value is None:
            raise ValueError("information record requires content or value")

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    def canonical_json(self) -> str:
        """Deterministic serialization: sorted keys, no runtime fields."""
        return json.dumps(self.as_dict(), sort_keys=True, ensure_ascii=False)

    def record_id(self) -> str:
        return hashlib_sha256(self.canonical_json())


def hashlib_sha256(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResearchInformationRecord:
    """Normalized, provenance-validated record admitted to the research layer."""

    record_id: str
    raw_record_id: str
    research_only: bool
    conflict_status: str | None
    source: str
    source_id: str
    source_category: str
    entity_id: str
    entity_type: str
    event_time: str
    available_time: str
    revision: int
    ingested_at: str
    symbol: str | None
    content: str | None
    value: float | None
    unit: str | None
    currency: str | None
    language: str | None
    quality_status: str
    freshness_policy_id: str | None
    metadata: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, ensure_ascii=False)


def utc_now_iso() -> str:
    """Runtime metadata helper. Callers must keep this OUT of deterministic
    artifacts (use for logs/console only)."""
    return datetime.now(timezone.utc).isoformat()
