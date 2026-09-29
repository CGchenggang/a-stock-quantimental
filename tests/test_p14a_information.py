"""P14-A information layer invariants (handoff §19 coverage)."""
from __future__ import annotations

import json

import pytest

from astock_v2.information import (
    CONFLICT,
    annotate_conflict_status,
    FRESH,
    MISSING_POLICY,
    STALE,
    UNKNOWN,
    FRESHNESS_POLICIES,
    RawInformationRecord,
    SOURCE_REGISTRY,
    assert_research_zone,
    dedup_key,
    deduplicate,
    detect_conflicts,
    freshness_status,
    is_admissible,
    normalize,
    provenance_issues,
    select_asof,
    to_research_record,
    visible_revisions,
)


def _record(**overrides):
    base = {
        "source": "macro_pmi_cn",
        "source_id": "PMI_CN_2026M01",
        "source_category": "MACRO",
        "entity_id": "CN",
        "entity_type": "ECONOMY",
        "event_time": "2026-01-31T09:00:00+08:00",
        "available_time": "2026-02-01T09:30:00+08:00",
        "revision": 0,
        "ingested_at": "2026-02-01T10:00:00+08:00",
        "value": 50.1,
        "unit": "index",
        "freshness_policy_id": "macro_release_35d",
    }
    base.update(overrides)
    return RawInformationRecord(**base)


# 1. canonical record schema
def test_record_schema_requires_provenance_and_content_or_value():
    with pytest.raises(ValueError):
        _record(source="")
    with pytest.raises(ValueError):
        _record(source_id="")
    with pytest.raises(ValueError):
        _record(revision=-1)
    with pytest.raises(ValueError):
        _record(content=None, value=None)
    with pytest.raises(ValueError):
        _record(available_time="2026-02-01T09:30:00")  # naive timestamp
    r = _record()
    assert r.canonical_json() == json.dumps(r.as_dict(), sort_keys=True, ensure_ascii=False)


# 2./3./4./5. PIT admissibility, exact boundary, event vs available time
def test_pit_boundary_is_inclusive_and_uses_available_time_only():
    # handoff cases: event_time = 2026-01-01, available_time = 2026-01-03
    record = _record(event_time="2026-01-01T09:00:00+08:00",
                     available_time="2026-01-03T09:30:00+08:00")
    # Case A: decision 01-02 -> NOT admissible
    assert is_admissible(record, "2026-01-02T09:00:00+08:00") is False
    # Case B: decision 01-03 -> ADMISSIBLE (available_time <= decision_time)
    assert is_admissible(record, "2026-01-03T09:30:00+08:00") is True


def test_event_time_cannot_substitute_available_time():
    # event 01-31, available 02-01: at decision 01-31 (after event) the
    # record is NOT yet admissible - only available_time gates PIT.
    record = _record()
    assert is_admissible(record, "2026-01-31T23:59:00+08:00") is False
    assert is_admissible(record, "2026-02-01T09:30:00+08:00") is True


def test_late_arriving_information_is_admissible_by_available_time():
    # event_time BEFORE available_time is the normal case; a big gap must
    # not cause rejection
    late = _record(event_time="2026-01-10T09:00:00+08:00",
                   available_time="2026-01-12T09:00:00+08:00")
    assert is_admissible(late, "2026-01-11T09:00:00+08:00") is False
    assert is_admissible(late, "2026-01-12T09:00:00+08:00") is True


# 7./8. revised information and revision boundary
def test_revision_visibility_boundary():
    records = [
        _record(revision=0, available_time="2026-02-01T09:30:00+08:00", value=50.1),
        _record(revision=1, available_time="2026-02-15T09:30:00+08:00", value=50.3),
    ]
    before = visible_revisions(records, "2026-02-10T09:00:00+08:00")
    assert before[("macro_pmi_cn", "PMI_CN_2026M01")].value == 50.1  # rev 0 only
    at = visible_revisions(records, "2026-02-15T09:30:00+08:00")
    assert at[("macro_pmi_cn", "PMI_CN_2026M01")].value == 50.3  # rev 1 from its boundary
    # revision 1 can never leak backwards
    early = visible_revisions(records, "2026-02-01T09:30:00+08:00")
    assert early[("macro_pmi_cn", "PMI_CN_2026M01")].revision == 0


