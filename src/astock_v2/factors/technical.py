import numpy as np
import pandas as pd

def technical_factors(df):
    x = df.copy()
    close = x["close"].astype(float)
    volume = x["volume"].astype(float)
    for n in (5, 20, 60):
        x[f"ret_{n}"] = close.pct_change(n)
        x[f"ma_gap_{n}"] = close / close.rolling(n).mean() - 1
    x["vol_z20"] = (volume-volume.rolling(20).mean()) / volume.rolling(20).std()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["rsi14"] = 100 - 100/(1+rs)
    return x.replace([np.inf, -np.inf], np.nan)
