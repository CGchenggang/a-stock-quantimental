from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class BacktestResult:
    hit_rate: float
    avg_return: float
    median_return: float
    profit_factor: float
    sharpe: float
    max_drawdown: float
    turnover: float
    n_trades: int

def _sharpe(r: pd.Series) -> float:
    if len(r)<2 or r.std(ddof=1)==0:return 0.0
    return float(np.sqrt(252)*r.mean()/r.std(ddof=1))

def simulate_long_only(df: pd.DataFrame, signal_col="signal", fee_bps=3.0,
                       slippage_bps=5.0, hold_days=1) -> BacktestResult:
    required={"open","close",signal_col}
    missing=required-set(df.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    x=df.reset_index(drop=True).copy()
    x["target"]=x[signal_col].astype(bool)
    equity=1.0; daily=[]; trades=0; turnover=0.0; position=False; age=0
    for i in range(len(x)-1):
        desired=bool(x.loc[i,"target"])
        next_row=x.loc[i+1]
        suspended=bool(next_row.get("suspended",False))
        buy_block=bool(next_row.get("limit_up_blocked",False))
        sell_block=bool(next_row.get("limit_down_blocked",False))
        if desired and not position and not suspended and not buy_block:
            position=True; age=0; trades+=1; turnover+=1
            entry=float(next_row["open"])*(1+slippage_bps/10000)+fee_bps/10000
        elif (not desired) and position and age>=hold_days and not suspended and not sell_block:
            position=False; age=0; trades+=1; turnover+=1
        if position:
            age+=1
            ret=float(next_row["close"])/float(next_row["open"])-1
            daily.append(ret-fee_bps/10000 if i>0 else ret)
            equity*=1+daily[-1]
        else:
            daily.append(0.0)
    r=pd.Series(daily,dtype=float)
    gains=r[r>0].sum(); losses=-r[r<0].sum()
    pf=float(gains/losses) if losses else float("inf") if gains else 0.0
    eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
    return BacktestResult(float((r>0).mean()) if len(r) else 0.0,float(r.mean()) if len(r) else 0.0,
                          float(r.median()) if len(r) else 0.0,pf,_sharpe(r),float(dd.min()) if len(dd) else 0.0,
                          turnover/max(1,len(x)),trades)

def evaluate_signals(df, signal_col="signal", horizon=5):
    r=df["close"].shift(-horizon)/df["close"]-1
    mask=df[signal_col].astype(bool)&r.notna()
    x=r[mask]
    if x.empty:return BacktestResult(0,0,0,0,0,0,0,0)
    eq=(1+x.clip(lower=-1)).cumprod(); dd=eq/eq.cummax()-1
    return BacktestResult(float((x>0).mean()),float(x.mean()),float(x.median()),0.0,_sharpe(x),float(dd.min()),0.0,int(len(x)))