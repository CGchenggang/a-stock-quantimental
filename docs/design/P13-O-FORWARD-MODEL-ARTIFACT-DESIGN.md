# P13-O Forward Model Artifact — Design (D1)

> STATUS: DRAFT — P13-O-FORWARD-MODEL-001 — Contract/Design gate ONLY.
> No training, no artifact creation, no production change in this phase.
> Companion normative contract:
> `docs/contracts/P13-O-FORWARD-MODEL-ARTIFACT-CONTRACT.md`.
> Baseline: Exact HEAD `3cdd1ee` (P13-O-ARTIFACT-001 = PASS / NOT RECOVERABLE).

## 1. Core Semantic

The future artifact is a **NEW FORWARD-APPLY MODEL ARTIFACT** — never a
"recovered P13-O model". The old P13-O raw-model artifact is frozen as
NOT RECOVERABLE; even if the new model adopts the same training protocol,
it receives a NEW model_id, NEW model_version, NEW artifact hash, NEW
provenance and a NEW freeze record. No retroactive identity changes.

## 2. Model Identity (contract P13O-F-001..004)

- `model_id` — stable semantic name assigned in the pre-training
  authorization record (e.g. `p13o-forward-logistic`); never derived from
  results.
- `model_version` — content-addressed: `sha256(bytes of the frozen
  parameter artifact)`, short prefix recorded in the manifest. Any byte
  change = new model_version = new artifact (identity is immutable; one
  model_id may accrete multiple versions but an authorization binds ONE).
- The artifact hash IS part of identity; the git commit is **provenance
  only** (never identity).
- `MODEL_APPLICATION_MANIFEST` (committed evidence) binds
  artifact_sha256 ↔ model_id/model_version ↔ every identity field.

## 3. Variant Selection Authority (contract P13O-F-005..007)

- Decision authority: the **project owner**, by explicit pre-training
  Human Authorization; the chosen variant is recorded in that
  authorization BEFORE any fit executes and is immutable afterwards.
- Timing: strictly BEFORE training (pre-registered). Train-all-then-pick
  is model selection: it belongs only to a research-comparison protocol
  (P13-O/P13-P lineage); its output can never directly become the apply
  artifact — a fresh single-variant pre-registration is required
  afterwards, and variant selection on validation results is leakage
  (BLOCKED).
- Guard: the training entry point (future) must assert the authorized
  variant and refuse any other.

## 4. Training/Calibration/Validation Boundaries (P13O-F-008..011)

Three disjoint decision-date windows, hard-dated in the pre-training
authorization (pre-registration prevents leakage; the contract fixes the
STRUCTURE, the owner fixes the DATES):

```text
[training window)   decision rows used to fit weights — ends at training_end
[calibration window) rows used to fit a/b — starts ≥ training_end,
                     disjoint from training; fits AFTER the model freeze
[validation window)  evaluation only — never fitted, never selected on
[virgin zone]        ≥ 2026-09-23 — ABSOLUTELY excluded from all three
```

- Labels for decision day t are known at the NEXT trading day close → any
  row whose label was not available by the window boundary is excluded.
- Virgin-zone protection invariant: every future training/calibration
  entry point calls `assert_research_zone`; P13-T stays STOPPED, P13-U
  PROTECTED (P13O-F-016).

## 5. Training Protocol (P13O-F-012)

PROPOSED DEFAULT = the historical P13-O protocol, adopted VERBATIM as an
EXPLICITLY FROZEN protocol at authorization:
`training_protocol_id = "p13o-logistic-gd-500x0.05-v1"` — unregularized
binary logistic, full-batch gradient descent, 500 epochs, lr 0.05,
zero-init weights + scalar bias, float64, numerically stable sigmoid
(clip ±30), no scaler (raw factor values), rows sorted by
(decision_time, symbol), one row per (symbol, decision_time)
(duplicates collapsed deterministically), rows with any missing factor
dropped deterministically. Full-batch GD is deterministic — same inputs
→ byte-identical artifact (G20).

