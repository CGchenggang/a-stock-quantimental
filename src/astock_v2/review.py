from datetime import datetime, timedelta, timezone

HORIZONS=(1,3,5,10)

def due_horizons(decision_time, now=None, completed=None):
    """Return review horizons whose calendar time has arrived."""
    start=datetime.fromisoformat(decision_time.replace("Z","+00:00"))
    current=now or datetime.now(timezone.utc)
    done=set(completed or [])
    return [h for h in HORIZONS if start+timedelta(days=h) <= current and h not in done]


from dataclasses import dataclass
from .recommendation import RecommendationRecord, LedgerReview

@dataclass(frozen=True)
class ReviewWindow:
    start_time: str
    end_time: str
    horizon_bars: int

def build_review_window(decision_time: str, *, end_time: str, horizon_bars: int) -> ReviewWindow:
    if not decision_time or not end_time or horizon_bars <= 0 or end_time < decision_time:
        raise ValueError("invalid review window")
    return ReviewWindow(decision_time, end_time, horizon_bars)

def make_review(record: RecommendationRecord, *, review_time: str, entry_price: float, exit_price: float) -> LedgerReview:
    if entry_price <= 0 or exit_price <= 0: raise ValueError("prices must be positive")
    ret=exit_price/entry_price-1.0
    signed=ret if record.action != "SELL" else -ret
    outcome="UNRESOLVED" if record.action == "NO_ACTION" or signed == 0 else ("CORRECT" if signed > 0 else "INCORRECT")
    return LedgerReview(record.record_id,review_time,signed,outcome,"price-to-price realized return")
