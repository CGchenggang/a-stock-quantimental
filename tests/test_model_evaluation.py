from astock_v2.model.evaluation import prediction_reality

def test_prediction_reality():
    result=prediction_reality([1,0,1],[0.8,0.4,0.7],[0.02,-0.01,0.03],[0.01,0.01,0.02])
    assert result["n"]==3
    assert result["brier"] > 0
    assert "mean_abs_return_error" in result
