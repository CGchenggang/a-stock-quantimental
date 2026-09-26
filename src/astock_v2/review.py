from datetime import datetime, timedelta, timezone

HORIZONS=(1,3,5,10)

def due_horizons(decision_time, now=None, completed=None):
    """Return review horizons whose calendar time has arrived."""
    start=datetime.fromisoformat(decision_time.replace("Z","+00:00"))
    current=now or datetime.now(timezone.utc)
    done=set(completed or [])
    return [h for h in HORIZONS if start+timedelta(days=h) <= current and h not in done]
