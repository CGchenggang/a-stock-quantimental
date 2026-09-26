import pandas as pd

REQUIRED = ["revenue_growth","profit_growth","roe","roic","ocf_to_profit",
            "debt_ratio","pe_percentile","pb_percentile","earnings_revision"]

def fundamental_factors(df):
    x = df.copy()
    for c in REQUIRED:
        if c not in x:
            x[c] = pd.NA
    x["quality"] = (
        x["roe"].astype(float)*0.30 +
        x["roic"].astype(float)*0.30 +
        x["ocf_to_profit"].astype(float)*0.20 -
        x["debt_ratio"].astype(float)*0.20
    )
    x["valuation"] = -(x["pe_percentile"].astype(float)+x["pb_percentile"].astype(float))/2
    return x
