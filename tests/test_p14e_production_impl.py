"""P14-E Production Implementation tests.

Tests the PRODUCTION evidence.py + evidence_store.py modules against the
accepted P14-E Contract semantics. Uses real P14-B RawIngestRecord and
P14-D run_query for authority; no mocks for the core path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from astock_v2.information.evidence import (
    BUNDLE_SCHEMA_VERSION,
    REJECTED_LOWER,
    REJECTED_TIE_NOT_EARLIEST,
    SELECTION_CANONICAL,
    SELECTION_EARLIEST_TIE,
    SELECTION_HIGHEST,
    TRACE_AMBIGUOUS,
    TRACE_IDENTITY_MISMATCH,
    TRACE_NOT_FOUND,
    TRACE_RAW_CORRUPTED,
    canonical_json,
    check_mutation,
    create_bundle,
    evidence_from,
    freeze_bundle,
    validate_bundle,
)
from astock_v2.information.evidence_store import EvidenceStore
from astock_v2.information.raw_store import RawIngestRecord, to_information_record
from astock_v2.information.research_query import ResearchQuery, run_query


def _rec(source="cn_stock_quote", source_id="q-1", entity="600000",
         entity_type="stock", event="2026-03-02T15:00:00+08:00",
         available="2026-03-02T16:00:00+08:00", revision=0,
         ingested="2026-03-02T16:05:00+08:00", payload=None,
         value=1.0, category="A_SHARE_MARKET"):
    return RawIngestRecord(
        source=source, source_id=source_id, source_category=category,
        entity_id=entity, entity_type=entity_type, event_time=event,
        available_time=available, revision=revision, ingested_at=ingested,
        raw_payload=payload if payload is not None else {"v": 1.0},
        value=value, adapter_version="fixture-adapter-v1")


def _query(as_of="2026-03-04T16:00:00+08:00", entity="600000",
           information_type="stock"):
    return {"entity": entity, "information_type": information_type,
            "as_of": as_of}


def _resolve(records, query):
    info = [to_information_record(r) for r in records]
    q = ResearchQuery(**query)
    return run_query(info, q)


# ------------------------------------------------------- evidence identity

def test_evidence_id_deterministic():
    r1 = _rec(payload={"close": 10.0}, value=10.0)
    r2 = _rec(payload={"close": 10.0}, value=10.0)
    assert evidence_from(r1)["evidence_id"] == evidence_from(r2)["evidence_id"]
    # ingested_at excluded
    r3 = _rec(payload={"close": 10.0}, ingested="2026-03-03T12:00:00+08:00")
    assert evidence_from(r3)["evidence_id"] == evidence_from(r1)["evidence_id"]


def test_evidence_id_changes_with_payload():
    r1 = _rec(payload={"close": 10.0}, value=10.0)
    r2 = _rec(payload={"close": 99.0}, value=99.0)
    assert evidence_from(r1)["evidence_id"] != evidence_from(r2)["evidence_id"]


# ------------------------------------------------------- bundle construction

def test_bundle_creation_and_structure():
    records = [_rec("cn_stock_quote", "q-1", payload={"close": 10.0}, value=10.0),
               _rec("cn_stock_quote", "q-2", event="2026-03-03T15:00:00+08:00",
                    available="2026-03-03T16:00:00+08:00")]
    result = _resolve(records, _query())
    bundle = create_bundle(result, records)
    assert bundle["schema_version"] == BUNDLE_SCHEMA_VERSION
    assert bundle["counts"]["evidence"] == 2
    assert bundle["result_id"] == result["result_id"]


def test_freeze_bundle_is_copy():
    r = [_rec()]
    result = _resolve(r, _query())
    b = create_bundle(result, r)
    frozen = freeze_bundle(b)
    assert frozen == b
    frozen["evidence"] = []
    assert b["evidence"]


def test_validate_bundle():
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    validate_bundle(b, result)


# ------------------------------------------------------- reverse trace

def test_reverse_trace_not_found():
    records = [_rec()]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    ev = b["evidence"][0]
    from astock_v2.information.evidence import reverse_trace_resolve
    with pytest.raises(ValueError, match="NOT_FOUND"):
        reverse_trace_resolve(ev, [])


def test_reverse_trace_ambiguous():
    records = [_rec()]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    ev = b["evidence"][0]
    row = {"record": json.loads(canonical_json(records[0].as_dict())),
           "outcome": "ACCEPTED"}
    from astock_v2.information.evidence import reverse_trace_resolve
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        reverse_trace_resolve(ev, [row, row])


def test_reverse_trace_identity_mismatch():
    records = [_rec("cn_stock_quote", "q-orig")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    ev = b["evidence"][0]
    row = {"record": dict(records[0].as_dict()), "outcome": "ACCEPTED"}
    row["record"]["source_id"] = "q-different"
    from astock_v2.information.evidence import reverse_trace_resolve
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        reverse_trace_resolve(ev, [row])


# ------------------------------------------------------- persistence

def test_store_append_and_reload(tmp_path):
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl")
    assert store.append(b) is True
    assert store.append(b) is False
    reloaded = store.reload()
    assert len(reloaded) == 1
    assert reloaded[0]["bundle_id"] == b["bundle_id"]


def test_store_detects_tamper(tmp_path):
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec()]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl")
    store.append(b)
    # tamper: inject garbage
    store.path.write_text("{broken json\n", encoding="utf-8")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        store.reload()


# ------------------------------------------------------- mutation detection

def test_mutation_detection():
    r1 = _rec("cn_stock_quote", "q-mut", payload={"close": 10.0}, value=10.0)
    r2 = _rec("cn_stock_quote", "q-mut", payload={"close": 99.0}, value=99.0)
    with pytest.raises(ValueError, match="mutation"):
        check_mutation([r1, r2])


def test_no_mutation_same_payload():
    r1 = _rec("cn_stock_quote", "q-ok", payload={"close": 10.0}, value=10.0)
    r2 = _rec("cn_stock_quote", "q-ok", payload={"close": 10.0}, value=10.0)
    check_mutation([r1, r2])


# ------------------------------------------------------- selection chain

def test_selection_highest_revision():
    records = [_rec("macro_pmi_cn", "m-1", revision=0, category="MACRO"),
               _rec("macro_pmi_cn", "m-1", revision=1, category="MACRO",
                    event="2026-03-03T15:00:00+08:00",
                    available="2026-03-03T16:00:00+08:00")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    assert b["evidence"][0]["revision"] == 1
    assert b["evidence"][0]["selection_reason"] == SELECTION_HIGHEST


def test_selection_earliest_on_revision_tie():
    records = [_rec("macro_pmi_cn", "m-tie", revision=1,
                    available="2026-03-03T16:00:00+08:00",
                    ingested="2026-03-02T16:05:00+08:00", category="MACRO"),
               _rec("macro_pmi_cn", "m-tie", revision=1,
                    available="2026-03-04T16:00:00+08:00",
                    ingested="2026-03-02T17:05:00+08:00", category="MACRO")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    assert b["evidence"][0]["available_time"] == "2026-03-03T16:00:00+08:00"
    assert b["evidence"][0]["selection_reason"] == SELECTION_EARLIEST_TIE


def test_selection_canonical_tiebreak():
    """Same key + same payload (same hash → not mutation) + different
    ingested_at → canonical_json differs → smallest canonical_json wins."""
    r1 = _rec("cn_stock_quote", "q-ct", payload={"v": 1.0},
              ingested="2026-03-02T16:05:00+08:00")
    r2 = _rec("cn_stock_quote", "q-ct", payload={"v": 1.0},
              ingested="2026-03-02T17:05:00+08:00")
    result = _resolve([r1, r2], _query())
    b = create_bundle(result, [r1, r2])
    ev = b["evidence"][0]
    assert ev["ingested_at"] == "2026-03-02T16:05:00+08:00"


# ------------------------------------------------------- P14-E-PI-010
# Architecture regression: P14-E does NOT re-run P14-D selection

def test_p14e_does_not_rerun_p14d_selection():
    """Monkey-patch run_query to raise. create_bundle must succeed
    because it consumes the already-resolved result, not the raw query."""
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    original = run_query
    import astock_v2.information.research_query as rq_mod
    rq_mod.run_query = lambda *a, **kw: (_ for _ in ()).throw(
        RuntimeError("P14-E must not re-execute P14-D run_query"))
    try:
        b = create_bundle(result, records)
        assert b["counts"]["evidence"] == 1
    finally:
        rq_mod.run_query = original


# ------------------------------------------------------- exclusion handling

def test_exclusions_carried_through():
    records = [_rec("cn_stock_quote", "q-vis"),
               _rec("cn_stock_quote", "q-future",
                    event="2026-03-03T15:00:00+08:00",
                    available="2026-03-09T16:00:00+08:00")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    assert b["counts"]["exclusions"] == 1
    assert b["exclusions"][0]["reason"] == "NOT_YET_AVAILABLE"
    assert b["exclusions"][0]["source_id"] == "q-future"


# ------------------------------------------------------- determinism

def test_bundle_determinism():
    records = [_rec("cn_stock_quote", "q-1"),
               _rec("macro_pmi_cn", "m-1", entity="600000",
                    entity_type="stock", category="MACRO")]
    result1 = _resolve(records, _query())
    b1 = create_bundle(result1, records)
    result2 = _resolve(list(reversed(records)), _query())
    b2 = create_bundle(result2, list(reversed(records)))
    assert b1["bundle_id"] == b2["bundle_id"]
    assert canonical_json(b1) == canonical_json(b2)
