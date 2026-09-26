from astock_v2.postmortem import build_postmortem

def test_postmortem_is_structured_and_non_mutating():
    p=build_postmortem("000001","2026-01-02",5,0.04,0.02,
                       causes=["REGIME_CHANGE"], data_quality_flags=["STALE"])
    assert p.outcome_horizon==5
    assert p.prediction==0.04
    assert "REGIME_CHANGE" in p.causes
