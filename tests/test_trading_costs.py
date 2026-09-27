from astock_v2.trading_costs import TradingConstraints, execute_order

def test_buy_has_slippage_and_no_stamp_duty():
    r=execute_order(side="buy",shares=100,price=10,constraints=TradingConstraints())
    assert r.executed_shares==100
    assert r.execution_price>10
    assert r.stamp_duty==0
    assert r.total_cost>0

def test_sell_limit_down_is_blocked():
    r=execute_order(side="sell",shares=100,price=10,constraints=TradingConstraints(),limit_down=True)
    assert r.executed_shares==0
    assert r.blocked_reason=="LIMIT_DOWN"

def test_sell_rounds_to_lot_and_caps_position():
    r=execute_order(side="sell",shares=155,price=10,constraints=TradingConstraints(),available_shares=120)
    assert r.executed_shares==100
