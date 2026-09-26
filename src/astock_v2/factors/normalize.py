import numpy as np
import pandas as pd

def winsorize(s, lower=0.01, upper=0.99):
    return s.clip(s.quantile(lower), s.quantile(upper))

def zscore(s):
    s = winsorize(s.astype(float))
    std = s.std(ddof=0)
    return s*0 if std == 0 or np.isnan(std) else (s-s.mean())/std

def normalize_frame(df, cols):
    x = df.copy()
    for c in cols:
        if c in x:
            x[c] = zscore(x[c])
    return x
