# Model Contract

## Input

Only PIT-safe features.

## Output

```text
probability
expected_return
volatility
drawdown
model_version
feature_version
training_window
calibration_status
```

## Calibration

Every probability model must expose whether calibration was performed.

## OOS

A model is not considered validated merely because it fits historical data.

Validation must preserve temporal order.

## Versioning

Every prediction must identify:

- model version;
- feature version;
- data snapshot / input snapshot;
- decision time.
