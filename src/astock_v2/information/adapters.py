"""P14-B source adapter contract, deterministic fixture adapters, and
the real local-historical-store adapter (R3-A).

An adapter turns one external source's payloads into raw ingest records
and an honest ingestion report. Adapters never decide research
admissibility and never invent timestamps:

- ``event_time``: the source's own event timestamp (verbatim semantics).
- ``available_time``: the source's publication/availability timestamp when
  the source contract provides one; otherwise UNRESOLVED — adapters must
  not fall back to event_time or ingested_at.
- ``ingested_at``: supplied by the ingestion caller (when this system
  stored it); fixtures pin it deterministically.

Every record and report carries ``adapter_version`` so historical raw
records are never misattributed to a newer adapter.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from ..data.local_store import LocalHistoricalStore  # noqa: F401 (R3-A adapter input)
from .registry import SOURCE_REGISTRY
from .raw_store import RawIngestRecord

# deterministic source-health statuses (handoff §18)
EMPTY_SUCCESS = "EMPTY_SUCCESS"
SOURCE_ERROR = "SOURCE_ERROR"
PARSE_ERROR = "PARSE_ERROR"
AUTH_ERROR = "AUTH_ERROR"
TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class AdapterMetadata:
    source: str
    source_category: str
    adapter_version: str
    timestamp_semantics: str
    revision_semantics: str
    provenance_requirements: tuple[str, ...]


@dataclass
class ParseResult:
    """One parsed payload: a raw record or a tracked failure."""

    record: RawIngestRecord | None = None
    error: str | None = None


@dataclass
class IngestionReport:
    """Per-source ingestion audit (handoff §17): attempted vs accepted vs
    rejected vs failed, duplicates and source health — nothing silent."""

    source: str
    adapter_version: str
    status: str = "PENDING"
    attempted: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    mutations: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "adapter_version": self.adapter_version,
            "status": self.status,
            "attempted": self.attempted,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "duplicates": self.duplicates,
            "mutations": self.mutations,
            "errors": list(self.errors),
        }


class SourceAdapter:
    """Base adapter: parse payloads into raw records via a subclass hook."""

    metadata: AdapterMetadata

    def fetch(self) -> list[dict]:
        """Return raw source payloads (deterministic in fixture adapters)."""
        raise NotImplementedError

    def parse(self, payload: dict) -> RawIngestRecord:
        """One source payload -> one RawIngestRecord (subclass hook)."""
        raise NotImplementedError

    def ingest(self, store, ingested_at: str) -> IngestionReport:
        """Fetch -> parse -> store, with a complete per-source report.

        Partial failure is audited: attempted = accepted + rejected +
        failed; the source health status distinguishes EMPTY_SUCCESS /
        SOURCE_ERROR / PARSE_ERROR / AUTH_ERROR / TIMEOUT. Every attempt —
        including failures — is durably audited via the store's audit log.
        """
        report = IngestionReport(source=self.metadata.source,
                                 adapter_version=self.metadata.adapter_version)
        try:
            payloads = self.fetch()
        except TimeoutError:
            report.status = TIMEOUT
            store.audit_event({"outcome": TIMEOUT, "source": self.metadata.source,
                               "adapter_version": self.metadata.adapter_version,
                               "error": "fetch timed out"})
            return report
        except PermissionError:
            report.status = AUTH_ERROR
            store.audit_event({"outcome": AUTH_ERROR, "source": self.metadata.source,
                               "adapter_version": self.metadata.adapter_version,
                               "error": "fetch not authorized"})
            return report
        except Exception as exc:  # noqa: BLE001 - audited as source health
            report.status = SOURCE_ERROR
            store.audit_event({"outcome": SOURCE_ERROR, "source": self.metadata.source,
                               "adapter_version": self.metadata.adapter_version,
                               "error": f"fetch failed: {exc}"})
            return report

        report.attempted = len(payloads)
        accepted_or_duplicate = 0
        parse_failures = 0
        for index, payload in enumerate(payloads):
            try:
                record = self.parse(payload)
            except Exception as exc:  # noqa: BLE001 - tracked parse failure
                parse_failures += 1
                report.errors.append(f"parse failed for payload[{index}]: {exc}")
                store.audit_event({
                    "outcome": "REJECTED",
                    "source": self.metadata.source,
                    "source_id": str(payload.get("source_id")),
                    "revision": int(payload.get("revision", 0)),
                    "adapter_version": self.metadata.adapter_version,
                    "error": f"parse failed for payload[{index}]: {exc}",
                    "payload_index": index,
                })
                continue
            outcome = store.put(record)
            if outcome == "ACCEPTED":
                report.accepted += 1
                accepted_or_duplicate += 1
            elif outcome == "DUPLICATE":
                report.duplicates += 1
                accepted_or_duplicate += 1
            elif outcome == "RAW_MUTATION_DETECTED":
                report.mutations += 1
                report.errors.append(
                    f"raw mutation detected for {record.source_id} "
                    f"rev{record.revision}"
                )
            else:  # pragma: no cover - defensive
                report.errors.append(f"unknown store outcome: {outcome}")
        report.rejected = parse_failures
        if not payloads:
            report.status = EMPTY_SUCCESS
        elif parse_failures:
            report.status = PARSE_ERROR  # partial failure is still a failure
        else:
            report.status = "OK"
        return report


# ---------------------------------------------------------------------------
# Real source adapters (R3-A)
# ---------------------------------------------------------------------------


HISTORICAL_ADAPTER_VERSION = "1"


def _canonical_row(record) -> dict:
    """HistoricalRecord -> JSON-primitive dict (deterministic, sorted)."""
    return json.loads(json.dumps(
        asdict(record), ensure_ascii=False, sort_keys=True,
        default=lambda o: o.value if hasattr(o, "value") else str(o),
    ))


class CNStockQuoteHistoricalAdapter(SourceAdapter):
    """Ingest local daily-history rows as ``cn_stock_quote`` records.

    One store row (one symbol, one trade date) becomes one raw record;
    distinct trade dates are distinct information events with their own
    ``source_id``, exactly like the P14-D lineage contract expects.

    Source identity: ``cn_stock_quote`` — already registered in the P14-A
    ``SOURCE_REGISTRY`` (A_SHARE_MARKET category, ``market_daily`` freshness
    policy). No registry change. Availability is carried VERBATIM from the
    store row's declared vendor publication time (trade day 16:00 +08:00,
    mandated by ``data/local_store.py``) — never derived or back-filled.
    ``ingested_at`` is supplied by the ingestion caller per the adapter
    contract and is deliberately kept OUT of ``raw_payload``: re-ingesting
    the same store data under a different ingestion run stays DUPLICATE
    (not RAW_MUTATION_DETECTED) and evidence identity stays stable
    (P14E-001). The adapter never decides research admissibility.
    """

    metadata = AdapterMetadata(
        source="cn_stock_quote",
        source_category=SOURCE_REGISTRY["cn_stock_quote"].source_category.value,
        adapter_version=f"cn_stock_quote_historical_adapter@{HISTORICAL_ADAPTER_VERSION}",
        timestamp_semantics=(
            "event_time=bar trade-date close (15:00 +08:00); available_time="
            "carried VERBATIM from the local store row's declared vendor "
            "publication time (trade day 16:00 +08:00, mandated by "
            "data/local_store.py) — never derived or back-filled"),
        revision_semantics=(
            "store rows are append-only revision 0; the same "
            "(source, source_id, revision) key with different content is a "
            "store-level RAW_MUTATION_DETECTED"),
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def __init__(self, store, dataset: str = "cn_stock_daily",
                 symbols: Sequence[str] | None = None,
                 ingested_at: str = "1970-01-01T00:00:00+00:00"):
        self._store = store
        self._dataset = dataset
        self._symbols = list(symbols) if symbols is not None else None
        self.ingested_at = ingested_at

    def ingest(self, store, ingested_at: str):
        """Pin the caller-supplied ingestion timestamp, then run the
        inherited fetch -> parse -> store pipeline unchanged."""
        self.ingested_at = ingested_at
        return super().ingest(store, ingested_at)

    def _symbols_in_scope(self) -> list[str]:
        if self._symbols is not None:
            return sorted(self._symbols)
        dataset_dir = Path(self._store.record_path(self._dataset, "_")).parent
        if not dataset_dir.exists():
            return []
        return sorted(p.stem for p in dataset_dir.glob("*.jsonl"))

    def fetch(self) -> list[dict]:
        payloads: list[dict] = []
        for symbol in self._symbols_in_scope():
            for record in self._store.read_records(self._dataset, symbol):
                payloads.append(_canonical_row(record))
        payloads.sort(key=lambda p: (p["symbol"], p["event_time"],
                                     p.get("revision", 0)))
        return payloads

    def parse(self, payload: dict) -> RawIngestRecord:
        if not payload.get("available_time"):
            raise ValueError(
                "local historical row without available_time violates the "
                "store contract (data/local_store.py mandates explicit "
                "availability); refusing to invent one")
        value = payload.get("value") or {}
        return RawIngestRecord(
            source=self.metadata.source,
            source_id=f"{payload['symbol']}:{payload['event_time']}",
            source_category=self.metadata.source_category,
            entity_id=payload["symbol"],
            entity_type="STOCK",
            symbol=payload["symbol"],
            event_time=payload["event_time"],
            available_time=payload["available_time"],
            revision=int(payload.get("revision", 0)),
            ingested_at=self.ingested_at,
            raw_payload=dict(payload),
            adapter_version=self.metadata.adapter_version,
            value=value.get("close"),
            unit="CNY",
            currency="CNY",
        )
