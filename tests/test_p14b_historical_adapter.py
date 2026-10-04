"""R3-A tests: local historical store -> P14-B real source adapter.

All fixtures are built in tmp_path through the store's own API — no
gitignored data file is ever read, so the suite is CI-offline and
byte-identical. Locks the R3-A invariants:

- source identity is the REGISTERED ``cn_stock_quote`` (no registry change);
- ``available_time`` is carried verbatim from the store row (never derived,
  never back-filled; missing availability is rejected, not invented);
- ``ingested_at`` never enters ``raw_payload`` (re-ingestion under a new
  ingestion run stays DUPLICATE, evidence identity stays stable);
- ingestion is idempotent / mutation-detecting via the accepted RawStore;
- the accepted PIT chain (to_information_record -> run_query) sees real
  daily bars with inclusive-boundary visibility and post-availability
  exclusion (P14-D authority; the adapter decides nothing).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.information.adapters import (
    CNStockQuoteHistoricalAdapter,
)
from astock_v2.information.normalization import normalize
from astock_v2.information.raw_store import RawStore, to_information_record
from astock_v2.information.registry import SOURCE_REGISTRY
from astock_v2.information.research_query import ResearchQuery, run_query

INGESTED_AT = "2026-03-01T00:00:00+08:00"


def _row(symbol="000001", day="2020-01-02", close=16.87, revision=0):
    return HistoricalRecord(
        symbol=symbol,
        event_time=f"{day}T15:00:00+08:00",
        available_time=f"{day}T16:00:00+08:00",
        source="akshare:stock_zh_a_hist_tx",
        source_type="historical_vendor",
        value={"date": day, "open": close - 0.2, "close": close,
               "high": close + 0.1, "low": close - 0.3, "volume": 1000.0,
               "amount": None, "adjust": ""},
        layer=DataLayer.CLEAN,
        asset_scope=AssetScope.CN_STOCK,
        revision=revision,
        raw_ref="a" * 64,
        quality="SOURCE_RETURNED",
    )


def _store(tmp_path: Path, rows) -> LocalHistoricalStore:
    store = LocalHistoricalStore(root=tmp_path)
    store.append_records("cn_stock_daily", rows)
    return store


def _adapter(tmp_path: Path, rows, **kwargs) -> CNStockQuoteHistoricalAdapter:
    return CNStockQuoteHistoricalAdapter(
        _store(tmp_path, rows), ingested_at=INGESTED_AT, **kwargs)


# ----------------------------------------------------------- source identity

def test_metadata_uses_registered_source():
    assert "cn_stock_quote" in SOURCE_REGISTRY
    adapter = CNStockQuoteHistoricalAdapter(LocalHistoricalStore(root="data"))
    assert adapter.metadata.source == "cn_stock_quote"
    assert (adapter.metadata.source_category
            == SOURCE_REGISTRY["cn_stock_quote"].source_category.value)
    assert adapter.metadata.source_category == "A_SHARE_MARKET"
    assert (adapter.metadata.adapter_version
            == "cn_stock_quote_historical_adapter@1")
    assert adapter.metadata.provenance_requirements == (
        "source", "source_id", "ingested_at")


# ------------------------------------------------------------ fetch behavior

def test_fetch_returns_store_rows_verbatim_and_sorted(tmp_path):
    rows = [_row(close=16.87), _row(day="2020-01-03", close=17.18),
            _row(symbol="000002", day="2020-01-02", close=11.0)]
    adapter = _adapter(tmp_path, rows)
    payloads = adapter.fetch()
    assert [p["symbol"] for p in payloads] == ["000001", "000001", "000002"]
    assert payloads[0]["event_time"] == "2020-01-02T15:00:00+08:00"
    assert payloads[0]["available_time"] == "2020-01-02T16:00:00+08:00"
    assert payloads[0]["value"]["close"] == 16.87
    assert payloads[0]["source"] == "akshare:stock_zh_a_hist_tx"
    assert payloads[0]["raw_ref"] == "a" * 64


def test_fetch_is_deterministic(tmp_path):
    rows = [_row(), _row(day="2020-01-03"), _row(day="2020-01-06")]
    first = json.dumps(_adapter(tmp_path, rows).fetch(), sort_keys=True)
    second = json.dumps(_adapter(tmp_path, rows).fetch(), sort_keys=True)
    assert first == second


def test_symbol_scope_filter(tmp_path):
    rows = [_row(), _row(symbol="000002")]
    scoped = _adapter(tmp_path, rows, symbols=["000002"])
    assert [p["symbol"] for p in scoped.fetch()] == ["000002"]


# ------------------------------------------------------------ parse behavior

def test_parse_carries_availability_verbatim(tmp_path):
    rows = [_row()]
    record = _adapter(tmp_path, rows).parse(_adapter(tmp_path, rows).fetch()[0])
    assert record.source == "cn_stock_quote"
    assert record.source_id == "000001:2020-01-02T15:00:00+08:00"
    assert record.entity_id == "000001"
    assert record.entity_type == "STOCK"
    assert record.event_time == "2020-01-02T15:00:00+08:00"
    # verbatim from the store row — not event_time, not ingested_at
    assert record.available_time == "2020-01-02T16:00:00+08:00"
    assert record.availability_status == "RESOLVED"
    assert record.quality_status == "OK"
    assert record.value == 16.87
    assert record.ingested_at == INGESTED_AT
    assert record.adapter_version == "cn_stock_quote_historical_adapter@1"


def test_raw_payload_is_the_store_row_without_ingested_at(tmp_path):
    rows = [_row()]
    adapter = _adapter(tmp_path, rows)
    payload = adapter.fetch()[0]
    record = adapter.parse(payload)
    assert record.raw_payload == payload
    assert "ingested_at" not in record.raw_payload


def test_parse_rejects_row_without_available_time(tmp_path):
    rows = [_row()]
    adapter = _adapter(tmp_path, rows)
    payload = adapter.fetch()[0]
    del payload["available_time"]
    with pytest.raises(ValueError, match="available_time"):
        adapter.parse(payload)


# ---------------------------------------------------------- ingestion invariants

def test_ingest_accepts_and_reports(tmp_path):
    rows = [_row(), _row(day="2020-01-03"), _row(day="2020-01-06")]
    adapter = _adapter(tmp_path, rows)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    report = adapter.ingest(raw, INGESTED_AT)
    assert report.status == "OK"
    assert report.attempted == 3
    assert report.accepted == 3
    assert report.duplicates == 0
    assert report.rejected == 0
    assert len(raw.records()) == 3
    assert set(r.source for r in raw.records()) == {"cn_stock_quote"}


def test_ingest_is_idempotent_across_ingestion_runs(tmp_path):
    rows = [_row(), _row(day="2020-01-03")]
    raw = RawStore(tmp_path / "raw_records.jsonl")
    first = _adapter(tmp_path, rows).ingest(raw, INGESTED_AT)
    # a later ingestion run of the SAME store data with a DIFFERENT
    # ingestion timestamp must stay DUPLICATE — never a mutation
    second = _adapter(tmp_path, rows).ingest(
        raw, "2026-06-01T00:00:00+08:00")
    assert first.status == "OK" and first.accepted == 2
    assert second.status == "OK" and second.duplicates == 2
    assert second.accepted == 0 and second.mutations == 0
    assert len(raw.records()) == 2


def test_mutation_detected_on_changed_content(tmp_path):
    rows = [_row()]
    store = _store(tmp_path, rows)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    CNStockQuoteHistoricalAdapter(
        store, ingested_at=INGESTED_AT).ingest(raw, INGESTED_AT)

    class _Tampered(CNStockQuoteHistoricalAdapter):
        def fetch(self):
            payloads = super().fetch()
            payloads[0]["value"]["close"] = 99.0
            return payloads

    report = _Tampered(store, ingested_at=INGESTED_AT).ingest(
        raw, INGESTED_AT)
    assert report.mutations == 1
    assert report.accepted == 0
    # the original record is preserved
    assert len(raw.records()) == 1
    assert raw.records()[0].value == 16.87


def test_durable_audit_reloads(tmp_path):
    rows = [_row()]
    path = tmp_path / "raw_records.jsonl"
    _adapter(tmp_path, rows).ingest(RawStore(path), INGESTED_AT)
    reloaded = RawStore(path)
    outcomes = [o["outcome"] for o in reloaded.outcomes()]
    assert outcomes == ["ACCEPTED"]
    assert len(reloaded.records()) == 1


# ---------------------------------------------------------- empty dataset

def test_empty_dataset_is_empty_success(tmp_path):
    adapter = CNStockQuoteHistoricalAdapter(
        LocalHistoricalStore(root=tmp_path), ingested_at=INGESTED_AT)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    report = adapter.ingest(raw, INGESTED_AT)
    assert report.status == "EMPTY_SUCCESS"
    assert report.attempted == 0


# ---------------------------------------------------------- accepted PIT chain

def test_pit_visibility_e2e(tmp_path):
    days = ["2020-01-02", "2020-01-03", "2020-01-06"]
    adapter = _adapter(tmp_path, [_row(day=d, close=16.0 + i)
                                  for i, d in enumerate(days)])
    raw = RawStore(tmp_path / "raw_records.jsonl")
    adapter.ingest(raw, INGESTED_AT)
    info = [to_information_record(r) for r in raw.records()]

    def _visible(as_of):
        result = run_query(info, ResearchQuery(
            entity="000001", information_type="STOCK", as_of=as_of))
        return result

    # day2's bar becomes visible exactly at its declared 16:00 availability
    result = _visible("2020-01-03T16:00:00+08:00")
    assert result["counts"]["visible"] == 2
    assert result["counts"]["excluded"] == 1
    assert result["excluded"][0]["reason"] == "NOT_YET_AVAILABLE"

    # 15:30 on day1: the day-1 close (15:00) exists but is NOT yet available
    result = _visible("2020-01-02T15:30:00+08:00")
    assert result["counts"]["visible"] == 0
    assert result["excluded"][0]["reason"] == "NOT_YET_AVAILABLE"

    # inclusive boundary: available at 16:00 sharp -> visible at 16:00
    result = _visible("2020-01-02T16:00:00+08:00")
    assert result["counts"]["visible"] == 1


def test_normalize_accepts_registered_source(tmp_path):
    rows = [_row(), _row(day="2020-01-03")]
    adapter = _adapter(tmp_path, rows)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    adapter.ingest(raw, INGESTED_AT)
    info = [to_information_record(r) for r in raw.records()]
    research = normalize(info)
    assert len(research) == 2
    assert all(r.source == "cn_stock_quote" for r in research)
