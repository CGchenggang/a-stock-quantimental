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

from astock_v2.backtest import BacktestBar, run_signal_backtest
from astock_v2.trading_costs import TradingConstraints

def test_signal_backtest_respects_limit_up():
    bars=[BacktestBar("2026-01-01T09:30:00+00:00","2026-01-01T09:31:00+00:00","000001",10,1,limit_up=True)]
    result=run_signal_backtest(bars,initial_cash=10000,target_shares=100, constraints=TradingConstraints())
    assert result.trades[0].blocked_reason=="LIMIT_UP"
    assert result.final_positions["000001"]==0

def test_signal_backtest_respects_t_plus_one():
    bars=[
      BacktestBar("2026-01-01T09:30:00+00:00","2026-01-01T09:31:00+00:00","000001",10,1),
      BacktestBar("2026-01-01T10:00:00+00:00","2026-01-01T10:01:00+00:00","000001",10,0),
    ]
    result=run_signal_backtest(bars,initial_cash=10000,target_shares=100, constraints=TradingConstraints())
    assert result.trades[1].blocked_reason=="T_PLUS_ONE"
    assert result.final_positions["000001"]==100

def test_signal_backtest_rejects_execution_before_decision():
    bars=[BacktestBar("2026-01-01T09:31:00+00:00","2026-01-01T09:30:00+00:00","000001",10,1)]
    try: run_signal_backtest(bars)
    except ValueError: return
    assert False
