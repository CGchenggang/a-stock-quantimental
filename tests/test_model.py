import numpy as np
import pandas as pd
from astock_v2.model.probability import ProbabilityModel

def test_multi_horizon_model():
    rng=np.random.default_rng(1)
    X=pd.DataFrame(rng.normal(size=(80,3)),columns=["a","b","c"])
    targets={h:pd.Series((X["a"]>0).astype(int)) for h in (1,3,5,10)}
    returns={h:X["a"]*0.01 for h in (1,3,5,10)}
    m=ProbabilityModel()
    m.fit(X,targets,returns)
    out=m.predict(X.iloc[[0]])
    assert set(out.p_up)=={1,3,5,10}
    assert out.calibration_status=="UNCALIBRATED"
