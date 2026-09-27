"""Public backtest API.

The package-level API exposes the PIT-aware execution engine.  The legacy
DataFrame simulator remains available from :mod:`astock_v2.backtest.engine`.
"""
from ..backtest import BacktestBar, BacktestResult, BacktestTrade, run_signal_backtest

__all__ = ["BacktestBar", "BacktestResult", "BacktestTrade", "run_signal_backtest"]
