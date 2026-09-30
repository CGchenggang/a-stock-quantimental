# P13-Q T5/T6: calibration methods (fit: discovery OOS (decision_time < 2025-01-01); evaluate: validation OOS (decision_time >= 2025-01-01))

| method | N | brier | logloss | ece | intercept | slope |
|---|---|---|---|---|---|---|
| raw | 28965 | 0.25076 | 0.69517 | 0.02406 | -0.0845 | +0.1668 |
| platt | 28965 | 0.24937 | 0.69188 | 0.01078 | +0.0372 | +1.0258 |
| isotonic | 28965 | 0.24938 | 0.69191 | 0.00894 | -0.0223 | +0.6053 |

## Δ vs raw (negative = improvement), symbol-clustered bootstrap (B=1000, seed=20260929)

| method:metric | point | ci95 |
|---|---|---|
| isotonic:delta_brier | -0.00138 | [-0.00172, -0.00099] |
| isotonic:delta_ece | -0.01512 | [-0.02046, -0.01012] |
| isotonic:delta_log_loss | -0.00325 | [-0.00423, -0.00227] |
| platt:delta_brier | -0.00139 | [-0.00177, -0.00097] |
| platt:delta_ece | -0.01328 | [-0.01911, -0.00844] |
| platt:delta_log_loss | -0.00329 | [-0.00435, -0.00222] |