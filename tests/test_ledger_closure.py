"""Ledger closure tests (Audit REQUIRED-1/2 + USEFUL-1/2).

Test A  append -> review -> load shows the latest review_status
Test B  multiple review events -> load returns the latest effective state
Test C  event history never shrinks
Test D  duplicate recommendation identity -> no duplicate event
Test E  different run identity -> independent recommendation
Test F  query(symbol=...)
Test G  query(action=...)
Test H  query(status=...)
Test I  query(date_range=...)
Test J  outcome_stats() over T+1/3/5/10
(Test K = existing suites stay green; run as a command, not here.)

All fixtures are tmp_path-synthesized; no data/ reads, no wall clock in
assertions (review_time values are fixed strings).
"""
from __future__ import annotations

import json

import pytest

from astock_v2.ledger import RecommendationLedger
from astock_v2.recommendation import RecommendationRecord


def _record(record_id="r1", symbol="000001", decision_time="2026-01-02T00:00:00+00:00",
            action="HOLD", probability=0.7):
    return RecommendationRecord(record_id, symbol, decision_time, action,
                                probability, 0.8, "x", "m1", {})


def _snapshot(run_id="run-1", result_id="res-1", bundle_id="bun-1"):
    return {"run_id": run_id, "result_id": result_id, "bundle_id": bundle_id}


def _review(record_id="r1", review_time="2026-01-07T00:00:00+00:00",
            realized_return=0.05, outcome="CORRECT"):
    from astock_v2.recommendation import LedgerReview
    return LedgerReview(record_id, review_time, realized_return, outcome, "closure test")


# ---------------------------------------------------------------- Test A

def test_a_review_event_reaches_read_view(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record(), "f1", input_snapshot=_snapshot())
    row = ledger.load()[0]
    assert row["review_status"] == "OPEN"          # before review

    ledger.append_review(_review(outcome="CORRECT"))
    row = ledger.load()[0]
    assert row["review_status"] == "CORRECT"       # after review (AC-2/AC-3)
    assert row["review"]["realized_return"] == 0.05
    assert row["review"]["notes"] == "closure test"


# ---------------------------------------------------------------- Test B

def test_b_multiple_reviews_latest_effective_wins(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record(), "f1", input_snapshot=_snapshot())
    ledger.append_review(_review(review_time="2026-01-05T00:00:00+00:00",
                                 realized_return=-0.01, outcome="INCORRECT"))
    ledger.append_review(_review(review_time="2026-01-07T00:00:00+00:00",
                                 realized_return=0.05, outcome="CORRECT"))
    ledger.append_review(_review(record_id="other", outcome="INCORRECT"))  # unrelated record
    row = ledger.load()[0]
    # file order is event order: the LAST review for r1 wins
    assert row["review_status"] == "CORRECT"
    assert row["review"]["review_time"] == "2026-01-07T00:00:00+00:00"


# ---------------------------------------------------------------- Test C

