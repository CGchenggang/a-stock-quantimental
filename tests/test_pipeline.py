from astock_v2.factor_contracts import FactorOutput
from astock_v2.data_quality import DataQualitySummary
from astock_v2.pipeline import run_walk_forward_probability

def _row(i, x):
    q=DataQualitySummary(1,1,{"ADMISSIBLE":1},1.0,True)
    return {"momentum":FactorOutput("momentum","000001",x,f"2026-01-{i:02d}",q)}

def test_walk_forward_probability_produces_only_oos_predictions():
    rows=[_row(i, float(i)/10) for i in range(1,9)]
    labels=[0,0,0,0,1,1,1,1]
    report=run_walk_forward_probability(rows,labels,factor_names=["momentum"],train_size=4,test_size=2)
    assert len(report.predictions)==4
    assert all(p.test_index>=4 for p in report.predictions)
    assert report.calibration is not None
