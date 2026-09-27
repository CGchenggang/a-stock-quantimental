"""Out-of-sample performance metrics with explicit edge-case handling."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Sequence

@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    annualized_return: float | None
    volatility: float | None
    sharpe: float | None
    max_drawdown: float
    calmar: float | None
    win_rate: float | None
    observations: int
    def as_dict(self):
        return {"total_return":self.total_return,"annualized_return":self.annualized_return,
                "volatility":self.volatility,"sharpe":self.sharpe,"max_drawdown":self.max_drawdown,
                "calmar":self.calmar,"win_rate":self.win_rate,"observations":self.observations}

def performance_metrics(equity: Sequence[float], *, periods_per_year: int = 252) -> PerformanceMetrics:
    if len(equity)<2: raise ValueError("at least two equity observations are required")
    if periods_per_year<=0: raise ValueError("periods_per_year must be positive")
    if any(float(x)<=0 for x in equity): raise ValueError("equity observations must be positive")
    values=[float(x) for x in equity]
    returns=[b/a-1 for a,b in zip(values,values[1:])]
    total=values[-1]/values[0]-1
    years=len(returns)/periods_per_year
    annual=(1+total)**(1/years)-1 if years>0 and 1+total>0 else None
    vol=pstdev(returns)*sqrt(periods_per_year) if len(returns)>1 else None
    sharpe=(mean(returns)/pstdev(returns)*sqrt(periods_per_year)) if len(returns)>1 and pstdev(returns)>0 else None
    peak=values[0]; max_dd=0.0
    for value in values:
        peak=max(peak,value)
        max_dd=min(max_dd,value/peak-1)
    calmar=annual/abs(max_dd) if annual is not None and max_dd<0 else None
    win=sum(r>0 for r in returns)/len(returns) if returns else None
    return PerformanceMetrics(total,annual,vol,sharpe,max_dd,calmar,win,len(values))
