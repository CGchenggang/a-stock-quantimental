import pandas as pd

def liquidity_factors(df: pd.DataFrame) -> pd.DataFrame:
    x=df.copy()
    close=x["close"].astype(float)
    volume=x["volume"].astype(float)
    x["turnover_proxy"]=close*volume
    x["volume_ma20"]=volume.rolling(20).mean()
    x["volume_ratio20"]=volume/x["volume_ma20"]
    x["amihud_proxy"]=close.pct_change().abs()/x["turnover_proxy"].replace(0,pd.NA)
    return x
