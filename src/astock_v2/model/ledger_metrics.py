import numpy as np

def aggregate_outcomes(rows, horizon):
    """Aggregate realized outcomes from ledger rows without altering snapshots."""
    key=f"T+{int(horizon)}"
    realized=[]
    predicted=[]
    errors=[]
    for row in rows:
        outcomes=row.get("outcomes", {})
        if key not in outcomes:
            continue
        actual=float(outcomes[key])
        expected=float(row.get("expected_return", {}).get(str(horizon),
                         row.get("expected_return", {}).get(int(horizon), 0.0)))
        realized.append(actual)
        predicted.append(expected)
        errors.append(actual-expected)
    if not realized:
        return {"horizon":int(horizon),"n":0}
    return {
        "horizon":int(horizon),
        "n":len(realized),
        "mean_actual_return":float(np.mean(realized)),
        "mean_expected_return":float(np.mean(predicted)),
        "mean_return_error":float(np.mean(errors)),
        "mean_abs_return_error":float(np.mean(np.abs(errors))),
    }

def aggregate_by_regime(rows, horizon):
    result={}
    for row in rows:
        regime=row.get("regime","UNKNOWN")
        result.setdefault(regime, []).append(row)
    return {regime: aggregate_outcomes(items,horizon) for regime,items in result.items()}
