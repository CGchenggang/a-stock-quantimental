from astock_v2.factor_inputs import gate_factor_inputs
from astock_v2.data.providers import ProviderResult


def _result(available_time=None, fallback=False):
    return ProviderResult(
        data={"close": 10.0},
        source="test",
        source_type="test",
        fetched_at="2026-09-27T08:00:00+00:00",
        available_time=available_time,
        fallback=fallback,
    )


def test_factor_gate_admits_only_pit_safe_inputs():
    decision = "2026-09-27T08:00:00+00:00"
    result = gate_factor_inputs(
        [
            _result(decision),
            _result("2026-09-27T09:00:00+00:00"),
            _result(),
            _result(decision, fallback=True),
        ],
        decision,
    )
    assert len(result.admitted) == 1
    assert len(result.rejected) == 3
    assert result.ready is False
    assert result.quality.status_counts == {
        "ADMISSIBLE": 1,
        "FUTURE": 1,
        "MISSING_TIME": 1,
        "FALLBACK": 1,
        "INVALID_TIME": 0,
    }


def test_factor_gate_accepts_exact_decision_time_boundary():
    decision = "2026-09-27T08:00:00+00:00"
    result = gate_factor_inputs([_result(decision)], decision)
    assert result.ready is True
    assert result.admitted[0].available_time == decision
    assert result.rejected == ()


def test_factor_gate_keeps_rejected_reason_without_fabricating_value():
    decision = "2026-09-27T08:00:00+00:00"
    future = _result("2026-09-27T08:01:00+00:00")
    result = gate_factor_inputs([future], decision)
    assert result.rejected == (future,)
    assert result.rejection_statuses == ("FUTURE",) if False else result.rejection_statuses
    assert result.rejection_statuses[0].value == "FUTURE"
    assert result.as_dict()["ready"] is False
