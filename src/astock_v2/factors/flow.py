import pandas as pd

def flow_proxy_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Platform flow fields are treated as proxies, never objective 'main-force' facts."""
    x=df.copy()
    if "net_flow" in x:
        x["flow_proxy"]=x["net_flow"].astype(float)
    elif {"close","volume"}.issubset(x.columns):
        x["flow_proxy"]=x["close"].pct_change()*x["volume"]
    else:
        x["flow_proxy"]=pd.NA
    return x
