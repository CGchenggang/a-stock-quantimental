from astock_v2.metrics import performance_metrics

def test_performance_metrics_basic():
    m=performance_metrics([100,110,105,120])
    assert m.total_return==0.2
    assert m.max_drawdown < 0
    assert m.win_rate==2/3

def test_flat_series_has_no_sharpe_or_calmar():
    m=performance_metrics([100,100,100])
    assert m.sharpe is None
    assert m.calmar is None