def test_c_event_history_never_shrinks(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    counts = []
    ledger.append(_record(), "f1", input_snapshot=_snapshot())
    counts.append(len(ledger.load()))
    ledger.append_review(_review(outcome="CORRECT"))
    counts.append(len(ledger.load()))
    ledger.append_review(_review(review_time="2026-01-08T00:00:00+00:00",
                                 realized_return=0.06, outcome="CORRECT"))
    counts.append(len(ledger.load()))
    assert counts == sorted(counts) and len(set(counts)) == len(counts)
    # raw event file only ever grows
    raw_lines = len((tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines())
    assert raw_lines == counts[-1]


# ---------------------------------------------------------------- Test D

def test_d_duplicate_identity_is_no_op(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    first = ledger.append_with_status(_record("r1"), "f1", input_snapshot=_snapshot())
    assert first["status"] == "created"
    second = ledger.append_with_status(_record("r1"), "f1", input_snapshot=_snapshot())
    assert second["status"] == "already_exists"
    assert second["event"] == first["event"]
    # plain append() is idempotent too
    ledger.append(_record("r1"), "f1", input_snapshot=_snapshot())
    rows = [r for r in ledger.load() if r.get("type") == "recommendation"]
    assert len(rows) == 1


# ---------------------------------------------------------------- Test E

def test_e_different_run_identity_is_independent(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append_with_status(_record("r1"), "f1", input_snapshot=_snapshot("run-A"))
    second = ledger.append_with_status(
        _record("r2"), "f1", input_snapshot=_snapshot("run-B", "res-B", "bun-B"))
    assert second["status"] == "created"
    rows = [r for r in ledger.load() if r.get("type") == "recommendation"]
    assert len(rows) == 2
    assert {r["record_id"] for r in rows} == {"r1", "r2"}


# ------------------------------------------------------------- Test F-I

def test_f_query_by_symbol(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record("r1", symbol="000001"), "f1", input_snapshot=_snapshot())
    ledger.append(_record("r2", symbol="000002"), "f1", input_snapshot=_snapshot("run-2", "res-2", "bun-2"))
    hits = ledger.query(symbol="000002")
    assert [r["record_id"] for r in hits] == ["r2"]


def test_g_query_by_action(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record("r1", action="HOLD"), "f1", input_snapshot=_snapshot())
    ledger.append(_record("r2", action="NO_ACTION"), "f1",
                  input_snapshot=_snapshot("run-2", "res-2", "bun-2"))
    assert [r["record_id"] for r in ledger.query(action="NO_ACTION")] == ["r2"]
    assert [r["record_id"] for r in ledger.query(action="HOLD")] == ["r1"]


def test_h_query_by_status(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record("r1"), "f1", input_snapshot=_snapshot())
    ledger.append(_record("r2"), "f1", input_snapshot=_snapshot("run-2", "res-2", "bun-2"))
    ledger.append_review(_review(record_id="r2", outcome="INCORRECT"))
    assert [r["record_id"] for r in ledger.query(status="OPEN")] == ["r1"]
    assert [r["record_id"] for r in ledger.query(status="INCORRECT")] == ["r2"]


def test_i_query_by_date_range(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    ledger.append(_record("r1", decision_time="2026-01-02T00:00:00+00:00"),
                  "f1", input_snapshot=_snapshot("run-1", "res-1", "bun-1"))
    ledger.append(_record("r2", decision_time="2026-03-02T00:00:00+08:00"),
                  "f1", input_snapshot=_snapshot("run-2", "res-2", "bun-2"))
    # UTC-normalized: 2026-03-01T00:00+08:00 == 2026-02-28T16:00Z <= r2 (03-01T16:00Z)
    hits = ledger.query(date_range=("2026-02-28T16:00:00+00:00", "2026-03-05T00:00:00+00:00"))
    assert [r["record_id"] for r in hits] == ["r2"]
    everything = ledger.query(date_range=("2026-01-01T00:00:00+00:00", "2026-12-31T00:00:00+00:00"))
    assert len(everything) == 2


# ---------------------------------------------------------------- Test J

def test_j_outcome_stats_over_all_horizons(tmp_path):
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    # r1 HOLD: positive T+1 (correct), negative T+3 (incorrect)
    ledger.append(_record("r1", action="HOLD"), "f1", input_snapshot=_snapshot())
    ledger.backfill_returns("000001", "2026-01-02T00:00:00+00:00",
                            {"decision": 10, 1: 10.5, 3: 9.8})
    # r2 BUY: zero T+5 (unresolved), positive T+10 (correct)
    ledger.append(_record("r2", symbol="000002", action="BUY",
                          decision_time="2026-01-03T00:00:00+00:00"),
                  "f1", input_snapshot=_snapshot("run-2", "res-2", "bun-2"))
    ledger.backfill_returns("000002", "2026-01-03T00:00:00+00:00",
                            {"decision": 20, 5: 20.0, 10: 21.0})
    # r3 NO_ACTION: realized T+1 but posture is unresolved
    ledger.append(_record("r3", symbol="000003", action="NO_ACTION",
                          decision_time="2026-01-04T00:00:00+00:00"),
                  "f1", input_snapshot=_snapshot("run-3", "res-3", "bun-3"))
    ledger.backfill_returns("000003", "2026-01-04T00:00:00+00:00",
                            {"decision": 30, 1: 31.0})

    stats = ledger.outcome_stats()
    assert set(stats) == {"T+1", "T+3", "T+5", "T+10"}

    t1 = stats["T+1"]
    assert t1["samples"] == 2                     # r1 + r3
    assert t1["correct"] == 1 and t1["incorrect"] == 0 and t1["unresolved"] == 1
    assert t1["hit_rate"] == pytest.approx(1.0)
    assert t1["avg_realized_return"] == pytest.approx(((10.5 / 10 - 1) + (31.0 / 30 - 1)) / 2)

    t3 = stats["T+3"]
    assert t3["samples"] == 1 and t3["incorrect"] == 1
    assert t3["hit_rate"] == pytest.approx(0.0)
    assert t3["avg_realized_return"] == pytest.approx(9.8 / 10 - 1)

    t5 = stats["T+5"]
    assert t5["samples"] == 1 and t5["unresolved"] == 1 and t5["hit_rate"] is None

    t10 = stats["T+10"]
    assert t10["correct"] == 1 and t10["hit_rate"] == pytest.approx(1.0)

    # read-only: stats never write events
    before = len((tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines())
    ledger.outcome_stats()
    after = len((tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines())
    assert before == after


# ------------------------------------------------- interaction with FS6 era

def test_k_r4a_shaped_duplicate_is_no_op(tmp_path):
    """The R4-A append path (record_id=r4a-<run_id>, full input_snapshot)
    must be idempotent across research reruns of the same store state."""
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    snap = {"run_id": "abcd1234", "result_id": "res", "bundle_id": "bun",
            "r4d_probability": {"probability_status": "CALIBRATED", "probability": 0.5},
            "p14f_registry_sha256": "sha", "p14f_feature_set_id": "fs-x"}
    a = ledger.append_with_status(_record("r4a-abcd1234"), "m1", input_snapshot=snap)
    b = ledger.append_with_status(_record("r4a-abcd1234"), "m1", input_snapshot=snap)
    assert a["status"] == "created" and b["status"] == "already_exists"
    rows = [r for r in ledger.load() if r.get("type") == "recommendation"]
    assert len(rows) == 1
    assert rows[0]["input_snapshot"]["p14f_feature_set_id"] == "fs-x"
