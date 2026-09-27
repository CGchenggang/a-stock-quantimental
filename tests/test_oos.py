from astock_v2.oos import evaluate_oos_predictions
from astock_v2.pipeline import OOSPrediction

def test_oos_evaluation_reports_accuracy_and_brier():
    report=evaluate_oos_predictions((OOSPrediction(1,.8,1),OOSPrediction(2,.2,0)))
    assert report.classification_accuracy==1.0
    assert report.brier_score < .05
