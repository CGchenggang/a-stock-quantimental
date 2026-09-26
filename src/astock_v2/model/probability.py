from dataclasses import dataclass
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge

@dataclass(frozen=True)
class ModelOutput:
    p_up: dict[int,float]
    expected_return: dict[int,float]
    version: str
    calibration_status: str="UNCALIBRATED"

class ProbabilityModel:
    def __init__(self, horizons=(1,3,5,10), c=0.5):
        self.horizons=tuple(horizons)
        self.models={h:LogisticRegression(C=c,max_iter=2000) for h in self.horizons}
        self.return_models={h:Ridge(alpha=1.0) for h in self.horizons}
        self.version="baseline-logistic-ridge-v2"
        self.features=[]

    def fit(self, X, targets: dict[int,tuple], y_returns: dict[int,object]):
        self.features=list(X.columns)
        xx=X.fillna(0)
        for h in self.horizons:
            y_up=targets[h]
            self.models[h].fit(xx,y_up.astype(int))
            self.return_models[h].fit(xx,y_returns[h].astype(float))
        return self

    def predict(self, X) -> ModelOutput:
        row=X[self.features].fillna(0)
        return ModelOutput(
            {h:float(self.models[h].predict_proba(row)[0,1]) for h in self.horizons},
            {h:float(self.return_models[h].predict(row)[0]) for h in self.horizons},
            self.version
        )
