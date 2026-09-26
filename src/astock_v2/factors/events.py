import pandas as pd

EVENT_WEIGHTS = {
    "earnings_surprise": 1.0, "earnings_revision": 0.9,
    "major_contract": 0.7, "buyback": 0.5, "insider_purchase": 0.5,
    "reduction": -0.6, "unlock": -0.4,
    "regulatory_penalty": -0.9, "litigation": -0.5, "restructuring": 0.2,
}

def event_factor(events):
    if events.empty:
        return pd.DataFrame(columns=["symbol","event_score"])
    x = events.copy()
    x["base"] = x["event_type"].map(EVENT_WEIGHTS).fillna(0)
    x["event_score"] = x["base"] * x["direction"].astype(float) * x["confidence"].astype(float)
    return x.groupby("symbol", as_index=False)["event_score"].sum()
