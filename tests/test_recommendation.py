from astock_v2.recommendation import RecommendationRecord, LedgerReview, close_review

def test_recommendation_record_is_auditable():
    r=RecommendationRecord("r1","000001","2026-01-01T09:30:00+00:00","BUY",.7,.8,"momentum","m1",{"pit_admissible":True},("hist",))
    assert r.as_dict()["provenance"]==["hist"]

def test_review_updates_status_without_changing_decision():
    r=RecommendationRecord("r1","000001","2026-01-01T09:30:00+00:00","BUY",.7,.8,"momentum","m1",{"pit_admissible":True})
    closed=close_review(r,LedgerReview("r1","2026-01-10T00:00:00+00:00",.05,"CORRECT"))
    assert closed.review_status=="CORRECT"
    assert closed.action=="BUY"
