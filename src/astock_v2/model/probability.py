from dataclasses import dataclass
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge

@dataclass
class ModelOutput:
    p_up: float
    expected_return: float
    version: str

class ProbabilityModel:
    def __init__(self, c=0.5):
        self.cls = LogisticRegression(C=c, max_iter=2000)
        self.ret = Ridge(alpha=1.0)
        self.version = "baseline-logistic-ridge-v1"
        self.features = []

    def fit(self, X, y_up, y_ret):
        self.features = list(X.columns)
        self.cls.fit(X.fillna(0), y_up.astype(int))
        self.ret.fit(X.fillna(0), y_ret.astype(float))
        return self

    def predict(self, X):
        row = X[self.features].fillna(0)
        return ModelOutput(
            float(self.cls.predict_proba(row)[0,1]),
            float(self.ret.predict(row)[0]),
            self.version
        )
