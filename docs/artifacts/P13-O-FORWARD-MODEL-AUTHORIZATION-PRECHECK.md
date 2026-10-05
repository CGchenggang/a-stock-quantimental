# P13-O Forward Model — Human Authorization Precheck — 2026-10-05

> STATUS: PRECHECK RECORD — audited at Exact HEAD `0168a77`
> (P13-O-FORWARD-MODEL-001 = PASS / INDEPENDENTLY ACCEPTED / CONTRACT+DESIGN).
> This document ONLY inventories what the owner must freeze. It selects
> NOTHING: no variant, no dates, no scope beyond restating the contract's
> required value. No training, fitting, calibration, or artifact creation
> was performed.

## 1. Parameters the Contract requires Human freeze

Per `P13O-F-001..027`, the authorization record must freeze exactly:

| # | Parameter | Contract ref | Frozen by contract already? |
|---|---|---|---|
| 1 | model_id (semantic name) | P13O-F-001 | NO — assigned in the authorization |
| 2 | model_variant (exactly one of four) | P13O-F-005/006 | NO — owner pre-registration required |
| 3 | training window dates | P13O-F-008 | NO — owner pre-registration |
| 4 | calibration window dates | P13O-F-008/019 | NO — owner pre-registration |
| 5 | validation window dates | P13O-F-008 | NO — owner pre-registration |
| 6 | training_protocol_id ratification | P13O-F-012 | DEFAULT proposed (`p13o-logistic-gd-500x0.05-v1`); ratified (possibly amended) at authorization |
| 7 | scope ratification | P13O-F-016b | Value REQUIRED by contract (`universe-d8c5016b1ded0984` lineage) — ratification is a formality unless the owner changes lineage (which would require contract amendment) |
| 8 | seed (manifest field) | P13O-F-022 | NO — GD is deterministic full-batch (seed unused by the fit); recorded for manifest completeness |
| 9 | training execution authorization itself | P13O-F-027 / R4-D C-gate | NO — the act that starts the phase |
| 10 | downstream policy binding confirmation | R4-D `threshold_platt_p50` | Bound in R4-D contract; confirmed at implementation authorization (not at training) |

## 2. Per-parameter detail

1. **model_id** — candidate: `p13o-forward-logistic` (suggested name in
   R4-D design §4). Source: semantic, assigned by owner. NOT frozen.
   MUST be human-decided.
2. **model_variant** — see §3. Four candidates, all structurally
   eligible. NOT frozen. MUST be human-decided (pre-registered, immutable).
3–5. **Windows** — see §5. Legal envelope fixed; dates open. MUST be
   human-decided (pre-registered, disjoint, label-availability respected).
6. **training_protocol_id** — candidate: `p13o-logistic-gd-500x0.05-v1`
   (verbatim historical protocol; contract-proposed default). Frozen
   VERBATIM at authorization — the owner ratifies or explicitly amends.
   Human ratification required.
7. **scope** — the only in-repo candidate: the committed frozen 76-stock
   universe (`universe-d8c5016b1ded0984`, `data/industry/
   validation_universe_76.txt`, committed at `a1a8d32`). Contract-
   REQUIRED value. Human ratification required.
8. **seed** — candidate: any fixed integer (P13-O precedent 20260929).
   The fit itself is deterministic full-batch GD (seed unused); the
   field is manifest-completeness only. Human-decided (trivial).
9. **training execution** — the authorization act itself. Human.
10. **policy binding** — R4-D froze `threshold_platt_p50` for the apply
    path. Not a training parameter; confirmed at R4-D implementation
    authorization. Human (deferred gate).

## 3. Variant candidates (definitions, evidence, eligibility)

All four are defined in `scripts/run_local_industry_relative_oos.py::_variants()`
(exact column order; order-bound to the weight vector). All four have
historical evidence. NONE is designated; **VARIANT = UNRESOLVED** — the
choice is the owner's pre-registered decision, and this document
deliberately does not rank them.

| variant | feature tuple (exact order) | feature_set implication | historical evidence | training-authorization-eligible? |
|---|---|---|---|---|
| baseline | momentum, volatility, trend, volume_ratio (4) | 4-factor set (new feature_set_id) | P13-O stability artifacts are baseline-dominated (bootstrap ×13, symbol_stability ×889, time_stability ×143, industry_stability ×313, regime ×39 entries); P13-P incremental row `A_baseline` (brier 0.25025) | Structurally YES — owner decision required |
| industry_5 | baseline + industry_relative_return_5 (5) | 5-factor set | P13-O variant-level summary entries (time_stability ×11, regime ×3, …); P13-P row `C_baseline_plus_ir5` (brier 0.25024, Δbrier −0.000865 vs A) | Structurally YES — owner decision required |
| industry_20 | baseline + industry_relative_return_20 (5) | 5-factor set | same artifact families (×11/×3); P13-P row `D_baseline_plus_ir20` (brier 0.25026, Δ +0.000878) | Structurally YES — owner decision required |
| industry_5_20 | baseline + both industry-relative returns (6) | **exactly the frozen calibrated 6-factor set** (`p13q/analysis_config.json` factor_list, config sha256 `f0602bb9…`) | same artifact families (×11/×3); P13-P row `E_baseline_plus_vol_ir5_ir20` (brier 0.25031, Δ +0.000929) | Structurally YES — owner decision required |

Consistency facts (NOT recommendations): only `industry_5_20`'s feature
set matches the R4-D contract's currently referenced calibrated
feature_set_id; authorizing any other variant is fully permitted by
P13O-F-019/021 (the NEW calibration binds to the authorized variant's
actual feature set) but the R4-D resolver's `feature_set_id` reference
would need its documented implementation-time alignment. Historical
deltas between variants are within noise (P13-P bootstrap CIs contain
zero) — the owner must decide on grounds OUTSIDE metric ranking.

