import numpy as np

def prediction_reality(y_true, probabilities, actual_returns, expected_returns):
    y=np.asarray(y_true, dtype=float)
    p=np.asarray(probabilities, dtype=float)
    actual=np.asarray(actual_returns, dtype=float)
    expected=np.asarray(expected_returns, dtype=float)
    if not (len(y)==len(p)==len(actual)==len(expected)):
        raise ValueError("all inputs must have equal length")
    brier=float(np.mean((p-y)**2))
    return {
        "n": int(len(y)),
        "brier": brier,
        "mean_return_error": float(np.mean(actual-expected)),
        "mean_abs_return_error": float(np.mean(np.abs(actual-expected))),
    }
