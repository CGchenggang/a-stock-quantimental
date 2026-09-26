import pandas as pd
from astock_v2.backtest.engine import simulate_long_only

def test_backtest_respects_missing_columns():
    try: simulate_long_only(pd.DataFrame({"close":[1,2]}))
    except ValueError: return
    assert False

def test_backtest_runs():
    df=pd.DataFrame({"open":[10,10,11,11,12],"close":[10,11,11,12,12],
                     "signal":[0,1,1,0,0],"suspended":[False]*5,
                     "limit_up_blocked":[False]*5,"limit_down_blocked":[False]*5})
    r=simulate_long_only(df)
    assert r.n_trades>=1