# 9./10. provenance
def test_provenance_rejects_placeholder_source_and_missing_ingested_at():
    issues = provenance_issues(_record(source="unknown"))
    assert "source_is_placeholder" in issues
    row = _record()
    del row.__dict__["ingested_at"]
    row.__dict__["ingested_at"] = ""
    assert "missing_ingested_at" in provenance_issues(row)
    with pytest.raises(ValueError, match="cannot enter the research layer"):
        to_research_record(_record(source="unknown"))


def test_source_identity_registry():
    assert SOURCE_REGISTRY["macro_pmi_cn"].source_category.name == "MACRO"
    assert "brand_new_blog" not in SOURCE_REGISTRY
    # normalization rejects unregistered sources
    with pytest.raises(ValueError, match="unregistered_source"):
        normalize([_record(source_id="WHATEVER", source="brand_new_blog")])


# 11. freshness with explicit per-source policy
def test_freshness_uses_policy_and_available_time():
    policies = dict(FRESHNESS_POLICIES)
    # macro policy allows 35 days
    r = _record(available_time="2026-02-01T09:30:00+08:00")
    assert freshness_status(r, "2026-02-20T09:30:00+08:00", policies) == FRESH
    assert freshness_status(r, "2026-03-10T09:30:00+08:00", policies) == STALE
    # a daily-market record under the macro policy is fresh, but under its
    # own daily policy the same age is stale -> per-source policies matter
    market = _record(source_id="X", source="cn_index_daily",
                     freshness_policy_id="market_daily",
                     available_time="2026-02-01T16:00:00+08:00")
    assert freshness_status(market, "2026-02-10T16:00:00+08:00", policies) == STALE
    # no policy id -> unknown (explicit), not silently fresh
    nop = _record(freshness_policy_id=None)
    assert freshness_status(nop, "2026-02-02T00:00:00+08:00", policies) == UNKNOWN
    # policy id that is not registered -> missing_policy, not guessed
    ghost = _record(freshness_policy_id="mystery_policy")
    assert freshness_status(ghost, "2026-02-02T00:00:00+08:00", policies) == MISSING_POLICY


# 12./13. deduplication
def test_dedup_key_and_deduplicate():
    a = _record()
    b = _record()  # identical duplicate
    c = _record(revision=1, available_time="2026-02-15T09:30:00+08:00", value=50.3)
    assert dedup_key(a) == dedup_key(b) == ("macro_pmi_cn", "PMI_CN_2026M01", 0)
    assert dedup_key(c) != dedup_key(a)  # revision is part of the key
    out = deduplicate([a, b, c])
    assert len(out) == 2
    assert {r.revision for r in out} == {0, 1}


def test_duplicate_source_record_order_independent():
    a = _record(ingested_at="2026-02-01T10:00:00+08:00")
    b = _record(ingested_at="2026-02-01T10:00:00+08:00")
    b.__dict__["ingested_at"] = "2026-02-01T11:00:00+08:00"
    out1 = deduplicate([a, b])
    out2 = deduplicate([b, a])
    assert [r.canonical_json() for r in out1] == [r.canonical_json() for r in out2]


# 14. conflicting sources kept, never resolved
def test_conflicting_sources_marked_conflict():
    src_a = _record(source="macro_pmi_cn", value=50.1,
                    available_time="2026-02-01T10:00:00+08:00")
    src_b = _record(source="macro_cpi_cn", source_id="PMI_ALT_2026M01",
                    value=50.3, available_time="2026-02-01T10:05:00+08:00")
    conflicts = detect_conflicts([src_a, src_b])
    assert conflicts  # different values from different sources
    annotated = annotate_conflict_status([src_a, src_b])
    status_by_id = {r.record_id(): st for r, st in annotated}
    assert status_by_id[src_a.record_id()] == CONFLICT
    assert status_by_id[src_b.record_id()] == CONFLICT
    # same source with a different revision is a correction, not a conflict
    same_source_rev = _record(revision=1, value=50.3,
                              available_time="2026-02-02T10:00:00+08:00")
    assert not detect_conflicts([src_a, same_source_rev])
    # identical values from different sources are not conflicts
    twin = _record(source="macro_cpi_cn", source_id="PMI_ALT",
                   value=50.1, available_time="2026-02-01T10:05:00+08:00")
    assert not detect_conflicts([src_a, twin])


# 15. missing source: explicit rejection, no fill, no silent drop
def test_missing_source_rejected_not_filled():
    row = _record(source="unknown")
    assert "source_is_placeholder" in provenance_issues(row)
    with pytest.raises(ValueError, match="rejected by normalization"):
        normalize([row])
    with pytest.raises(ValueError, match="cannot enter the research layer"):
        to_research_record(row)


