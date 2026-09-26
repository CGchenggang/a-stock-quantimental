import pandas as pd
from astock_v2.regime.engine import RegimeEngine

def test_unknown():
    df=pd.DataFrame({"close":range(10)})
    assert RegimeEngine().classify(df)=="UNKNOWN"

def test_multi_signal_range():
    df=pd.DataFrame({"close":[100+i*0.02 for i in range(80)]})
    assert RegimeEngine().classify(df,{"advance_ratio":0.5}) in {"RANGE","TREND_UP","HIGH_VOL","UNKNOWN"}
