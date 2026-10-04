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
    REJECTED_CANONICAL,
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
from astock_v2.information.raw_store import (
    RawIngestRecord,
    RawStore,
    to_information_record,
)
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

def _authority(tmp_path, records):
    """P14-B raw authority store pre-loaded with the given records."""
    raw = RawStore(tmp_path / "raw_records.jsonl")
    for r in records:
        raw.put(r)
    return raw


def test_store_append_and_reload(tmp_path):
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    raw = _authority(tmp_path, records)
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl",
                          raw_store_path=raw.path)
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
    raw = _authority(tmp_path, records)
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl",
                          raw_store_path=raw.path)
    store.append(b)
    # tamper: inject garbage
    store.path.write_text("{broken json\n", encoding="utf-8")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        store.reload()


def test_store_requires_raw_authority_path():
    from pathlib import Path as _P
    with pytest.raises(TypeError):
        EvidenceStore(_P("evidence_bundles.jsonl"))


def test_store_reload_fails_without_p14b_authority(tmp_path):
    """REPAIR-001: reload MUST verify P14-B authority — a missing raw
    authority store is a REVERSE_TRACE_NOT_FOUND failure, never a silent
    hash-only pass."""
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec("cn_stock_quote", "q-auth")]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    raw_path = tmp_path / "raw_records.jsonl"
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl",
                          raw_store_path=raw_path)
    assert store.append(b) is True
    # authority file does not exist at all
    with pytest.raises(ValueError, match="REVERSE_TRACE_NOT_FOUND"):
        store.reload()
    # authority file exists but holds no matching row
    raw_path.touch()
    with pytest.raises(ValueError, match="REVERSE_TRACE_NOT_FOUND"):
        store.reload()
    # with the real P14-B authority the same bundle reloads
    raw = _authority(tmp_path, records)
    assert raw.path == raw_path
    reloaded = store.reload()
    assert len(reloaded) == 1
    assert reloaded[0]["bundle_id"] == b["bundle_id"]


def test_store_reload_rejects_mutated_authority(tmp_path):
    """Bundle hash intact but the raw authority row no longer resolves
    (payload mutated elsewhere) → reload fails fast."""
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec("cn_stock_quote", "q-mut-auth",
                    payload={"close": 10.0}, value=10.0)]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    mutated = [_rec("cn_stock_quote", "q-mut-auth",
                    payload={"close": 99.0}, value=99.0)]
    raw = _authority(tmp_path, mutated)
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl",
                          raw_store_path=raw.path)
    store.append(b)
    with pytest.raises(ValueError, match="REVERSE_TRACE_NOT_FOUND"):
        store.reload()


def test_store_reload_rejects_hash_mismatched_authority_row(tmp_path):
    """REPAIR-003 Test E (adversarial row): an authority row carrying the
    right ingestion_id but a non-matching raw_payload_hash cannot
    resolve — reverse trace requires BOTH fields to match."""
    from astock_v2.information.evidence_store import EvidenceStore
    records = [_rec("cn_stock_quote", "q-hm",
                    payload={"close": 10.0}, value=10.0)]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    row = {"record": json.loads(canonical_json(records[0].as_dict())),
           "outcome": "ACCEPTED"}
    row["record"]["raw_payload_hash"] = "0" * 64
    raw_path = tmp_path / "raw_records.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(canonical_json(row) + "\n", encoding="utf-8")
    store = EvidenceStore(tmp_path / "evidence_bundles.jsonl",
                          raw_store_path=raw_path)
    store.append(b)
    with pytest.raises(ValueError, match="REVERSE_TRACE_NOT_FOUND"):
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
    assert len(b["candidate_trace"]) == 1
    assert b["candidate_trace"][0]["rejection_reason"] == REJECTED_TIE_NOT_EARLIEST


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
    assert ev["selection_reason"] == SELECTION_CANONICAL
    assert len(b["candidate_trace"]) == 1
    assert b["candidate_trace"][0]["rejection_reason"] == REJECTED_CANONICAL


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


# --------------------------------------- REPAIR-001: PIT-safe candidate trace
# candidate_trace labels ONLY visible losers; records P14-D excluded
# (post-as_of included) never appear in the bundle beyond the carried
# exclusions.

