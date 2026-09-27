from astock_v2.calibration import calibration_report

def test_calibration_report_returns_brier_and_nonempty_bins():
    report=calibration_report([0.1,0.2,0.8,0.9],[0,0,1,1],bins=5)
    assert report.brier_score<0.05
    assert len(report.bins)==3

def test_calibration_rejects_invalid_probability():
    try: calibration_report([1.2],[1])
    except ValueError: pass
    else: raise AssertionError("invalid probability must be rejected")
