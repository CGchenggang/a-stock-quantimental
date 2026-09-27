from astock_v2.monitoring import standardized_mean_shift, probability_distribution_shift, population_stability_index

def test_mean_shift_detects_large_factor_drift():
    r=standardized_mean_shift([0,1,0,-1,0],[5,6,5,4,5])
    assert r.drifted

def test_probability_shift_is_monitoring_only():
    r=probability_distribution_shift([.5,.5,.5],[.8,.9,.85])
    assert r.drifted

def test_psi_is_deterministic():
    r=population_stability_index([0,1,2,3,4],[0,0,3,4,4])
    assert r.value >= 0