def test_candidate_trace_pit_safe_no_post_as_of_leak():
    visible = _rec("cn_stock_quote", "q-pit", revision=0,
                   event="2026-03-02T15:00:00+08:00",
                   available="2026-03-02T16:00:00+08:00",
                   ingested="2026-03-02T16:05:00+08:00",
                   payload={"close": 10.0}, value=10.0)
    future = _rec("cn_stock_quote", "q-pit", revision=1,
                  event="2026-03-09T15:00:00+08:00",
                  available="2026-03-09T16:00:00+08:00",
                  ingested="2026-03-09T16:05:00+08:00",
                  payload={"close": 20.0}, value=20.0)
    result = _resolve([visible, future], _query())
    b = create_bundle(result, [visible, future])
    text = canonical_json(b)
    assert b["candidate_trace"] == []
    assert future.raw_payload_hash not in text
    assert future.ingested_at not in text
    assert b["evidence"][0]["revision"] == 0
    assert b["evidence"][0]["selection_reason"] == SELECTION_HIGHEST
    # the future record is represented ONLY by P14-D's resolved exclusion
    assert b["exclusions"] == [
        {"source": "cn_stock_quote", "source_id": "q-pit",
         "reason": "NOT_YET_AVAILABLE",
         "available_time": "2026-03-09T16:00:00+08:00"}]


def test_candidate_trace_labels_only_visible_losers():
    records = [
        _rec("cn_stock_quote", "q-ml", revision=0, payload={"close": 10.0},
             value=10.0),
        _rec("cn_stock_quote", "q-ml", revision=1,
             event="2026-03-03T15:00:00+08:00",
             available="2026-03-03T16:00:00+08:00",
             ingested="2026-03-03T16:05:00+08:00", payload={"close": 11.0},
             value=11.0),
        _rec("cn_stock_quote", "q-ml", revision=2,
             event="2026-03-03T17:00:00+08:00",
             available="2026-03-03T18:00:00+08:00",
             ingested="2026-03-03T18:05:00+08:00", payload={"close": 12.0},
             value=12.0),
    ]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    assert b["evidence"][0]["revision"] == 2
    assert b["evidence"][0]["selection_reason"] == SELECTION_HIGHEST
    reasons = {t["revision"]: t["rejection_reason"]
               for t in b["candidate_trace"]}
    assert reasons == {0: REJECTED_LOWER, 1: REJECTED_LOWER}
    assert b["counts"]["candidates"] == 2


def test_selection_reason_not_mislabeled_by_future_revision():
    """Regression: the reason must come from the visible candidates P14-D
    resolved, not from the full lineage — a future revision must not flip
    the label away from SELECTED_HIGHEST_REVISION."""
    visible = _rec("macro_pmi_cn", "m-fut", revision=1, category="MACRO",
                   event="2026-03-02T15:00:00+08:00",
                   available="2026-03-02T16:00:00+08:00",
                   payload={"v": 1.0})
    future = _rec("macro_pmi_cn", "m-fut", revision=2, category="MACRO",
                  event="2026-03-09T15:00:00+08:00",
                  available="2026-03-09T16:00:00+08:00",
                  ingested="2026-03-09T16:05:00+08:00",
                  payload={"v": 2.0})
    result = _resolve([visible, future], _query())
    b = create_bundle(result, [visible, future])
    assert b["evidence"][0]["selection_reason"] == SELECTION_HIGHEST
    assert b["candidate_trace"] == []


# --------------------------------- REPAIR-001: no PIT/selection re-execution

def test_create_bundle_never_executes_pit_or_selection(monkeypatch):
    """Architecture regression: no PIT / selection entry point executes
    anywhere inside create_bundle — even with post-as-of siblings."""
    import astock_v2.information.pit as pit_mod
    import astock_v2.information.research_query as rq_mod
    records = [
        _rec("cn_stock_quote", "q-noexec", revision=0,
             payload={"close": 10.0}, value=10.0),
        _rec("cn_stock_quote", "q-noexec", revision=1,
             event="2026-03-09T15:00:00+08:00",
             available="2026-03-09T16:00:00+08:00",
             ingested="2026-03-09T16:05:00+08:00", payload={"close": 20.0},
             value=20.0),
    ]
    result = _resolve(records, _query())  # resolve BEFORE patching

    def _boom(*args, **kwargs):
        raise RuntimeError("P14-E executed PIT/selection logic")

    monkeypatch.setattr(pit_mod, "is_admissible", _boom)
    monkeypatch.setattr(pit_mod, "visible_revisions", _boom)
    monkeypatch.setattr(pit_mod, "admissible_records", _boom)
    monkeypatch.setattr(pit_mod, "resolve_selection", _boom)
    monkeypatch.setattr(rq_mod, "run_query", _boom)
    b = create_bundle(result, records)
    assert b["counts"]["evidence"] == 1
    assert b["candidate_trace"] == []