# 16. deterministic normalization
def test_normalization_is_deterministic():
    records = [
        _record(source_id="PMI_CN_2026M01"),
        _record(source_id="PMI_CN_2026M02", event_time="2026-02-28T09:00:00+08:00",
                available_time="2026-03-01T09:30:00+08:00", value=50.2),
    ]
    shuffled = list(reversed(records))
    out1 = json.dumps([r.as_dict() for r in normalize(records)], sort_keys=True)
    out2 = json.dumps([r.as_dict() for r in normalize(shuffled)], sort_keys=True)
    assert out1 == out2
    # no runtime/generated fields in normalized output
    keys = set(normalize(records)[0].as_dict())
    assert not {"generated_at", "uuid", "ingested_wall_time"} & keys


# 17. repeated-run byte identity (records + research conversion)
def test_repeated_run_byte_identical():
    records = [_record(source_id="PMI_CN_2026M01"),
               _record(source_id="PMI_CN_2026M02", value=49.9,
                       available_time="2026-02-01T11:00:00+08:00")]
    first = json.dumps([r.as_dict() for r in normalize(records)], sort_keys=True)
    second = json.dumps([r.as_dict() for r in normalize(records)], sort_keys=True)
    assert first == second
    raw_first = json.dumps([r.as_dict() for r in records], sort_keys=True)
    research_first = json.dumps(
        [to_research_record(r).as_dict() for r in records], sort_keys=True)
    raw_second = json.dumps([r.as_dict() for r in records], sort_keys=True)
    research_second = json.dumps(
        [to_research_record(r).as_dict() for r in records], sort_keys=True)
    assert raw_first == raw_second
    assert research_first == research_second


# 19. P13-U virgin holdout protection through the P14 layer
def test_information_layer_rejects_virgin_decision_time():
    record = _record(available_time="2026-01-02T09:00:00+08:00")
    # PIT would admit this at any later date, but the virgin boundary fails fast
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT DATA CANNOT BE CONSUMED"):
        select_asof([record], "2026-09-23T16:00:00+08:00")
    with pytest.raises(ValueError, match="VIRGIN HOLDOUT DATA CANNOT BE CONSUMED"):
        select_asof([record], "2027-06-01T16:00:00+08:00")


def test_information_layer_selects_research_zone_dates():
    record = _record(available_time="2025-03-01T09:00:00+08:00")
    out = select_asof([record], "2025-03-02T16:00:00+08:00")
    assert len(out) == 1
    # boundary date 2026-09-22 is still research zone
    assert select_asof([record], "2026-09-22T16:00:00+08:00")
    # boundary semantics of select: not yet available records are excluded
    assert select_asof([record], "2025-02-28T16:00:00+08:00") == []


def test_virgin_guard_constant_shared_with_p13u():
    from astock_v2.information import VIRGIN_START
    from astock_v2.research_boundary import VIRGIN_START as ROOT_VIRGIN_START
    import scripts.run_p13u_gate as gate
    assert VIRGIN_START == ROOT_VIRGIN_START == gate.VIRGIN_START == "2026-09-23"


# 20. P13-Q/P13-R research-zone protection unchanged
def test_p13q_and_p13r_guards_still_active():
    import scripts.run_p13q_analysis as q
    import scripts.run_p13r_analysis as r
    for module in (q, r):
        assert module.assert_research_zone.__module__ in (
            "astock_v2.research_boundary", "scripts.run_p13u_gate")
        with pytest.raises(ValueError, match="VIRGIN HOLDOUT"):
            module.assert_research_zone(["2026-09-23T16:00:00+08:00"])


# 21.-24. production snapshots untouched
def test_production_snapshots_unchanged():
    from astock_v2.factors import FACTOR_REGISTRY
    assert set(FACTOR_REGISTRY) == {
        "momentum", "volatility", "trend", "volume_ratio",
        "close_to_high", "close_to_low", "range_ratio", "close_location",
    }
    import scripts.run_p13r_analysis as pr
    policies = pr.build_policy_registry(0.02)
    assert len(policies) == 8
    registry = json.load(open("data/industry/p13q/calibration_registry.json",
                              encoding="utf-8"))
    assert all(e["status"] == "research_only" for e in registry["methods"].values())


def test_information_records_are_research_only():
    record = to_research_record(_record())
    assert record.research_only is True
