# P13-O Raw Model Apply Artifact Audit — 2026-10-05

> P13-O-ARTIFACT-001. Audit-only task at Exact HEAD `b5c8e29` (base). No training,
> no refit, no recalibration, no production/registry/P14/R4 change, no P13-T/U contact.
> Question: can a unique, deterministic, auditable, forward-apply P13-O raw-model
> artifact be recovered from existing repository and research artifacts?

## Verdict

```text
P13-O RAW MODEL APPLY ARTIFACT = NOT RECOVERABLE
```

The P13-O "model" exists only as **transient per-fold computation**: an
unregularized logistic regression refit inside every walk-forward fold whose
weights were never persisted — not on the filesystem, not in git history, not in
any document. Only its historical predictions and metrics survive. Recovering
parameters would require re-fitting (forbidden) or algebraic inversion from
(feature, prediction) pairs (a disguised refit — equally forbidden and numerically
not the accepted artifact).

## 1. Model family (audited, not guessed)

Unregularized binary logistic regression, full-batch gradient descent —
`scripts/run_local_industry_relative_oos.py::fit_predict`: weights zero-initialized,
500 epochs, lr 0.05, bias scalar, numerically stable sigmoid, **no regularization,
no scaler/normalizer** (raw factor values enter the design matrix directly).
Fold schedule: `walk_forward_windows` (`src/astock_v2/validation.py`) with
train 252 / test 20 / step 20 / gap 1 over decision-time-ordered rows
(first decision date 2021-02-22).

## 2. Model identity — MISSING

No `model_id` / `model_version` field exists anywhere for the raw model. The only
identity is provenance: runner git commit `4d792100…` + protocol (252/20/20/1) +
variant + frozen 76 universe + local data snapshot. `model_version` = **MISSING**.

## 3. Variants — four defined, none designated

| variant | feature tuple (exact column order) | coefficients persisted | apply-usable |
|---|---|---|---|
| baseline | momentum, volatility, trend, volume_ratio | NO | NO |
| industry_5 | baseline + industry_relative_return_5 | NO | NO |
| industry_20 | baseline + industry_relative_return_20 | NO | NO |
| industry_5_20 | baseline + both industry-relative returns (6) | NO | NO |

Column order is exactly `_variants()` tuple order (`fit_predict` receives
`[[row[name] for name in factor_names]]` — order-bound). No accepted
apply-variant designation exists anywhere → **VARIANT = UNRESOLVED**.

## 4. Raw parameters — NOT_RECOVERABLE_FROM_PREDICTIONS

- Filesystem: zero `.pkl/.joblib/.npz/.npy/.h5/.sav` or coefficient/weight files
  under `data/`.
- `p13p/incremental_models.json` = OOS **metric comparisons** (A/B/C/D), not
  parameters.
- `oos_predictions_76.json` = per-row `{symbol, decision_time, variant, p, y,
  baseline_p}` — predictions only. Predictions are not a model.
- Docs record only P13-Q **calibration** slope/intercept, never raw-model weights.
- Git history: **no model-artifact file was ever committed or deleted** (full
  `--all --diff-filter=A/D` audit); the runner's own 8-commit history never
  contained persistence.

## 5. OOS prediction ≠ forward artifact

`oos_predictions_76.json` is historical evidence of what transient fold models
predicted on their own test folds. It cannot produce `p_raw` for a new as_of:
HISTORICAL OOS PREDICTION ARTIFACT CANNOT SUBSTITUTE FOR A FORWARD-APPLY MODEL
ARTIFACT.

## 6. Calibration binding — UNRESOLVED

P13-Q fitted **variant-pooled** (zero variant references in
`p13q/analysis_config.json` / `probability_audit.json`): the Platt map
(slope 0.16256…, intercept −0.11864…, logit domain) was fitted on a mixture of
all four variants' raw probabilities. No registry field binds it to a variant or
feature set → `CALIBRATION_MODEL_BINDING = UNRESOLVED`; pooled compatibility with
a future variant-bound model is NOT assumed.

## 7. Policy binding — consistent but blocked upstream

8 frozen policies (`361791f8…`) reference the same P13-M label semantics
(next-trading-day close-up) — probability target is consistent with P13-O. The
apply chain is blocked at the raw-model stage; policy layer itself is not the
blocker.

## 8. Tracked/untracked status of audited artifacts

All `data/industry/p13o|p13q|p13p|p13r/*` files: **gitignored + local-only**
(untracked; NOT GitHub Exact-HEAD auditable). Tracked evidence:
`docs/artifacts/R4-D-APPLY-ARTIFACT-EVIDENCE.md` (committed at `88898f4`, contains
audited sha256 values). Local-only sha256 spot values recorded there and in
R4-D-NARROW-REPAIR-001; a clean clone can verify only the committed evidence
file, not the gitignored artifacts.

## 9. What a future recovery path would require (informational — NOT performed)

A future authorized phase would need to: choose ONE variant by an explicit owner
decision; refit under the accepted protocol with a fresh a-priori window
decision; persist per-fold (or single final) weights + exact feature order +
identity (model_id/version/variant/feature_set_id/scope/split_date/
research_end/provenance); freeze with manifest evidence; then re-issue a
variant-bound calibration bound to that exact artifact. All of that is outside
this audit and currently unauthorized.

## 10. Missing items (complete list)

raw-model parameters (all folds) · model_id/model_version · accepted apply
variant designation · calibration↔variant binding · calibration↔feature-set
binding · forward fold-selection semantics · GitHub-auditable model artifact
bytes.
