import pandas as pd

def momentum_factors(df: pd.DataFrame) -> pd.DataFrame:
    x=df.copy(); close=x["close"].astype(float)
    for n in (1,3,5,10,20,60):
        x[f"momentum_{n}d"]=close.pct_change(n)
    x["drawdown_60d"]=close/close.rolling(60).max()-1
    return x
