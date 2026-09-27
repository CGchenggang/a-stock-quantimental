from astock_v2.recommendation import RecommendationRecord
from astock_v2.review import build_review_window, make_review

def test_review_window_rejects_backwards_time():
    try: build_review_window("2026-01-02",end_time="2026-01-01",horizon_bars=1)
    except ValueError: return
    assert False

def test_buy_review_is_correct_when_return_positive():
    r=RecommendationRecord("r1","000001","2026-01-01","BUY",.7,.8,"x","m1",{})
    review=make_review(r,review_time="2026-01-03",entry_price=10,exit_price=11)
    assert review.outcome=="CORRECT"
    assert review.realized_return==.1
