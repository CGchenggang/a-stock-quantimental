"""P14-B source adapter contract and deterministic fixture adapters.

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

from dataclasses import dataclass, field
from typing import Callable

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
        SOURCE_ERROR / PARSE_ERROR / AUTH_ERROR / TIMEOUT.
        """
        report = IngestionReport(source=self.metadata.source,
                                 adapter_version=self.metadata.adapter_version)
        try:
            payloads = self.fetch()
        except TimeoutError:
            report.status = TIMEOUT
            report.errors.append("fetch timed out")
            return report
        except PermissionError:
            report.status = AUTH_ERROR
            report.errors.append("fetch not authorized")
            return report
        except Exception as exc:  # noqa: BLE001 - audited as source health
            report.status = SOURCE_ERROR
            report.errors.append(f"fetch failed: {exc}")
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
                continue
            if record.available_time is None:
                # adapter contract: never fabricate availability
                record.__dict__["quality_status"] = "UNRESOLVED"
                record.__dict__["availability_status"] = "available_time_unresolved"
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
        elif parse_failures and accepted_or_duplicate == 0:
            report.status = PARSE_ERROR
        elif parse_failures:
            report.status = PARSE_ERROR  # partial failure is still a failure
        else:
            report.status = EMPTY_SUCCESS if not payloads else "OK"
        return report
