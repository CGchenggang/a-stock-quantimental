# R4-D Apply-Path Artifact Evidence — 2026-10-05

> STATUS: EVIDENCE RECORD — audited at Exact HEAD `0406abc` (R4-D-NARROW-REPAIR-001).
> Purpose: independently auditable identity of every artifact the R4-D apply path
> depends on — WITHOUT committing any historical market data. The sha256 values below
> let independent acceptance verify the gitignored artifacts byte-for-byte against
> local copies (or future committed manifests).
>
> **Raw-model application artifact: ABSENT — R4-D implementation authorization is
> BLOCKED until one is independently frozen by a future authorized phase.**

## Three-artifact taxonomy (normative — R4D-003c)

1. **HISTORICAL_OOS_PREDICTION** — recorded outputs of past walk-forward runs
   (`oos_predictions_76.json`). Evidence of what the model DID predict; **MUST NOT**
   be used as `p_raw` for any current/future research run (R4D-003c).
2. **MODEL_APPLICATION** — a frozen, forward-applicable model artifact (fitted
   parameters/weights + complete feature mapping + version identity) loadable at
   runtime to compute `p_raw` for NEW as_of data. **Currently ABSENT from this
   repository.**
3. **CALIBRATION** — the frozen P13-Q registry + fitted Platt parameters. Present.

## Artifact inventory (audited sha256)

| artifact_id | file | type | sha256 | status |
|---|---|---|---|---|
| p13o-oos-predictions | `data/industry/p13o/oos_predictions_76.json` | HISTORICAL_OOS_PREDICTION | `c60fac96d0611b6bb15de9f3c53d9b95a762c0c90c88eed0827f670dc3a1ccc4` | NOT apply-usable (R4D-003c) |
| p13o-analysis-config | `data/industry/p13o/analysis_config.json` | HISTORICAL_OOS_PREDICTION | `3f67ef8a8d225b5ef244a5247e396e4f34d80c13a3f241e593f05eabc7599e38` | provenance of the above |
| p13q-calibration-registry | `data/industry/p13q/calibration_registry.json` | CALIBRATION | `643a3dcd2c53a9445aca56e6d7655e60dfe2c1508c719442f6b621db89c71d52` | apply-usable ONLY after a MODEL_APPLICATION artifact is frozen AND variant/feature binding resolved |
| p13q-calibration-methods | `data/industry/p13q/calibration_methods.json` | CALIBRATION | `d8964112561877ca4dfeb1332599e89857f5e4177e4298d2da26d03c614ae46e` | platt slope/intercept pinned |
| p13q-analysis-config | `data/industry/p13q/analysis_config.json` | CALIBRATION | `f0602bb61874d0f28a873416661aa743d79aedca36571aeb236c2be11cf9a4e6` | feature_set_id source (6 factors) |
| p13q-manifest | `data/industry/p13q/manifest.json` | CALIBRATION | `377d94644cf2829471ea5d1df8213ca65a5c1e417a2a8f1ec910118369b3228f` | pins p13q file hashes |
| p13r-policy-registry | `data/industry/p13r/decision_policy_registry.json` | POLICY | `361791f8bf072778b9cbb84f3a81b6079a148471cb17c6b5953e042ddf09d16c` | 8 frozen policies |
| p13r-manifest | `data/industry/p13r/manifest.json` | POLICY | `5a07b5dc76c2cea80939df89dc767d2f900b98be88ad06417d1ceab7d95f78dd` | pins p13r file hashes |
| p13p-incremental-models | `data/industry/p13p/incremental_models.json` | METRICS_ONLY (A/B/C/D OOS metric comparisons — NOT model parameters) | `c1ee18d2765719ec5b4a9e33744b6832bd0e6860fd5fa85bcdc7a1234abc867f` | NOT a model artifact |

## Raw-model application authority: NOT FROZEN (BLOCKER-1 finding)

Audit at Exact HEAD `0406abc`:

- The P13-O walk-forward models were fitted **transiently inside fold loops**
  (`run_local_industry_relative_oos.py::fit_predict` — predictions returned,
  weights discarded). No joblib/pickle/np.save/coef persistence exists anywhere in
  `scripts/` or `data/`.
- `p13p/incremental_models.json` contains OOS **metric comparisons** (A/B/C/D),
  not parameters — it is evidence of incremental value, not a model.
- Therefore: **no MODEL_APPLICATION artifact exists**. Per R4D-003b, R4-D
  implementation authorization is **BLOCKED**; historical OOS predictions MUST NOT
  substitute (R4D-003c); retraining at runtime or now is forbidden (retraining is
  not apply).

## Variant & feature binding: UNRESOLVED (BLOCKER-2 finding)

`p13q/analysis_config.json` and `p13q/probability_audit.json` contain **no variant
dimension** (0 occurrences of variant/industry_5_20/baseline): the calibration was
fitted POOLED across all four variant prediction rows. Consequently the registry
records NO `calibration ↔ model_variant` binding and NO variant-specific feature
mapping. A future frozen raw-model artifact MUST record its exact variant, and a
future calibration re-issue MUST bind to that variant + feature set (R4D-002b/
R4D-003a). Until then the binding is UNRESOLVED and no variant may be selected at
runtime (R4D-002a: no auto-selection of best/latest/first/arbitrary).

## Required identity fields for the future MODEL_APPLICATION artifact

When produced (by a future authorized phase — NOT by R4-D), the artifact MUST
record: `artifact_id, artifact_type=MODEL_APPLICATION, sha256, model_id,
model_version, model_variant, feature_set_id (all 6 calibrated features with
computation identity), training_window_protocol, split_date, research_end, scope
(universe-d8c5016b1ded0984), status, source provenance (exact script + git
commit + seed)` — and MUST be re-fitted under the SAME accepted walk-forward
protocol with a new a-priori frozen window decision, not silently re-used. Its
evidence row is then appended to THIS file, and only that act unblocks R4-D
implementation authorization (R4D-003b).