**Single final model** (not a per-fold collection): the apply artifact is
ONE weight vector + bias fitted on the entire training window. The
walk-forward fold machinery remains a VALIDATION instrument only; mixing
fold collections with forward apply is forbidden (P13O-F-013).

## 6. Feature Contract (P13O-F-014..016)

`feature_set_id = "fs-" + sha256(canonical [name, definition_version]
list)`. The manifest stores the exact ordered feature list. Any
feature_set_id / feature_order / preprocessing mismatch → `INELIGIBLE`
(no auto-adjustment) — mirrors R4-D G7/G14.

## 7. Forward Model Selection (P13O-F-017 — executable rule)

With a single frozen artifact the rule is:

```text
eligible ⇔ artifact_sha256 == manifest.artifact_sha256
        AND manifest.model_variant == authorized_variant
        AND manifest.feature_set_id == packet feature_set_id
        AND manifest.training_end < as_of        (STRICT — label
          availability: last training label known only after training_end)
        AND symbol ∈ manifest.scope
exactly one frozen artifact exists → selected; none → NOT_AVAILABLE
```

Strict `<` is deliberate (future-leakage guard). No tie-breaking is
needed by construction (one authorized artifact); a second eligible
artifact would be a governance error → fail closed (G11).

## 8. Calibration Design (P13O-F-018..021)

Existing P13-Q is variant-pooled with unresolved binding → it is **NOT
the future model's calibration**. A NEW calibration artifact must be
issued for the frozen model: platt `sigmoid(a + b·logit(p_raw))` (clip
±30) fitted on the NEW model's raw outputs over the calibration window
(a priori dates), recording: a, b, logit domain, fit population (n,
window), fit boundary, AND the binding tuple
`{model_id, model_version, model_variant, feature_set_id}`. Mismatch on
any binding field → INELIGIBLE (G12/G13/G14). The calibration artifact
gets its own sha256 + manifest + evidence row.

## 9. Artifact Manifest & Integrity (P13O-F-022..024)

`MODEL_APPLICATION_MANIFEST` fields (nulls written explicitly as `null`,
never omitted): artifact_type, artifact_id, artifact_sha256, model_id,
model_version, model_family, variant, feature_set_id, feature_names
(ordered), preprocessing (="identity"), target, horizon, positive_class,
training_start, training_end, research_end, training_protocol_id, seed,
weights (ordered), bias, calibration_id, calibration_binding, provenance,
source_commit, created_at (execution metadata — outside research
identity), freeze_status. Integrity chain: artifact bytes → sha256 →
manifest → manifest hash → committed evidence record
(`docs/artifacts/`). Hash mismatch → FAIL CLOSED; never regenerate,
retrain, or substitute (G02/G19/G20).

## 10. R4-D Unblock Conditions (P13O-F-025)

C1 unique variant (pre-registered) · C2 frozen protocol · C3
deterministic artifact (double-run byte-identical) · C4 complete feature
binding · C5 model identity · C6 artifact sha256 · C7 forward selection
rule · C8 calibration artifact · C9 calibration↔model binding · C10
provenance manifest · C11 independent artifact acceptance · C12
exact-head CI. ALL satisfied → `R4-D APPLY = ELIGIBLE FOR AUTHORIZATION`
— final unlock still requires Human Authorization. Never an automatic
R4-D PASS.

## 11. Golden Cases

G01–G20 per contract §11 (missing artifact, hash mismatch, model_id/
version mismatch, variant/feature_set/order/preprocessing mismatch,
training_end after as_of, no eligible model, ambiguous eligibles,
calibration mis-binding ×3, P13-T/U contamination attempt, historical
OOS predictions as model artifact, missing weights/bias,
manifest/artifact inconsistency, non-deterministic generation).

## 12. Authority Boundaries

P13-Q owns calibration research (its successor issues the new
calibration); P13-R owns policies (untouched); P14-D remains the sole
PIT/selection authority (the `<` rule consumes as_of, it does not
re-implement visibility); P14-E remains the sole evidence/provenance
authority (manifest evidence complements, never replaces, P14-E).