def test_evidence_source_has_no_pit_or_selection_calls():
    """Static surface: the production evidence module contains no call
    form of any PIT/selection entry point."""
    import astock_v2.information.evidence as ev_mod
    text = Path(ev_mod.__file__).read_text(encoding="utf-8")
    for token in ("is_admissible(", "visible_revisions(",
                  "select_lineage(", "run_query(", "admissible_records(",
                  "resolve_selection("):
        assert token not in text, token


# ----------------------------------- REPAIR-002: pure consumption of the
# resolved selection/rejection state

def test_create_bundle_requires_selected_record_in_authority():
    """P14-E consumes the resolved result 1:1 — a selected record with no
    authoritative counterpart is an identity failure, never a silent
    drop."""
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    with pytest.raises(ValueError, match="identity_failure"):
        create_bundle(result, [])


def test_create_bundle_requires_resolved_selection_state():
    """REPAIR-002: P14-E consumes the resolved selection/rejection state —
    a result without it (or with unlabeled entries) is not a resolved
    result."""
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    stripped = {k: v for k, v in result.items() if k != "selection"}
    with pytest.raises(ValueError, match="authority_violation"):
        create_bundle(stripped, records)
    half = dict(result)
    half["selection"] = {"selected": result["selection"]["selected"]}
    with pytest.raises(ValueError, match="authority_violation"):
        create_bundle(half, records)
    bare = dict(result)
    bare["selection"] = {"selected": [{"source": "cn_stock_quote"}],
                         "rejected": []}
    with pytest.raises(ValueError, match="authority_violation"):
        create_bundle(bare, records)


def test_create_bundle_rejects_uncovered_selected_record():
    """Every selected record must be covered by the resolved selection
    state — an unlabeled records entry is an authority violation, never a
    silently unlabeled bundle."""
    records = [_rec("cn_stock_quote", "q-1")]
    result = _resolve(records, _query())
    stripped = dict(result)
    stripped["selection"] = {"selected": [], "rejected": []}
    with pytest.raises(ValueError, match="authority_violation"):
        create_bundle(stripped, records)


def test_create_bundle_anchors_trace_to_authority():
    """Resolved rejections are anchored to the P14-B authoritative
    records — a rejection citing no authoritative record is an identity
    failure (the trace never cites unanchored records)."""
    keep = _rec("cn_stock_quote", "q-keep", revision=1,
                event="2026-03-03T15:00:00+08:00",
                available="2026-03-03T16:00:00+08:00",
                ingested="2026-03-03T16:05:00+08:00",
                payload={"close": 11.0}, value=11.0)
    drop = _rec("cn_stock_quote", "q-keep", revision=0,
                payload={"close": 10.0}, value=10.0)
    result = _resolve([drop, keep], _query())
    assert len(result["selection"]["rejected"]) == 1
    with pytest.raises(ValueError, match="identity_failure"):
        create_bundle(result, [keep])


def test_bundle_consumes_p14d_resolved_labels_verbatim():
    """REPAIR-002 core proof: the bundle carries P14-D's resolved labels
    as-is. Rewriting the resolved selection state rewrites the bundle —
    consumption, not re-derivation."""
    records = [
        _rec("cn_stock_quote", "q-verbatim", revision=0,
             payload={"close": 10.0}, value=10.0),
        _rec("cn_stock_quote", "q-verbatim", revision=1,
             event="2026-03-03T15:00:00+08:00",
             available="2026-03-03T16:00:00+08:00",
             ingested="2026-03-03T16:05:00+08:00",
             payload={"close": 11.0}, value=11.0),
    ]
    result = _resolve(records, _query())
    b = create_bundle(result, records)
    assert (b["evidence"][0]["selection_reason"]
            == result["selection"]["selected"][0]["selection_reason"]
            == SELECTION_HIGHEST)
    assert (b["candidate_trace"][0]["rejection_reason"]
            == result["selection"]["rejected"][0]["rejection_reason"]
            == REJECTED_LOWER)
    # flip the resolved labels -> the bundle follows them verbatim
    flipped = json.loads(json.dumps(result))
    flipped["selection"]["selected"][0]["selection_reason"] = \
        "SELECTED_CANONICAL_TIEBREAK"
    flipped["selection"]["rejected"][0]["rejection_reason"] = \
        "REJECTED_CANONICAL_TIEBREAK"
    b2 = create_bundle(flipped, records)
    assert b2["evidence"][0]["selection_reason"] == \
        "SELECTED_CANONICAL_TIEBREAK"
    assert b2["candidate_trace"][0]["rejection_reason"] == \
        "REJECTED_CANONICAL_TIEBREAK"
