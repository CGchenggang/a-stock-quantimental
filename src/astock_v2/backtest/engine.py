from dataclasses import dataclass
import pandas as pd

@dataclass
class BacktestResult:
    hit_rate: float
    avg_return: float
    median_return: float
    max_drawdown: float
    n: int

def evaluate_signals(df, signal_col="signal", horizon=5):
    r = df["close"].shift(-horizon)/df["close"] - 1
    mask = df[signal_col].astype(bool) & r.notna()
    x = r[mask]
    if x.empty:
        return BacktestResult(0,0,0,0,0)
    equity=(1+x.clip(lower=-1)).cumprod()
    dd=equity/equity.cummax()-1
    return BacktestResult(float((x>0).mean()),float(x.mean()),
                          float(x.median()),float(dd.min()),int(len(x)))
