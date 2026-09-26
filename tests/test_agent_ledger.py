from astock_v2.ledger import RecommendationLedger
from astock_v2.types import DecisionPacket

def packet():
    return DecisionPacket(
        symbol="000001",
        decision_time="2026-01-02",
        model_version="m1",
        p_up={1:0.55,3:0.60,5:0.65,10:0.58},
        expected_return={1:0.01,3:0.02,5:0.04,10:0.05},
        expected_volatility=0.03,
        expected_drawdown=0.08,
        regime="RANGE",
        data_quality=0.9,
        risk_flags=["EVENT"],
        evidence=[{"kind":"supporting","text":"example"}],
        invalidation=["regime_change"],
        decision_class="RESEARCH",
    )

def test_snapshot_and_outcome_backfill(tmp_path):
    ledger=RecommendationLedger(tmp_path/"ledger.jsonl")
    row=ledger.append(packet(), feature_version="f1", input_snapshot={"source":"test"})
    assert row["feature_version"]=="f1"
    assert row["outcomes"]=={}
    assert ledger.backfill_returns("000001","2026-01-02",
                                    {"decision":10,1:10.2,3:10.4})
    # JSON object keys may be strings; the public method also accepts integer keys.
    loaded=ledger.load()
    assert loaded[0]["outcomes"]["T+1"]==0.02
    assert loaded[0]["outcomes"]["T+3"]==0.04