## 4. feature_set_id candidates (exact ordered fields)

| candidate variant | ordered feature fields |
|---|---|
| baseline | [momentum, volatility, trend, volume_ratio] |
| industry_5 | [momentum, volatility, trend, volume_ratio, industry_relative_return_5] |
| industry_20 | [momentum, volatility, trend, volume_ratio, industry_relative_return_20] |
| industry_5_20 | [momentum, volatility, trend, volume_ratio, industry_relative_return_5, industry_relative_return_20] |

`feature_set_id = "fs-" + sha256(canonical ordered [name,
definition_version] list)` (P13O-F-014). `definition_version` must be
recorded for every feature at authorization (definitions are
order-bound to the weight vector; industry-relative features additionally
depend on the frozen SW1 membership lineage). The 6-factor list equals
the P13-Q calibrated `factor_list` (config sha256 `f0602bb9…`).

## 5. Window legal envelope (dates NOT chosen)

Hard constraints for the three decision-date windows (all in the
consumed research zone):

1. All three windows are disjoint; ordering: training_end ≤
   calibration_start, calibration_end ≤ validation_start (recommended
   structure; owner may tighten, never loosen disjointness).
2. Every decision date in every window ≤ **2026-09-22** (RESEARCH_END);
   ≥ **VIRGIN_START (2026-09-23)** is absolutely excluded from all three
   (P13O-F-010; virgin rows are label-unknown anyway — the last virgin
   labels are unavailable for any pre-2026-09-23 decision).
3. Label availability: a decision date d is usable in a window only if
   d's label (next trading day close) was known by that window's
   boundary — practically, the last usable decision date of any window
   is the trading day before the boundary.
4. Training window must be large enough for the frozen protocol's
   walk-forward validation instrument (252-row training folds) to remain
   meaningful inside it (informational; the single-final-model fit uses
   the entire training window).
5. R4D-003b note: P13-O/P13-Q consumed the full history, so the window
   decision is a FRESH a-priori act (not a reuse of historical windows).
6. No window may extend to or past 2026-09-23 in any candidate
   configuration → **P13-T/U cannot be polluted by any legal choice**
   (see §7).

## 6. Scope candidates (not chosen)

The only in-repo candidate is the contract-required one: the frozen
76-stock universe lineage `universe-d8c5016b1ded0984` (committed file,
76 unique sorted symbols, auditable from clean clone — verified in
R4-C-NARROW-REPAIR-001). A different scope would require a new universe
definition (owner decision + contract amendment) and has no in-repo
candidate. Ratification is the human act.

## 7. P13-T/U pollution check

- Virgin zone (≥ 2026-09-23) is excluded from training/calibration/
  validation by P13O-F-010; every legal window ends ≤ 2026-09-22.
- The training/calibration entry points (future) must call
  `assert_research_zone` (P13O-F-016 of R4-D lineage; G15).
- Scope = 76 research-zone symbols; no virgin decision date can enter
  any candidate configuration. **No pollution path exists.**
- P13-T remains STOPPED / NOT EXECUTED; P13-U remains PROTECTED.

## 8. P14-D PIT constraint check

- The forward model's TRAINING is pre-registered batch fitting over
  historical rows — row visibility inside the dataset follows the
  accepted `local_pipeline` PIT semantics (factors at day t from
  revisions available by t's decision time; labels from the next day,
  outside the factor window).
- RUNTIME visibility remains P14-D `run_query` exclusively; the forward
  selection rule (`training_end < as_of`) is an artifact-eligibility
  rule, NOT a second visibility implementation.
- No candidate parameter changes any P14-D semantics. ✓

## 9. R4-D C1–C12 satisfaction map (post-authorization steps)

| Condition | Satisfied by |
|---|---|
| C1 unique variant | Human authorization (§3 choice), pre-registered |
| C2 frozen protocol | Authorization ratifies `p13o-logistic-gd-500x0.05-v1` |
| C3 deterministic artifact | Training phase double-fit check (G20) |
| C4 complete feature binding | Training phase manifest (ordered feature_names, P13O-F-014) |
| C5 model identity | Training phase (model_id/version assignment) |
| C6 artifact sha256 | Freeze step (content hash, P13O-F-023) |
| C7 forward selection rule | Already contract-defined (P13O-F-017); implemented in the apply phase |
| C8 calibration artifact | Separate calibration phase over the calibration window (P13O-F-018/019) |
| C9 calibration↔model binding | Same phase (binding tuple recorded, P13O-F-019/021) |
| C10 provenance manifest | Freeze step (committed MODEL_APPLICATION_MANIFEST + evidence row) |
| C11 independent artifact acceptance | Owner/independent acceptance of the frozen artifact |
| C12 exact-head CI | Push of the freeze commit + workflow verification |

All twelve are steps AFTER the human authorization gate; none is
satisfiable before it.

## 10. Items requiring explicit Human approval

1. model_id assignment.
2. model_variant (exactly one of the four §3 candidates).
3. training window dates (start/end).
4. calibration window dates (start/end).
5. validation window dates (start/end).
6. training_protocol_id ratification (`p13o-logistic-gd-500x0.05-v1` or
   explicit amendment).
7. scope ratification (`universe-d8c5016b1ded0984` lineage).
8. seed value (manifest completeness).
9. Training execution authorization (starts the phase).
10. (Deferred) policy binding confirmation + R4-D implementation
    authorization — separate later gates.
