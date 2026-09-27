from astock_v2.data.providers import ProviderResult
from astock_v2.data_quality import summarize_pit
from astock_v2.factor_contracts import FactorOutput
from astock_v2.probability_inputs import gate_probability_inputs


def _factor(name, value, available):
    decision = "2026-09-27T08:00:00+00:00"
    result = ProviderResult(
        data={"value": value},
        source="test",
        source_type="test",
        fetched_at=decision,
        available_time=available,
    )
    quality = summarize_pit([result], decision)
    return FactorOutput(name, "000001", value, decision, quality, ("test",))


def test_probability_gate_requires_named_factors():
    factors = [_factor("momentum", 0.2, "2026-09-27T08:00:00+00:00"),
               _factor("volatility", 0.4, "2026-09-27T08:00:00+00:00")]
    gate = gate_probability_inputs(factors, required_names=("momentum", "volatility"))
    assert gate.ready is True
    assert len(gate.admitted) == 2
    assert gate.rejected == ()


def test_probability_gate_rejects_future_factor():
    factors = [_factor("momentum", 0.2, "2026-09-27T09:00:00+00:00")]
    gate = gate_probability_inputs(factors, required_names=("momentum",))
    assert gate.ready is False
    assert gate.admitted == ()
    assert gate.rejected == tuple(factors)


def test_probability_gate_rejects_missing_required_factor():
    factors = [_factor("momentum", 0.2, "2026-09-27T08:00:00+00:00")]
    gate = gate_probability_inputs(factors, required_names=("momentum", "volatility"))
    assert gate.ready is False
    assert gate.as_dict()["admitted"] == ["momentum"]
