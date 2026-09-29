"""P14-B raw ingestion store and adapter contract invariants (28 checks)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import pathlib

from astock_v2.information.adapters import (
    AUTH_ERROR,
    EMPTY_SUCCESS,
    PARSE_ERROR,
    SOURCE_ERROR,
    TIMEOUT,
    IngestionReport,
    SourceAdapter,
)
from astock_v2.information.adapters_fixture import FIXTURE_ADAPTERS, MacroPMICNAdapter
from astock_v2.information.raw_store import (
    RAW_MUTATION_DETECTED,
    canonical_payload_hash,
    RawIngestRecord,
    RawStore,
    canonical_payload_hash,
    to_information_record,
)
from astock_v2.information import normalize, select_asof

FIXTURES = {
    "cn_index_daily": {
        "source_id": "CSI300_2026-03-02", "entity_id": "CSI300",
        "event_time": "2026-03-02T15:00:00+08:00",
        "available_time": "2026-03-02T16:00:00+08:00",
        "ingested_at": "2026-03-02T16:05:00+08:00",
        "close": 4123.45, "symbol": "000300",
    },
    "company_announcement": {
        "source_id": "ANN_000001_2026-03-03", "entity_id": "000001",
        "event_time": "2026-03-03T17:30:00+08:00",
        "available_time": "2026-03-03T19:00:00+08:00",
        "ingested_at": "2026-03-03T19:10:00+08:00",
        "content": "Research fixture announcement.",
        "symbol": "000001",
    },
    "macro_pmi_cn": {
        "source_id": "PMI_CN_2026M01", "entity_id": "CN",
        "event_time": "2026-01-31T09:00:00+08:00",
        "available_time": "2026-02-01T09:30:00+08:00",
        "ingested_at": "2026-02-01T10:00:00+08:00",
        "value": 50.1,
    },
    "us_index_daily": {
        "source_id": "SPX_2026-03-02", "entity_id": "SPX",
        "event_time": "2026-03-02T05:00:00+08:00",
        "available_time": "2026-03-02T06:00:00+08:00",
        "ingested_at": "2026-03-02T06:10:00+08:00",
        "close": 5432.1,
    },
}


def _adapter(source: str, payloads=None):
    adapter = FIXTURE_ADAPTERS[source]
    if payloads is None:
        payloads = [dict(FIXTURES[source])]
    return type(adapter)(list(payloads))


def _ingest(tmp_path, source, payloads=None):
    if payloads is None:
        payloads = [dict(FIXTURES[source])]
    store = RawStore(pathlib.Path(tmp_path) / "raw.jsonl")
    report = _adapter(source, payloads).ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    return store, report


# 1. raw record schema
def test_raw_record_schema_fields(tmp_path):
    store, report = _ingest(tmp_path, "macro_pmi_cn")
    record = store.records()[0]
    for field in ("source", "source_id", "source_category", "entity_id",
                  "entity_type", "symbol", "event_time", "available_time",
                  "revision", "content", "value", "unit", "currency",
                  "ingested_at", "raw_payload", "raw_payload_hash",
                  "ingestion_id", "adapter_version"):
        assert field in record.as_dict(), field


# 2./3. raw payload preservation and hash
def test_raw_payload_preserved_and_hashed(tmp_path):
    store, report = _ingest(tmp_path, "company_announcement")
    record = store.records()[0]
    payload = FIXTURES["company_announcement"]
    assert record.raw_payload == payload  # verbatim canonical payload kept
    assert record.raw_payload_hash == canonical_payload_hash(payload)
    # hash is deterministic for the same payload
    assert canonical_payload_hash(payload) == canonical_payload_hash(dict(payload))


def test_canonical_payload_hash_detects_difference(tmp_path):
    a = canonical_payload_hash({"v": 50.1})
    b = canonical_payload_hash({"v": 50.3})
    assert a != b
    assert a == canonical_payload_hash({"v": 50.1})


# 4. same payload idempotency
PMI_BOTH: list[dict] = [
    dict(FIXTURES["macro_pmi_cn"], revision=0,
         available_time="2026-02-01T09:30:00+08:00", value=50.1),
    dict(FIXTURES["macro_pmi_cn"], source_id="PMI_CN_2026M01", revision=1,
         available_time="2026-02-15T09:30:00+08:00", value=50.3),
]


def test_same_payload_reingest_is_idempotent(tmp_path):
    store, first = _ingest(tmp_path, "macro_pmi_cn", [dict(p) for p in PMI_BOTH])
    adapter = _adapter("macro_pmi_cn", [dict(p) for p in PMI_BOTH])
    second = adapter.ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    assert first.accepted == 2 and second.duplicates == 2 and second.accepted == 0
    assert len(store.records()) == 2


# 5./8. conflicting payload detection (no silent overwrite)
def test_same_key_different_payload_is_mutation_detected(tmp_path):
    store = RawStore(tmp_path / "raw.jsonl")
    seeds = [dict(p) for p in PMI_BOTH]
    _adapter("macro_pmi_cn", seeds).ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    # same source/source_id/revision, different value -> different payload
    tampered = [dict(seeds[0], value=99.9)]
    report = _adapter("macro_pmi_cn", tampered).ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    assert report.mutations == 1
    records = store.records()
    assert len(records) == 2  # original rev0 + rev1 preserved, no overwrite
    assert all(r.value != 99.9 for r in records)
    assert report.errors and "raw mutation detected" in report.errors[0]


# 6. revision preservation
def test_revision_history_preserved(tmp_path):
    store, report = _ingest(tmp_path, "macro_pmi_cn", [dict(p) for p in PMI_BOTH])
    # fixture contains rev0 (2026-02-01) and rev1 (2026-02-15): both stored
    revisions = sorted(r.revision for r in store.records())
    assert revisions == [0, 1]
    by_rev = {r.revision: r for r in store.records()}
    assert by_rev[0].value == 50.1 and by_rev[0].available_time.startswith("2026-02-01")
    assert by_rev[1].value == 50.3 and by_rev[1].available_time.startswith("2026-02-15")


# 7. raw record immutability (frozen dataclass)
def test_raw_record_is_immutable():
    payload = dict(FIXTURES["macro_pmi_cn"])
    record = RawIngestRecord(
        source="macro_pmi_cn", source_id=payload["source_id"],
        source_category="MACRO", entity_id=payload["entity_id"],
        entity_type="ECONOMY", event_time=payload["event_time"],
        available_time=payload["available_time"], revision=0,
        ingested_at=payload["ingested_at"], raw_payload=payload,
        adapter_version="macro_pmi_cn_adapter@1", value=payload["value"],
        unit="index")
    with pytest.raises(Exception):
        record.value = 99.9


# 9./10./11./12. provenance, adapter version, timestamp preservation,
# availability never falls back
def test_ingest_metadata_preserved_and_never_fabricated(tmp_path):
    store, report = _ingest(tmp_path, "cn_index_daily")
    record = store.records()[0]
    fixture = FIXTURES["cn_index_daily"]
    assert record.ingested_at == fixture["ingested_at"]
    assert record.event_time == fixture["event_time"]
    assert record.available_time == fixture["available_time"]
    assert record.adapter_version == "cn_index_daily_adapter@1"
    assert record.raw_payload["ingested_at"] == fixture["ingested_at"]
    assert record.raw_payload["event_time"] == fixture["event_time"]


def test_missing_available_time_stays_unresolved(tmp_path):
    """A source without reliable available_time must NOT inherit
    event_time or ingested_at. The raw store keeps it marked UNRESOLVED;
    the projection to the P14-A information contract refuses it (it could
    never pass PIT admissibility), so it cannot reach the research layer."""
    payload = dict(FIXTURES["macro_pmi_cn"])
    payload["available_time"] = None
    store = RawStore(tmp_path / "raw.jsonl")
    adapter = _adapter("macro_pmi_cn", [payload])
    adapter.ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    record = store.records()[0]
    assert record.available_time is None
    assert record.quality_status == "UNRESOLVED"
    assert record.availability_status == "available_time_unresolved"
    with pytest.raises(ValueError, match="available_time"):
        to_information_record(record)


# 15. duplicate ingestion audited as duplicate, not a new fact
def test_duplicate_ingestion_audited(tmp_path):
    store, report = _ingest(tmp_path, "cn_index_daily")
    replay = _adapter("cn_index_daily").ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    assert replay.duplicates == 1 and replay.accepted == 0
    outcomes = [o["outcome"] for o in store.outcomes()]
    assert outcomes.count("DUPLICATE") == 1


# 16./17. partial and failed ingestion
def test_partial_ingestion_is_audited(tmp_path):
    """attempted = accepted + rejected; parse failures are audited with
    their payload index and set status = PARSE_ERROR."""
    good = dict(FIXTURES["macro_pmi_cn"])
    broken = {k: v for k, v in good.items() if k != "source_id"}  # parse fails
    store = RawStore(tmp_path / "raw.jsonl")
    adapter = _adapter("macro_pmi_cn", [good, broken])
    report = adapter.ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    assert report.attempted == 2
    assert report.accepted == 1
    assert report.rejected == 1
    assert report.errors and "payload[1]" in report.errors[0]
    assert report.status == PARSE_ERROR
    assert [r.source_id for r in store.records()] == ["PMI_CN_2026M01"]


def test_failed_ingestion_statuses():
    assert {EMPTY_SUCCESS, SOURCE_ERROR, PARSE_ERROR, AUTH_ERROR, TIMEOUT} == {
        "EMPTY_SUCCESS", "SOURCE_ERROR", "PARSE_ERROR", "AUTH_ERROR", "TIMEOUT",
    }


def test_empty_source_is_empty_success_not_error(tmp_path):
    store = RawStore(tmp_path / "raw.jsonl")
    report = _adapter("macro_pmi_cn", []).ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
    assert report.status == EMPTY_SUCCESS
    assert report.attempted == 0


def test_source_error_and_auth_and_timeout_statuses(tmp_path):
    class Boom(MacroPMICNAdapter):
        def fetch(self):
            raise RuntimeError("boom")

    class Denied(MacroPMICNAdapter):
        def fetch(self):
            raise PermissionError("denied")

    class Slow(MacroPMICNAdapter):
        def fetch(self):
            raise TimeoutError("slow")

    for adapter_cls, expected in ((Boom, SOURCE_ERROR), (Denied, AUTH_ERROR),
                                  (Slow, TIMEOUT)):
        store = RawStore(tmp_path / f"{expected}.jsonl")
        report = adapter_cls([]).ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
        assert report.status == expected


# 18./19. deterministic adapter output and raw storage
def test_adapter_output_and_store_deterministic(tmp_path):
    runs = []
    for i in range(2):
        store = RawStore(tmp_path / f"raw{i}.jsonl")
        report = _adapter("macro_pmi_cn").ingest(store, ingested_at="2026-03-10T16:00:00+08:00")
        runs.append(json.dumps({
            "report": report.as_dict(),
            "records": [r.as_dict() for r in store.records()],
        }, sort_keys=True))
    assert runs[0] == runs[1]


# 20./21. repeated ingestion byte identity across store instances
def test_store_file_byte_identical_on_replay(tmp_path):
    store_a = RawStore(tmp_path / "a.jsonl")
    _adapter("cn_index_daily").ingest(store_a, ingested_at="2026-03-10T16:00:00+08:00")
    data_a = (tmp_path / "a.jsonl").read_bytes()
    store_b = RawStore(tmp_path / "b.jsonl")
    _adapter("cn_index_daily").ingest(store_b, ingested_at="2026-03-10T16:00:00+08:00")
    data_b = (tmp_path / "b.jsonl").read_bytes()
    assert data_a == data_b
    # replay into the SAME store appends only audit lines? No: puts are
    # in-memory idempotent; the file already holds one line per record.
    _adapter("cn_index_daily").ingest(store_a, ingested_at="2026-03-10T16:00:00+08:00")
    assert (tmp_path / "a.jsonl").read_bytes() == data_a


# 22. P14-A normalization compatibility
def test_raw_records_flow_through_p14a_normalization(tmp_path):
    store, report = _ingest(tmp_path, "company_announcement")
    research = normalize([to_information_record(r) for r in store.records()])
    assert len(research) == 1
    assert research[0].research_only is True
    assert research[0].content == FIXTURES["company_announcement"]["content"]
    assert research[0].metadata["raw_payload_hash"] == \
        store.records()[0].raw_payload_hash


# 23. P13-U virgin protection through the ingested-data path
def test_ingested_data_cannot_be_selected_in_virgin_zone(tmp_path):
    store, report = _ingest(tmp_path, "company_announcement")
    research = normalize([to_information_record(r) for r in store.records()])
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT DATA CANNOT BE CONSUMED"):
        select_asof(research, "2026-09-23T16:00:00+08:00")
    # research-zone selection still works (fixture is from 2026-03)
    assert select_asof(research, "2026-03-04T16:00:00+08:00")


# 24. P13-Q/P13-R guard preservation
def test_p13q_p13r_guards_preserved():
    import scripts.run_p13q_analysis as q
    import scripts.run_p13r_analysis as r
    for module in (q, r):
        with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
            module.assert_research_zone(["2026-09-23T16:00:00+08:00"])


# 25.-27. production snapshots untouched
def test_production_factor_policy_calibration_snapshots(tmp_path):
    """P14-B must not mutate the production factor registry, the P13-R
    policy registry or the P13-Q calibration registry. Registries are
    rebuilt in-test from the shipped builders (CI has no data artifacts)."""
    from astock_v2.factors import FACTOR_REGISTRY
    assert set(FACTOR_REGISTRY) == {
        "momentum", "volatility", "trend", "volume_ratio",
        "close_to_high", "close_to_low", "range_ratio", "close_location",
    }
    import scripts.run_p13r_analysis as pr
    policies_first = json.dumps(pr.build_policy_registry(0.02), sort_keys=True)
    assert len(json.loads(policies_first)) == 8

    from scripts.run_p13q_analysis import task_registry
    methods = {
        m: {"n": 5, "brier": 0.25, "log_loss": 0.69, "ece": 0.01,
            "calibration_intercept": 0.0, "calibration_slope": 1.0,
            "delta_brier": 0.0, "delta_log_loss": 0.0, "delta_ece": 0.0}
        for m in ("raw", "platt", "isotonic")
    }
    payload = {"training_period": "t", "evaluation_period": "e",
               "training_n": 1, "evaluation_n": 1, "methods": methods}
    registry_first = tmp_path / "registry_run1.json"
    task_registry(payload, tmp_path)
    (tmp_path / "calibration_registry.json").rename(registry_first)
    task_registry(payload, tmp_path)
    registry_second = tmp_path / "calibration_registry.json"
    assert registry_first.read_bytes() == registry_second.read_bytes()
    rebuilt = json.loads(registry_second.read_text(encoding="utf-8"))
    assert all(e["status"] == "research_only"
               for e in rebuilt["methods"].values())


# 28. no recommendation generation in the raw layer
def test_raw_store_module_generates_no_recommendation(tmp_path):
    import scripts.run_p13u_gate as gate
    import astock_v2.information.raw_store as raw_store
    import astock_v2.information.adapters as adapters
    for module in (gate, raw_store, adapters):
        source = Path(module.__file__).read_text(encoding="utf-8").lower()
        for banned in ("buy_now", "place_order", "execute_trade",
                       "open_position", "close_position", "broker"):
            assert banned not in source, (module.__name__, banned)
