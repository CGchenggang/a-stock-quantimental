"""P14-D Acceptance Harness — behavioral checks P14D-001..010.

Each test drives the PRODUCTION query layer (run_query / ResearchQuery)
and proves one frozen contract invariant. Expected values are hand-written
here and in the golden fixtures — never derived from the implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from astock_v2.information.models import RawInformationRecord  # noqa: E402
from astock_v2.information.research_query import (  # noqa: E402
    EXCLUSION_NOT_YET_AVAILABLE,
    EXCLUSION_OUTSIDE_AS_OF,
    PROVENANCE_FIELDS,
    ResearchQuery,
    run_query,
)


def _record(source, source_id, entity="600000", entity_type="stock",
            event="2026-03-02T15:00:00+08:00",
            available="2026-03-02T16:00:00+08:00", revision=0,
            metadata=None):
    return RawInformationRecord(
        source=source, source_id=source_id, source_category="A_SHARE_MARKET",
        entity_id=entity, entity_type=entity_type, event_time=event,
        available_time=available, revision=revision,
        ingested_at=available, value=1.0, quality_status="OK",
        freshness_policy_id="market_daily", metadata=metadata or {})


def _query(as_of="2026-03-04T15:00:00+08:00", **kw):
    return ResearchQuery(entity=kw.get("entity", "600000"),
                         information_type=kw.get("information_type", "stock"),
                         as_of=as_of, source=kw.get("source"))


def _visible_source_ids(result):
    return [r["source_record_id"] for r in result["records"]]


def test_p14d_001_normal_pit():
    records = [_record("cn_stock_quote", "q-1"),
               _record("cn_stock_quote", "q-2",
                       event="2026-03-03T15:00:00+08:00",
                       available="2026-03-03T16:00:00+08:00")]
    result = run_query(records, _query())
    assert _visible_source_ids(result) == ["q-1", "q-2"]
    assert result["counts"] == {"visible": 2, "excluded": 0, "examined": 2}


def test_p14d_002_future_hidden():
    records = [_record("cn_stock_quote", "q-f",
                       available="2026-03-05T09:00:00+08:00")]
    result = run_query(records, _query())
    assert result["records"] == []
    assert result["excluded"] == [{
        "source": "cn_stock_quote", "source_id": "q-f",
        "reason": EXCLUSION_NOT_YET_AVAILABLE,
        "available_time": "2026-03-05T09:00:00+08:00"}]


def test_p14d_003_event_time_never_grants_visibility():
    records = [_record("company_announcement", "ann-x",
                       event="2026-03-01T10:00:00+08:00",   # event <= as_of
                       available="2026-03-11T09:00:00+08:00")]  # avail > as_of
    result = run_query(records, _query(as_of="2026-03-10T15:00:00+08:00"))
    assert result["records"] == []
    assert result["excluded"][0]["reason"] == EXCLUSION_NOT_YET_AVAILABLE


def test_p14d_011_same_revision_tie_earliest_wins():
    """P14-D-REPAIR-001: same (source, source_id, revision) with different
    available_time — the EARLIEST available_time wins once both are
    admissible. Driven through the production run_query."""
    a = _record("TEST", "R-TIE-001", entity="R-TIE-001",
                entity_type="indicator",
                event="2026-02-28T18:00:00+08:00",
                available="2026-03-01T09:00:00+08:00", revision=1)
    b = _record("TEST", "R-TIE-001", entity="R-TIE-001",
                entity_type="indicator",
                event="2026-02-28T18:00:00+08:00",
                available="2026-03-01T10:00:00+08:00", revision=1)
    result = run_query([a, b], _query(as_of="2026-03-01T11:00:00+08:00",
                                      entity="R-TIE-001",
                                      information_type="indicator"))
    assert _visible_source_ids(result) == ["R-TIE-001"]
    assert result["counts"]["visible"] == 1
    assert result["records"][0]["available_time"] == "2026-03-01T09:00:00+08:00"
    assert result["records"][0]["revision"] == 1
    # insertion order must not matter
    result_reversed = run_query([b, a], _query(as_of="2026-03-01T11:00:00+08:00",
                                               entity="R-TIE-001",
                                               information_type="indicator"))
    assert result_reversed["result_id"] == result["result_id"]


def test_p14d_004_deterministic_version_selection():
    records = [_record("macro_pmi_cn", "q-100", revision=0),
               _record("macro_pmi_cn", "q-100",
                       event="2026-03-03T15:00:00+08:00",
                       available="2026-03-03T16:00:00+08:00", revision=1),
               _record("macro_pmi_cn", "q-200")]
    result = run_query(records, _query())
    assert _visible_source_ids(result) == ["q-100", "q-200"]
    revs = {r["source_record_id"]: r["revision"] for r in result["records"]}
    assert revs == {"q-100": 1, "q-200": 0}


def test_p14d_005_restatement_invisible_before_t2():
    t1 = "2026-03-02T16:00:00+08:00"
    t2 = "2026-03-05T09:00:00+08:00"
    records = [_record("macro_pmi_cn", "pmi-m01", entity="CN",
                       entity_type="macro", available=t1, revision=0),
               _record("macro_pmi_cn", "pmi-m01", entity="CN",
                       entity_type="macro", available=t2, revision=1)]
    before = run_query(records, _query(as_of="2026-03-03T15:00:00+08:00",
                                       entity="CN", information_type="macro"))
    # as_of in [T1, T2): only the original version is visible
    assert _visible_source_ids(before) == ["pmi-m01"]
    assert before["records"][0]["revision"] == 0
    at = run_query(records, _query(as_of="2026-03-05T09:00:00+08:00",
                                   entity="CN", information_type="macro"))
    # as_of >= T2: the restated version is the visible one
    assert at["records"][0]["revision"] == 1


def test_p14d_006_deterministic_result():
    records = [_record("cn_stock_quote", "q-1"),
               _record("macro_pmi_cn", "m-1", entity="600000")]
    q = _query()
    r1 = run_query(list(reversed(records)), q)
    r2 = run_query(records, q)
    assert r1 == r2
    assert r1["result_id"] == r2["result_id"]
    assert len(r1["result_id"]) == 64  # sha256 hex


def test_p14d_007_provenance_complete():
    records = [_record("company_announcement", "ann-7",
                       metadata={"adapter_version": "ann-adapter@1",
                                 "raw_payload_hash": "hash-ann-7",
                                 "ingestion_id": "ing-ann-7"})]
    result = run_query(records, _query())
    assert len(result["records"]) == 1
    record = result["records"][0]
    assert tuple(sorted(record)) == tuple(sorted(PROVENANCE_FIELDS))
    assert record["source"] == "company_announcement"
    assert record["source_record_id"] == "ann-7"
    assert record["raw_payload_hash"] == "hash-ann-7"
    assert record["ingestion_id"] == "ing-ann-7"
    assert record["available_time"] == "2026-03-02T16:00:00+08:00"


def test_p14d_008_out_of_scope_never_leaks():
    records = [_record("cn_stock_quote", "q-1", entity="600001"),      # other entity
               _record("macro_pmi_cn", "m-1", entity="600000",
                       entity_type="macro"),                        # other type
               _record("us_index_daily", "u-1"),                    # other source
               _record("cn_stock_quote", "q-2")]                    # in scope
    result = run_query(records, _query(source="cn_stock_quote"))
    assert _visible_source_ids(result) == ["q-2"]
    reasons = {e["source_id"]: e["reason"] for e in result["excluded"]}
    assert reasons == {"q-1": EXCLUSION_OUTSIDE_AS_OF,
                       "m-1": EXCLUSION_OUTSIDE_AS_OF,
                       "u-1": EXCLUSION_OUTSIDE_AS_OF}


def test_p14d_009_virgin_zone_guard_raises():
    # synthetic far-future date proves the P13-U guard fires on the query
    # entry point; no real virgin data is involved anywhere
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
        _query(as_of="2099-01-01T00:00:00+08:00")


def test_p14d_010_query_layer_is_infrastructure_only():
    """The query result schema carries information retrieval fields only —
    no score / recommendation / decision surface exists."""
    result = run_query([_record("cn_stock_quote", "q-1")], _query())
    allowed_record_fields = set(PROVENANCE_FIELDS)
    assert set(result["records"][0]) <= allowed_record_fields
    assert set(result) == {"query", "records", "excluded", "counts", "result_id"}
    assert set(result["counts"]) == {"visible", "excluded", "examined"}


# boundary: inclusive visibility at available_time == as_of
def test_boundary_timestamp_inclusive():
    records = [_record("cn_stock_quote", "q-edge",
                       event="2026-03-03T15:00:00+08:00",
                       available="2026-03-03T16:00:00+08:00")]
    result = run_query(records, _query(as_of="2026-03-03T16:00:00+08:00"))
    assert _visible_source_ids(result) == ["q-edge"]


# unresolved availability (P14-C taxonomy reuse) is never visible: the
# P14-A model rejects records without a parseable available_time outright
# (proven above), and run_query's defensive branch excludes anything whose
# available_time cannot be parsed — exercised here via a minimal stub
def test_unresolved_availability_never_visible():
    from dataclasses import dataclass, field

    from astock_v2.information.research_query import EXCLUSION_UNRESOLVED_AVAILABILITY
    with pytest.raises(ValueError, match="available_time"):
        RawInformationRecord(
            source="cn_stock_quote", source_id="q-u",
            source_category="A_SHARE_MARKET", entity_id="600000",
            entity_type="stock", event_time="2026-03-02T15:00:00+08:00",
            available_time="", revision=0,
            ingested_at="2026-03-02T16:00:00+08:00", value=1.0)

    @dataclass(frozen=True)
    class _UnparseableRecord:
        """Minimal record-shaped stub whose available_time is non-empty
        but carries no timezone — unreachable via the frozen model, so the
        stub exercises run_query's defensive exclusion branch only."""

        def __getattr__(self, name):
            raise AttributeError(name)

        source = "cn_stock_quote"
        source_id = "q-bad"
        entity_id = "600000"
        entity_type = "stock"
        event_time = "2026-03-02T15:00:00+08:00"
        available_time = "2026-03-02T16:00:00"   # no timezone
        revision = 0

        def canonical_json(self):
            return '{"source_id": "q-bad"}'

    result = run_query([_UnparseableRecord()], _query())
    assert result["records"] == []
    assert result["excluded"][0]["reason"] == EXCLUSION_UNRESOLVED_AVAILABILITY
    assert result["excluded"][0]["source_id"] == "q-bad"


# malformed query construction fails fast
def test_query_validation():
    with pytest.raises(ValueError):
        _query(entity="")
    with pytest.raises(ValueError):
        _query(as_of="2026-03-04T15:00:00")  # no timezone
