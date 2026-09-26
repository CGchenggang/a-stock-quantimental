from dataclasses import dataclass
import pandas as pd
@dataclass(frozen=True)
class Fold:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
def make_folds(index,train_years=3,test_years=1):
    years=sorted(pd.DatetimeIndex(index).year.unique()); folds=[]
    for i in range(train_years,len(years)-test_years+1):
        tr=years[i-train_years:i]; te=years[i:i+test_years]
        folds.append(Fold(f"{tr[0]}-01-01",f"{tr[-1]}-12-31",f"{te[0]}-01-01",f"{te[-1]}-12-31"))
    return folds
