from astock_v2.data.providers import ProviderResult
from astock_v2.data_quality import summarize_pit
from astock_v2.factor_contracts import FactorOutput, factor_output_ready


def test_factor_output_requires_value_and_pit_quality():
    decision = "2026-09-27T08:00:00+00:00"
    base = ProviderResult(
        data={"close": 10.0},
        source="test",
        source_type="test",
        fetched_at=decision,
        available_time=decision,
    )
    quality = summarize_pit([base], decision)
    output = FactorOutput("momentum", "000001", 0.12, decision, quality, ("test",))
    assert output.admissible is True
    assert factor_output_ready(output) is True
    assert output.as_dict()["data_quality"]["pit_admissible"] is True


def test_factor_output_rejects_future_input_quality():
    decision = "2026-09-27T08:00:00+00:00"
    future = ProviderResult(
        data={"close": 10.0},
        source="test",
        source_type="test",
        fetched_at=decision,
        available_time="2026-09-27T09:00:00+00:00",
    )
    quality = summarize_pit([future], decision)
    output = FactorOutput("momentum", "000001", 0.12, decision, quality)
    assert output.admissible is False
    assert factor_output_ready(output) is False


def test_factor_output_rejects_missing_value_even_when_inputs_are_admissible():
    decision = "2026-09-27T08:00:00+00:00"
    base = ProviderResult(
        data={"close": 10.0},
        source="test",
        source_type="test",
        fetched_at=decision,
        available_time=decision,
    )
    quality = summarize_pit([base], decision)
    output = FactorOutput("momentum", "000001", None, decision, quality)
    assert output.admissible is False
