from datetime import datetime, timezone
from astock_v2.ledger import RecommendationLedger
from astock_v2.types import DecisionPacket
from astock_v2.review import due_horizons

def test_p7_due_review_and_backfill(tmp_path):
    p=DecisionPacket("000001","2026-01-02T00:00:00+00:00","m1",
                     {1:.6,3:.6,5:.6,10:.6},{1:.01,3:.02,5:.03,10:.04},
                     .03,.08,"RANGE",.9)
    ledger=RecommendationLedger(tmp_path/"ledger.jsonl")
    ledger.append(p, "f1")
    assert due_horizons("2026-01-02T00:00:00+00:00",
                        datetime(2026,1,7,tzinfo=timezone.utc),
                        completed=[1]) == [3,5]
    assert ledger.backfill_returns("000001","2026-01-02T00:00:00+00:00",
                                   {"decision":10,1:10.1,3:10.3,5:10.5,10:11})
    row=ledger.load()[0]
    assert row["p_up"]["5"]==.6
    assert row["outcomes"]["T+5"]==.05
