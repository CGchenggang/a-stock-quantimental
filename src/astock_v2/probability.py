"""Small dependency-free baseline probability model for P4."""
from __future__ import annotations
from dataclasses import dataclass
from math import exp
from typing import Mapping, Sequence
from .factor_contracts import FactorOutput
from .probability_inputs import gate_probability_inputs


def _sigmoid(x: float) -> float:
    if x >= 0:
        z=exp(-x); return 1.0/(1.0+z)
    z=exp(x); return z/(1.0+z)

@dataclass(frozen=True)
class LogisticProbabilityModel:
    factor_names: tuple[str, ...]
    coefficients: tuple[float, ...]
    intercept: float
    trained_rows: int
    learning_rate: float
    epochs: int

    def predict(self, factors: Sequence[FactorOutput]) -> float:
        gate=gate_probability_inputs(factors,required_names=self.factor_names)
        if not gate.ready: raise ValueError("probability inputs are not ready")
        values={item.name:item.value for item in gate.admitted}
        score=self.intercept+sum(w*float(values[name]) for w,name in zip(self.coefficients,self.factor_names))
        return _sigmoid(score)


def fit_logistic_probability_model(rows: Sequence[Mapping[str, FactorOutput]], labels: Sequence[int], *, factor_names: Sequence[str], learning_rate: float=0.05, epochs: int=500) -> LogisticProbabilityModel:
    names=tuple(factor_names)
    if not names: raise ValueError("factor_names must not be empty")
    if len(rows)!=len(labels) or not rows: raise ValueError("rows and labels must have equal non-zero length")
    if any(label not in (0,1) for label in labels): raise ValueError("labels must be 0 or 1")
    matrix=[]
    for row in rows:
        gate=gate_probability_inputs(row.values(),required_names=names)
        if not gate.ready: raise ValueError("training row contains inadmissible or missing factors")
        values={item.name:item.value for item in gate.admitted}
        matrix.append([float(values[name]) for name in names])
    weights=[0.0]*len(names); intercept=0.0; n=float(len(rows))
    for _ in range(epochs):
        grad_w=[0.0]*len(names); grad_b=0.0
        for x,y in zip(matrix,labels):
            p=_sigmoid(intercept+sum(w*v for w,v in zip(weights,x))); error=p-y
            grad_b+=error
            for i,v in enumerate(x): grad_w[i]+=error*v
        intercept-=learning_rate*grad_b/n
        weights=[w-learning_rate*g/n for w,g in zip(weights,grad_w)]
    return LogisticProbabilityModel(names,tuple(weights),intercept,len(rows),learning_rate,epochs)
