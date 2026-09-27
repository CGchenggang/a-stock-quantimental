"""A-share execution cost and trading-constraint primitives for backtests."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TradingConstraints:
    commission_rate: float = 0.0003
    stamp_duty_rate: float = 0.0005
    transfer_fee_rate: float = 0.00001
    slippage_rate: float = 0.0005
    lot_size: int = 100
    t_plus_one: bool = True
    limit_pct: float = 0.10

    def __post_init__(self) -> None:
        for name in ("commission_rate","stamp_duty_rate","transfer_fee_rate","slippage_rate","limit_pct"):
            if getattr(self, name) < 0: raise ValueError(f"{name} must be non-negative")
        if self.lot_size <= 0: raise ValueError("lot_size must be positive")
        if self.limit_pct <= 0: raise ValueError("limit_pct must be positive")

@dataclass(frozen=True)
class ExecutionResult:
    requested_shares: int
    executed_shares: int
    execution_price: float
    commission: float
    stamp_duty: float
    transfer_fee: float
    slippage_cost: float
    total_cost: float
    blocked_reason: str | None = None

def round_lot(shares: int, lot_size: int = 100) -> int:
    if shares < 0: raise ValueError("shares must be non-negative")
    if lot_size <= 0: raise ValueError("lot_size must be positive")
    return shares // lot_size * lot_size

def execute_order(*, side: str, shares: int, price: float, constraints: TradingConstraints,
                  limit_up: bool = False, limit_down: bool = False,
                  suspended: bool = False, available_shares: int | None = None) -> ExecutionResult:
    side = side.lower()
    if side not in {"buy","sell"}: raise ValueError("side must be buy or sell")
    if shares < 0 or price <= 0: raise ValueError("shares must be non-negative and price positive")
    if suspended: return ExecutionResult(shares,0,price,0,0,0,0,0,"SUSPENDED")
    if side == "buy" and limit_up: return ExecutionResult(shares,0,price,0,0,0,0,0,"LIMIT_UP")
    if side == "sell" and limit_down: return ExecutionResult(shares,0,price,0,0,0,0,0,"LIMIT_DOWN")
    if side == "sell" and available_shares is not None:
        shares = min(shares, max(0, available_shares))
    executed = round_lot(shares, constraints.lot_size)
    if executed == 0: return ExecutionResult(shares,0,price,0,0,0,0,0,"LOT_SIZE")
    exec_price = price * (1 + constraints.slippage_rate if side == "buy" else 1 - constraints.slippage_rate)
    notional = executed * exec_price
    commission = notional * constraints.commission_rate
    stamp = notional * constraints.stamp_duty_rate if side == "sell" else 0.0
    transfer = notional * constraints.transfer_fee_rate
    slippage = executed * abs(exec_price-price)
    return ExecutionResult(shares,executed,exec_price,commission,stamp,transfer,slippage,
                           commission+stamp+transfer+slippage)

def net_cash_delta(*, side: str, execution: ExecutionResult) -> float:
    gross = execution.executed_shares * execution.execution_price
    return -(gross + execution.commission + execution.stamp_duty + execution.transfer_fee) if side.lower()=="buy" else gross - execution.commission - execution.stamp_duty - execution.transfer_fee
