from astock_v2.ledger import RecommendationLedger
from astock_v2.recommendation import RecommendationRecord

def test_ledger_is_append_only(tmp_path):
    ledger=RecommendationLedger(tmp_path/"r.jsonl")
    r=RecommendationRecord("r1","000001","2026-01-01","HOLD",.7,.8,"x","m1",{})
    ledger.append(r)
    assert len(ledger.records())==1
    ledger.backfill_returns("000001","2026-01-01",{"decision":10,1:11})
    rows=ledger.records()
    assert len(rows)==2
    assert rows[0]["type"]=="recommendation"
    assert rows[1]["type"]=="outcome"
