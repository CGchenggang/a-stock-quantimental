# P13-O Forward Model — Artifact Evidence — 2026-10-06

> STATUS: FROZEN — P13-O-FORWARD-MODEL-EXECUTION-001 — IMPLEMENTATION COMPLETE,
> READY FOR INDEPENDENT ACCEPTANCE. Executed at Exact HEAD
> `91382faf9cd57cc7d1641b6d2a9df9cfd74fa517` under the FROZEN Human
> Authorization Record (`P13-O-FORWARD-MODEL-HUMAN-AUTHORIZATION.md`).
> This record distinguishes the three artifact classes normatively
> (R4D-003c / P13O-F lineage): MODEL_APPLICATION (created here),
> CALIBRATION (created here, bound), HISTORICAL_OOS_PREDICTION (not
> used, never a model).

## MODEL_APPLICATION（created & frozen — ONE artifact）

```text
artifact path:    docs/artifacts/p13o-forward-model/MODEL_APPLICATION.json
artifact sha256:  97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664
model_id:         p13o-forward-logistic
model_version:    97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664
                  (= full lowercase SHA-256 of the exact canonical artifact bytes;
                   64 hex chars; byte size 375)
model_variant:    industry_5_20
model_family:     unregularized_binary_logistic
feature_set_id:   fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe
                  (recomputed in-process before fitting — exact match with the
                   Human Authorization Record; definition blobs verified at HEAD:
                   local_pipeline.py@0582f91e…, run_local_industry_relative_oos.py@0b6c0f14…)
feature_names:    momentum, volatility, trend, volume_ratio,
                  industry_relative_return_5, industry_relative_return_20 (frozen order)
weights:          [-0.010751918948003914, 0.023428091430548876, -0.013818932486082331,
                   -0.02635588574586267, -0.002145305489515557, -0.00550166937555921]
bias:             -0.135236840320142
scope:            universe-d8c5016b1ded0984
scope_sha256:     b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1
target/horizon/
positive_class:   next trading day close-up direction / next_trading_day / next_return > 0
```

> **NARROW-REPAIR-001 (2026-10-06):** F-022 manifest schema closure — the manifest now
> carries the ordered `weights` (equal to the artifact vector, positionally bound to
> feature_names) alongside `weights_sha256`; the verifier enforces G-F022-1..5; 8 new
> golden tests. The MODEL_APPLICATION and CALIBRATION SHAs are UNCHANGED (no retraining,
> no parameter change); only the manifest SHA legitimately changed
> (`e1993c3f…dd4` → `041c5552…713a2`).

## MODEL_APPLICATION_MANIFEST

```text
path:             docs/artifacts/p13o-forward-model/MODEL_APPLICATION_MANIFEST.json
manifest sha256:  041c5552733b2c81586385d4ddfe40989004c6904daa4db64c2d4adab9c713a2
                  (post F-022 closure; pre-repair value e1993c3f9dd0ed1bbc8fa8e405c386b63ee5fac1f0652fa7116775d0aeab6dd4)
                  (canonical bytes; binds artifact_sha256 ↔ model identity ↔ variant ↔
                   feature_set ↔ scope ↔ windows ↔ protocol/seed ↔ calibration binding;
                   weights carried as weights_sha256, bias verbatim; created_at = null)
windows (verbatim half-open):
    training    [2020-01-02, 2025-01-01)   last decision date used: 2024-12-30
    calibration [2025-01-01, 2025-07-01)   last decision date used: 2025-06-30
    validation  [2025-07-01, 2026-09-22]   (evaluation-only — NOT used in this phase)
    research_end 2026-09-22 / virgin_start 2026-09-23
protocol:         p13o-logistic-gd-500x0.05-v1
seed:             20260929 (manifest metadata only; deterministic full-batch GD)
```

## CALIBRATION（created & frozen — bound to the model）

```text
path:              docs/artifacts/p13o-forward-model/CALIBRATION.json
artifact sha256:   6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9
calibration_id:    p13o-forward-platt
calibration_version: 6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9
method:            platt — sigmoid(a + b·logit(p_raw)), logit domain clip ±30
a:                 0.22696568443636966
b:                 2.274174209586145
fit population:    n = 8,389 rows, window [2025-01-01, 2025-07-01)
                   (decision dates 2025-01-02 … 2025-06-30; last decision date
                    used 2025-06-30 per the frozen label-availability rule)
fit_time_boundary: 2025-07-01
binding:           {model_id: p13o-forward-logistic,
                    model_version: 97602f4d…664,
                    model_variant: industry_5_20,
                    feature_set_id: fs-d1f3bdca…3afe}
fitter provenance: scripts/run_p13q_analysis.py::fit_platt (the accepted P13-Q
                   numerical protocol, reused verbatim — NOT the P13-Q artifact)
manifest:          CALIBRATION_MANIFEST.json, sha256
                   b758015ade2d6ee1dfe8dfb8d00fd0eb169b589cb932b67414ebeebc5d3f5d7c
```

The P13-Q pooled calibration was NOT reused (P13O-F-018); this
calibration was fitted on THIS model's raw outputs over the authorized
calibration window.

## Data provenance & integrity chain

- Training rows: **84,466** (76 symbols × decision dates 2020-01-02 …
  2024-12-30; one row per (symbol, decision_time); rows sorted by
  (decision_time, symbol); missing-factor rows dropped deterministically).
  Source: the local historical store via the accepted
  `build_local_factor_rows` + `build_universe_industry_relative_context_maps`
  (the frozen feature definitions — blob-verified at HEAD).
- Integrity chain: artifact bytes → SHA-256 (`97602f4d…`) →
  MODEL_APPLICATION_MANIFEST (sha256 `e1993c3f…`) → CALIBRATION
  (`6e341fcd…`) → CALIBRATION_MANIFEST (`b758015a…`) → this committed
  evidence record. All links re-verified by
  `tests/test_p13o_forward_model_execution.py` (19 golden checks,
  G21–G30 + positive chain).
- Double-fit: two independent full executions (separate processes) —
  all four artifact files **byte-identical** (G29 PASS).
- Virgin-zone scan: max decision date used anywhere = **2025-06-30**
  (< 2026-09-23); context data truncated to `< virgin_start` before row
  assembly. **virgin contamination: NONE.**
- Boundary exclusions honored: decision dates 2024-12-31 (training),
  2025-07-01 (calibration), 2026-09-22 (validation) excluded per the
  frozen label-availability rule.

## Execution status

```text
MODEL_APPLICATION = CREATED AND FROZEN (one artifact)
CALIBRATION       = CREATED AND FROZEN (bound to the model)
R4-D APPLY        = BLOCKED (unchanged — implementation NOT AUTHORIZED)
P14-F             = NOT AUTHORIZED
P13-T             = STOPPED / NOT EXECUTED
P13-U             = PROTECTED
```
