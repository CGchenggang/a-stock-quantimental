from astock_v2.model.ledger_metrics import aggregate_outcomes, aggregate_by_regime

def test_aggregate_outcomes():
    rows=[
        {"regime":"RANGE","expected_return":{"5":0.04},"outcomes":{"T+5":0.02}},
        {"regime":"RANGE","expected_return":{"5":0.02},"outcomes":{"T+5":0.01}},
        {"regime":"RISK_OFF","expected_return":{"5":0.03},"outcomes":{"T+5":-0.01}},
    ]
    x=aggregate_outcomes(rows,5)
    assert x["n"]==3
    assert abs(x["mean_actual_return"]-0.0066666666667)<1e-9
    by=aggregate_by_regime(rows,5)
    assert by["RANGE"]["n"]==2
    assert by["RISK_OFF"]["n"]==1
