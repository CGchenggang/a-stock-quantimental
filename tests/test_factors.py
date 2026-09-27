from astock_v2.data.providers import ProviderResult
from astock_v2.factors import compute_factor

DECISION="2026-09-27T15:00:00+00:00"

def provider(rows, available=DECISION, fallback=False):
    return ProviderResult(data=rows,source="fixture",source_type="historical",fetched_at=DECISION,available_time=available,fallback=fallback)

def rows(n=21):
    return [{"close":100+i,"volume":1000+i*10} for i in range(n)]

def test_momentum_is_pit_admissible_and_deterministic():
    out=compute_factor("momentum",provider(rows()),symbol="000001",decision_time=DECISION,lookback=20)
    assert round(out.value,8)==round(120/100-1,8)
    assert out.admissible

def test_trend_and_volume_ratio_are_calculated_from_explicit_rows():
    data=rows(21)
    trend=compute_factor("trend",provider(data),symbol="000001",decision_time=DECISION,lookback=20)
    volume=compute_factor("volume_ratio",provider(data),symbol="000001",decision_time=DECISION,lookback=20)
    assert trend.value is not None and volume.value is not None
    assert volume.value>0

def test_volatility_uses_log_returns():
    out=compute_factor("volatility",provider(rows(21)),symbol="000001",decision_time=DECISION,lookback=20)
    assert out.value is not None and out.value>=0

def test_future_input_cannot_produce_factor_value():
    future="2026-09-27T15:00:01+00:00"
    out=compute_factor("momentum",provider(rows(),future),symbol="000001",decision_time=DECISION,lookback=20)
    assert out.value is None and not out.admissible

def test_fallback_input_cannot_produce_factor_value():
    out=compute_factor("momentum",provider(rows(),fallback=True),symbol="000001",decision_time=DECISION,lookback=20)
    assert out.value is None and not out.admissible

def test_insufficient_history_is_not_fabricated():
    out=compute_factor("momentum",provider(rows(5)),symbol="000001",decision_time=DECISION,lookback=20)
    assert out.value is None and not out.admissible
