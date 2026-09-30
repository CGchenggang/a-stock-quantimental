# P13-R policy comparison (low-cost scenario, validation window)

Research observation only - not a validated production strategy.

| policy | N | coverage | hit_rate | net/day | turnover | max_dd |
|---|---|---|---|---|---|---|
| hold_all | 18632 | 0.6433 | 0.4739 | +0.00020 | 0.0077 | -0.2520 |
| threshold_raw_p50 | 7823 | 0.2701 | 0.4823 | +0.00021 | 0.3256 | -0.2188 |
| threshold_platt_p50 | 15 | 0.0005 | 0.2000 | -0.00605 | 1.2667 | -0.1615 |
| threshold_iso_p50 | 1 | 0.0000 | 1.0000 | +0.10044 | 0.0000 | 0.0000 |
| topk_platt_k3 | 1255 | 0.0433 | 0.4821 | -0.00104 | 0.6693 | -0.3794 |
| percentile_platt_p80 | 5592 | 0.1931 | 0.4832 | -0.00015 | 0.4061 | -0.2722 |
| er_platt_0 | 8684 | 0.2998 | 0.4675 | -0.00032 | 0.2050 | -0.3252 |
| er_platt_pos_risk | 3611 | 0.1247 | 0.4691 | +0.00016 | 0.2401 | -0.1937 |