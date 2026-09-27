from astock_v2.data.providers import ProviderResult
from astock_v2.leakage import audit_provider_results, assert_no_pit_leakage

def test_leakage_audit_flags_future_input():
    results=[
      ProviderResult(data={},source="hist",source_type="historical",fetched_at="2026-01-02T00:00:00+00:00",available_time="2026-01-01T00:00:00+00:00"),
      ProviderResult(data={},source="future",source_type="historical",fetched_at="2026-01-03T00:00:00+00:00",available_time="2026-01-03T00:00:00+00:00"),
    ]
    audit=audit_provider_results(results,"2026-01-02T00:00:00+00:00")
    assert audit.passed is False
    assert audit.findings[0].status.value=="FUTURE"

def test_leakage_audit_passes_all_admissible():
    result=ProviderResult(data={},source="hist",source_type="historical",fetched_at="2026-01-02T00:00:00+00:00",available_time="2026-01-01T00:00:00+00:00")
    assert assert_no_pit_leakage([result],"2026-01-02T00:00:00+00:00").passed
