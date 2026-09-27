"""Point-in-time-safe backtest execution primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..trading_costs import TradingConstraints, execute_order, net_cash_delta


@dataclass(frozen=True)
class BacktestBar:
    decision_time: str
    execution_time: str
    symbol: str
    close: float
    signal: float
    tradable: bool = True
    limit_up: bool = False
    limit_down: bool = False
    suspended: bool = False


@dataclass(frozen=True)
class BacktestTrade:
    execution_time: str
    symbol: str
    side: str
    requested_shares: int
    executed_shares: int
    price: float
    costs: float
    blocked_reason: str | None


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_cash: float
    final_positions: dict[str, int]
    equity_curve: tuple[float, ...]
    trades: tuple[BacktestTrade, ...]


def run_signal_backtest(
    bars: Sequence[BacktestBar],
    *,
    initial_cash: float = 1_000_000.0,
    target_shares: int = 100,
    constraints: TradingConstraints | None = None,
) -> BacktestResult:
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive")
    if target_shares < 0:
        raise ValueError("target_shares must be non-negative")

    constraints = constraints or TradingConstraints()
    cash = initial_cash
    positions: dict[str, int] = {}
    acquired_dates: dict[str, str] = {}
    trades: list[BacktestTrade] = []
    equity: list[float] = []
    latest_prices: dict[str, float] = {}
    last_execution_time = None

    for bar in bars:
        if last_execution_time is not None and bar.execution_time < last_execution_time:
            raise ValueError("bars must be ordered by execution_time")
        if bar.execution_time < bar.decision_time:
            raise ValueError("execution_time cannot precede decision_time")

        last_execution_time = bar.execution_time
        latest_prices[bar.symbol] = float(bar.close)
        current = positions.get(bar.symbol, 0)
        execution_date = bar.execution_time[:10]
        desired = target_shares if bar.signal > 0 else 0
        delta = desired - current

        if delta:
            side = "buy" if delta > 0 else "sell"
            requested = abs(delta)

            if not bar.tradable or bar.suspended:
                result = execute_order(
                    side=side, shares=requested, price=bar.close,
                    constraints=constraints, suspended=True,
                )
            elif side == "sell" and constraints.t_plus_one and acquired_dates.get(bar.symbol) == execution_date:
                result = execute_order(
                    side=side, shares=requested, price=bar.close,
                    constraints=constraints, available_shares=0,
                )
                result = type(result)(
                    result.requested_shares, result.executed_shares,
                    result.execution_price, result.commission, result.stamp_duty,
                    result.transfer_fee, result.slippage_cost, result.total_cost,
                    "T_PLUS_ONE",
                )
            else:
                result = execute_order(
                    side=side, shares=requested, price=bar.close,
                    constraints=constraints, limit_up=bar.limit_up,
                    limit_down=bar.limit_down, suspended=bar.suspended,
                    available_shares=current if side == "sell" else None,
                )

            if side == "buy" and result.executed_shares:
                required_cash = -net_cash_delta(side=side, execution=result)
                if required_cash > cash:
                    affordable = int(
                        cash / (
                            result.execution_price
                            * (1 + constraints.commission_rate + constraints.transfer_fee_rate)
                        )
                    )
                    result = execute_order(
                        side=side, shares=affordable, price=bar.close,
                        constraints=constraints, limit_up=bar.limit_up,
                        limit_down=bar.limit_down, suspended=bar.suspended,
                    )

            cash += net_cash_delta(side=side, execution=result)
            positions[bar.symbol] = current + result.executed_shares * (1 if side == "buy" else -1)

            if side == "buy" and result.executed_shares:
                acquired_dates[bar.symbol] = execution_date

            trades.append(
                BacktestTrade(
                    bar.execution_time, bar.symbol, side,
                    result.requested_shares, result.executed_shares,
                    result.execution_price, result.total_cost, result.blocked_reason,
                )
            )

        marked_value = cash + sum(
            shares * latest_prices.get(sym, 0.0)
            for sym, shares in positions.items()
        )
        equity.append(marked_value)

    return BacktestResult(
        initial_cash, cash, dict(positions), tuple(equity), tuple(trades)
    )
