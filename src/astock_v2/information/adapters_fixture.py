"""Deterministic fixture adapters for the four representative sources.

All payloads are embedded constants; fetch() returns them unchanged, so
CI is fully offline and byte-identical. The adapters use the P14-A source
registry categories and never fabricate availability.
"""
from __future__ import annotations

from .adapters import AdapterMetadata, SourceAdapter
from .raw_store import RawIngestRecord
from .registry import SOURCE_REGISTRY

ADAPTER_VERSION = "1"


class _FixtureAdapter(SourceAdapter):
    """Shared plumbing: subclass supplies payloads + a parse hook."""

    def __init__(self, payloads: list[dict]):
        self._payloads = payloads

    def fetch(self) -> list[dict]:
        return list(self._payloads)


class CNIndexDailyAdapter(_FixtureAdapter):
    metadata = AdapterMetadata(
        source="cn_index_daily",
        source_category=SOURCE_REGISTRY["cn_index_daily"].source_category.value,
        adapter_version=f"cn_index_daily_adapter@{ADAPTER_VERSION}",
        timestamp_semantics="event_time=bar close time; available_time=vendor "
                            "publication time (same day 16:00 +08:00)",
        revision_semantics="vendor may republish; monotone revisions",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def parse(self, payload: dict) -> RawIngestRecord:
        return RawIngestRecord(
            source=self.metadata.source,
            source_id=payload["source_id"],
            source_category=self.metadata.source_category,
            entity_id=payload["entity_id"],
            entity_type="INDEX",
            symbol=payload.get("symbol"),
            event_time=payload["event_time"],
            available_time=payload.get("available_time"),
            revision=payload.get("revision", 0),
            ingested_at=payload["ingested_at"],
            raw_payload=dict(payload),
            adapter_version=self.metadata.adapter_version,
            value=payload.get("close"),
            unit="points",
        )


class CompanyAnnouncementAdapter(_FixtureAdapter):
    metadata = AdapterMetadata(
        source="company_announcement",
        source_category=SOURCE_REGISTRY["company_announcement"].source_category.value,
        adapter_version=f"company_announcement_adapter@{ADAPTER_VERSION}",
        timestamp_semantics="event_time=announcement event; available_time="
                            "exchange publication time",
        revision_semantics="announcements are append-only (revision 0)",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def parse(self, payload: dict) -> RawIngestRecord:
        return RawIngestRecord(
            source=self.metadata.source,
            source_id=payload["source_id"],
            source_category=self.metadata.source_category,
            entity_id=payload["entity_id"],
            entity_type="LISTED_COMPANY",
            symbol=payload.get("symbol"),
            event_time=payload["event_time"],
            available_time=payload.get("available_time"),
            revision=payload.get("revision", 0),
            ingested_at=payload["ingested_at"],
            raw_payload=dict(payload),
            adapter_version=self.metadata.adapter_version,
            content=payload.get("content"),
        )


class MacroPMICNAdapter(_FixtureAdapter):
    metadata = AdapterMetadata(
        source="macro_pmi_cn",
        source_category=SOURCE_REGISTRY["macro_pmi_cn"].source_category.value,
        adapter_version=f"macro_pmi_cn_adapter@{ADAPTER_VERSION}",
        timestamp_semantics="event_time=reference month end; available_time="
                            "NBS release time",
        revision_semantics="initial release revision 0; revisions appended "
                           "with their own release dates",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def parse(self, payload: dict) -> RawIngestRecord:
        return RawIngestRecord(
            source=self.metadata.source,
            source_id=payload["source_id"],
            source_category=self.metadata.source_category,
            entity_id=payload["entity_id"],
            entity_type="ECONOMY",
            event_time=payload["event_time"],
            available_time=payload.get("available_time"),
            revision=payload.get("revision", 0),
            ingested_at=payload["ingested_at"],
            raw_payload=dict(payload),
            adapter_version=self.metadata.adapter_version,
            value=payload.get("value"),
            unit=payload.get("unit", "index"),
        )


class USIndexDailyAdapter(_FixtureAdapter):
    metadata = AdapterMetadata(
        source="us_index_daily",
        source_category=SOURCE_REGISTRY["us_index_daily"].source_category.value,
        adapter_version=f"us_index_daily_adapter@{ADAPTER_VERSION}",
        timestamp_semantics="event_time=US bar close; available_time=vendor "
                            "publication time",
        revision_semantics="vendor may republish; monotone revisions",
        provenance_requirements=("source", "source_id", "ingested_at"),
    )

    def parse(self, payload: dict) -> RawIngestRecord:
        return RawIngestRecord(
            source=self.metadata.source,
            source_id=payload["source_id"],
            source_category=self.metadata.source_category,
            entity_id=payload["entity_id"],
            entity_type="INDEX",
            event_time=payload["event_time"],
            available_time=payload.get("available_time"),
            revision=payload.get("revision", 0),
            ingested_at=payload["ingested_at"],
            raw_payload=dict(payload),
            adapter_version=self.metadata.adapter_version,
            value=payload.get("close"),
            unit="points",
            currency="USD",
        )


FIXTURE_ADAPTERS: dict[str, SourceAdapter] = {
    adapter.metadata.source: adapter
    for adapter in (
        CNIndexDailyAdapter([]),
        CompanyAnnouncementAdapter([]),
        MacroPMICNAdapter([]),
        USIndexDailyAdapter([]),
    )
}
