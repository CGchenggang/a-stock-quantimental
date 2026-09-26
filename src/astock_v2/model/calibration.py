import numpy as np

def brier_score(y_true, p):
    y, p = np.asarray(y_true, float), np.asarray(p, float)
    return float(np.mean((p-y)**2))

def reliability_bins(y_true, p, bins=10):
    y, p = np.asarray(y_true), np.asarray(p)
    edges = np.linspace(0,1,bins+1)
    rows=[]
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask=(p>=lo)&((p<hi) if hi<1 else (p<=hi))
        if mask.any():
            rows.append({"lo":lo,"hi":hi,"n":int(mask.sum()),
                         "pred":float(p[mask].mean()),"actual":float(y[mask].mean())})
    return rows
