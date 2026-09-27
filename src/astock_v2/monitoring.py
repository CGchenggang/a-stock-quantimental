"""Model and factor drift monitoring primitives."""
from __future__ import annotations
from dataclasses import dataclass
from math import log
from statistics import mean, pstdev
from typing import Sequence

@dataclass(frozen=True)
class DriftReport:
    metric: str
    value: float
    threshold: float
    drifted: bool
    observations: int
    def as_dict(self):
        return {"metric":self.metric,"value":self.value,"threshold":self.threshold,"drifted":self.drifted,"observations":self.observations}

def standardized_mean_shift(reference: Sequence[float], current: Sequence[float]) -> DriftReport:
    if not reference or not current: raise ValueError("reference and current must be non-empty")
    ref_sd=pstdev(reference)
    value=abs(mean(current)-mean(reference))/(ref_sd if ref_sd>0 else 1.0)
    return DriftReport("standardized_mean_shift",value,2.0,value>=2.0,len(current))

def probability_distribution_shift(reference: Sequence[float], current: Sequence[float]) -> DriftReport:
    if not reference or not current: raise ValueError("reference and current must be non-empty")
    def entropy_mean(xs):
        return mean(max(1e-12,min(1-1e-12,float(x))) for x in xs)
    # Compare Bernoulli cross-entropy-like mean probabilities; this is a monitoring signal, not a calibrated test.
    value=abs(entropy_mean(current)-entropy_mean(reference))
    return DriftReport("mean_probability_shift",value,0.10,value>=0.10,len(current))

def population_stability_index(reference: Sequence[float], current: Sequence[float], *, bins: int = 10) -> DriftReport:
    if not reference or not current or bins < 2: raise ValueError("invalid PSI inputs")
    combined=sorted(float(x) for x in reference)
    edges=[combined[0]+(combined[-1]-combined[0])*i/bins for i in range(bins+1)]
    def counts(xs):
        out=[0]*bins
        for x in xs:
            idx=min(bins-1,max(0,next((i for i in range(bins) if x <= edges[i+1]),bins-1)))
            out[idx]+=1
        return out
    rc,cc=counts(reference),counts(current)
    rn,cn=len(reference),len(current)
    psi=0.0
    for r,c in zip(rc,cc):
        rp=max(r/rn,1e-6); cp=max(c/cn,1e-6)
        psi+=(cp-rp)*log(cp/rp)
    return DriftReport("psi",psi,0.20,psi>=0.20,len(current))
