from astock_v2.data.providers import ProviderResult
from astock_v2.factor_contracts import FactorOutput
from astock_v2.data_quality import summarize_pit
from astock_v2.probability import fit_logistic_probability_model

T="2026-09-27T15:00:00+00:00"

def factor(name,value):
    q=summarize_pit([ProviderResult(data={},source="fixture",source_type="hist",fetched_at=T,available_time=T)],T)
    return FactorOutput(name,"000001",value,T,q)

def test_logistic_probability_model_learns_direction():
    rows=[]; labels=[]
    for x,y in [(-2,0),(-1,0),(-0.5,0),(0.5,1),(1,1),(2,1)]:
        rows.append({"momentum":factor("momentum",x)})
        labels.append(y)
    model=fit_logistic_probability_model(rows,labels,factor_names=["momentum"],epochs=1000,learning_rate=0.1)
    low=model.predict([factor("momentum",-2)])
    high=model.predict([factor("momentum",2)])
    assert 0<=low<high<=1

def test_probability_training_rejects_future_factor():
    future_q=summarize_pit([ProviderResult(data={},source="fixture",source_type="hist",fetched_at=T,available_time="2026-09-27T15:00:01+00:00")],T)
    rows=[{"momentum":FactorOutput("momentum","000001",1,T,future_q)}]
    try:
        fit_logistic_probability_model(rows,[1],factor_names=["momentum"])
    except ValueError as exc:
        assert "inadmissible" in str(exc)
    else:
        raise AssertionError("future factor must block training")
