# P13-O Forward Model — Human Authorization Candidates — 2026-10-05

> STATUS: CANDIDATES RECORD — audited at Exact HEAD `2235471`
> (P13-O-FORWARD-MODEL-001 = PASS / INDEPENDENTLY ACCEPTED / CONTRACT+DESIGN;
> AUTHORIZATION-PRECHECK = PASS / INDEPENDENTLY ACCEPTED).
> NO training, fitting, calibration, threshold optimization, or artifact
> creation was performed. This document proposes LEGAL candidate schemes for
> the Human Authorization record; it ranks nothing and selects nothing.

---

## 一、Variant candidates（FINAL VARIANT = HUMAN UNRESOLVED）

Definitions are verbatim from `scripts/run_local_industry_relative_oos.py::_variants()`
(column order is the weight-vector order — order-bound).

| candidate | exact ordered feature tuple | feature count |
|---|---|---|
| baseline | momentum, volatility, trend, volume_ratio | 4 |
| industry_5 | momentum, volatility, trend, volume_ratio, industry_relative_return_5 | 5 |
| industry_20 | momentum, volatility, trend, volume_ratio, industry_relative_return_20 | 5 |
| industry_5_20 | momentum, volatility, trend, volume_ratio, industry_relative_return_5, industry_relative_return_20 | 6 |

**feature_set_id computation** (P13O-F-014):
`feature_set_id = "fs-" + sha256(canonical_json([["<name>", "<definition_version>"], …]))`
— the ordered `[name, definition_version]` list, canonical serialization per
P13O-F-016c, hashed over the exact bytes.

**required definition_version**: each feature needs one, assigned at
authorization (suggested lineage label: `p13m-local-pipeline-v1` — the
historical definitions live in `src/astock_v2/local_pipeline.py` and the
OOS runner; industry-relative features additionally depend on the frozen
SW1 membership lineage `data/industry/sw_official_sw1_membership_all.csv`).

**relationship to P13-Q's current feature set**: only `industry_5_20`'s
6-factor list equals the P13-Q calibrated `factor_list` (`p13q/
analysis_config.json`, sha256 `f0602bb9…`). The other three candidates
define NEW feature sets (new feature_set_id) — fully legal under
P13O-F-018/021 because the NEW calibration binds to the authorized
variant's actual feature set; but for those candidates the R4-D
resolver's `feature_set_id` reference (currently the 6-factor list) must
be aligned at R4-D implementation authorization.

**historical research evidence** (inventory only — differences are within
P13-P bootstrap noise; CIs contain zero):

| variant | P13-O stability artifact presence | P13-P incremental row | P13-P brier (discovery) |
|---|---|---|---|
| baseline | dominant (bootstrap ×13, symbol ×889, time ×143, industry ×313, regime ×39) | `A_baseline` | 0.250245 |
| industry_5 | variant-level summary entries (×11 / ×3) | `C_baseline_plus_ir5` | 0.250243 (Δ −0.000865) |
| industry_20 | variant-level summary entries (×11 / ×3) | `D_baseline_plus_ir20` | 0.250256 (Δ +0.000878) |
| industry_5_20 | variant-level summary entries (×11 / ×3); matches P13-Q factor_list | `E_baseline_plus_vol_ir5_ir20` | 0.250307 (Δ +0.000929) |

**structurally trainable?** YES — all four: definitions executable,
data covers 2020-01-02 → 2026-09-24 for all 76 scope symbols, protocol
needs only ≥ 252-row training windows.

**binding / calibration compatibility issues?**
- ALL candidates: the current P13-Q calibration is variant-POOLED with
  unresolved binding → NOT reusable; a NEW variant-bound calibration is
  mandatory in every case (P13O-F-018/019/021). COMPATIBLE (via the new
  calibration), no candidate has a pre-existing calibration shortcut.
- industry_5_20 additionally: its feature set coincides with the pooled
  P13-Q factor_list, but P13O-F-018 still requires the NEW bound
  calibration — the coincidence grants nothing.
- baseline/industry_5/industry_20 additionally: R4-D resolver's current
  `feature_set_id` reference would need documented alignment at R4-D
  implementation authorization (COMPATIBLE with that documented step).

## 二、Time-window candidates（FINAL WINDOWS = HUMAN UNRESOLVED）

Boundary semantics: calendar-date thresholds; actual rows are the
trading days within; labels for decision day t come from the NEXT
trading day close (label-availability per P13O-F-009). All candidates
share `validation_end = 2026-09-22` → the last included validation
decision date is **2026-09-21 (Mon)**, whose label closes **2026-09-22
(Tue, inside the research zone)** — no virgin-zone data is touched.
Approximate row counts assume ~243 A-share trading days/year × 76 symbols.

### C-W1 — historical-lineage aligned

training [2020-01-02, 2025-01-01) · calibration [2025-01-01, 2025-07-01) ·
validation [2025-07-01, 2026-09-22]
≈ 1,215 train days (~92k rows) · ≈ 115 cal days (~8.7k rows) · ≈ 295 val days

### C-W2 — extended training

training [2020-01-02, 2025-07-01) · calibration [2025-07-01, 2026-03-02) ·
validation [2026-03-02, 2026-09-22]
≈ 1,335 train days · ≈ 165 cal days (~12.5k rows) · ≈ 145 val days

### C-W3 — balanced thirds

training [2020-01-02, 2025-04-01) · calibration [2025-04-01, 2026-01-05) ·
validation [2026-01-05, 2026-09-22]
≈ 1,275 train days · ≈ 185 cal days (~14k rows) · ≈ 185 val days

### C-W4 — maximum training

training [2020-01-02, 2026-01-05) · calibration [2026-01-05, 2026-04-01) ·
validation [2026-04-01, 2026-09-22]
≈ 1,460 train days · ≈ 58 cal days (~4.4k rows) · ≈ 135 val days

### C-W5 — post-2020 compact

training [2021-01-04, 2025-01-01) · calibration [2025-01-01, 2025-09-30) ·
validation [2025-09-30, 2026-09-22]
≈ 972 train days · ≈ 180 cal days (~13.7k rows) · ≈ 240 val days

### Nine-point legality proof (applies to EVERY candidate; all = LEGAL)

1. **三窗口互斥**: half-open intervals on a shared axis, no overlap by
   construction (end == next start, half-open).
2. **时间顺序正确**: training_end ≤ calibration_start ≤ calibration_end ≤
   validation_start ≤ validation_end holds in all five.
3. **decision date ≤ 2026-09-22**: the global maximum is validation_end
   = 2026-09-22 itself as a threshold; the last INCLUDED decision date is
   2026-09-21 (Mon) — trading-day-strictly-before the boundary.
4. **不进入 virgin zone**: no decision date ≥ 2026-09-23 in any window;
   the only post-boundary value used anywhere is the 2026-09-22 close
   (label of 2026-09-21), which is inside the research zone.
5. **label availability satisfied**: by the boundary rule (P13O-F-009),
   the last validation decision date (2026-09-21) has its label closed
   on 2026-09-22 ≤ validation boundary usage; training/calibration
   windows end years earlier.
6. **training history length**: every candidate's training window ≥ 972
   trading days — far above the frozen protocol's 252-row fold
   requirement; the SINGLE FINAL MODEL fits the entire window.
7. **validation not used for variant selection**: variant is
   pre-registered by the owner BEFORE training (P13O-F-005/006/007);
   validation is evaluation-only, post-freeze.
8. **P13-T/U 不污染**: no window contains any date ≥ 2026-09-23;
   P13-T remains STOPPED / NOT EXECUTED; P13-U remains PROTECTED.
9. **P14-D PIT 不违反**: training/calibration consume historical rows
   under the accepted `local_pipeline` PIT semantics (factors visible at
   decision time, labels next-day outside the factor window); runtime
   research visibility remains P14-D `run_query` exclusively.

No candidate is marked best/recommended — all five are **LEGAL**;
selection is the owner's.

## 三、Scope candidates（FINAL SCOPE ratification = HUMAN）

The only in-repo candidate (contract-required value):

```text
universe_id = universe-d8c5016b1ded0984
file         = data/industry/validation_universe_76.txt
             (committed at a1a8d32; 76 unique sorted symbols; clean-clone auditable)
```

Creating a new universe is out of scope for this stage and has no
candidate.

## 四、Training protocol candidate（FINAL ratification = HUMAN）

`training_protocol_id = "p13o-logistic-gd-500x0.05-v1"` — the complete
frozen parameter set:

- unregularized binary logistic regression;
- full-batch gradient descent (no sampling, deterministic);
- 500 epochs;
- learning rate 0.05;
- zero initialization (weights vector + scalar bias);
- float64 throughout;
- numerically stable sigmoid (clip ±30);
- no scaler (raw factor values, preprocessing = "identity");
- deterministic row ordering: sort by (decision_time, symbol); one row
  per (symbol, decision_time); rows with any missing factor dropped
  deterministically;
- **SINGLE FINAL MODEL** fitted on the entire training window (the
  252/20/20/1 walk-forward machinery is the validation instrument only).

NOT executed in this stage.

## 五、Model identity candidates（FINAL MODEL_ID = HUMAN UNRESOLVED）

Naming candidates (semantic, assigned in the authorization record):

1. `p13o-forward-logistic` (the R4-D design's suggested name);
2. `p13o-forward-model`;
3. `astock-forward-logistic`.

**model_version = NOT YET AVAILABLE** — it is the full lowercase SHA-256
of the canonical frozen parameter artifact bytes (P13O-F-002/016c) and
therefore exists only after the future freeze. It cannot be pre-claimed,
pre-computed, or simulated.

## 六、Seed candidate

Candidate: **20260929** (the historical P13-O/P13-P lineage seed).
Facts: full-batch GD uses no random sampling — the fit is deterministic
without a seed; the seed is recorded solely for manifest completeness /
deterministic-execution metadata (P13O-F-022). Final value still frozen
by Human Authorization.

## 七、Ranking prohibition

This document contains NO "best", "recommended", or ranked conclusion.
Every candidate is annotated only **LEGAL / ILLEGAL** and
**COMPATIBLE / INCOMPATIBLE**. All five window candidates: LEGAL. All
four variant candidates: LEGAL and structurally trainable; calibration
COMPATIBLE-via-new-bound-calibration for all four. Final research
selection belongs exclusively to the Human Authorization.

## 八、Per-candidate C1–C12 satisfaction map

For EVERY candidate scheme (variant × window × model_id × seed), the
post-authorization steps that satisfy each condition:

| Condition | Satisfied at/after authorization by |
|---|---|
| C1 unique variant | The authorization itself (pre-registered variant, immutable) |
| C2 frozen protocol | The authorization ratifying §四 protocol_id |
| C3 deterministic artifact | Training phase double-fit check (P13O-F-024/G20) |
| C4 complete feature binding | Training phase manifest — ordered feature_names + definition_versions (§一 per-variant list) |
| C5 model identity | Training phase (authorized model_id + content-addressed model_version) |
| C6 artifact sha256 | Freeze step (canonical bytes hash, P13O-F-002/023) |
| C7 forward selection rule | Already contract-frozen (P13O-F-017); wired at R4-D implementation |
| C8 calibration artifact | Calibration phase over the authorized calibration window |
| C9 calibration↔model binding | Same phase (binding tuple, P13O-F-019/021) |
| C10 provenance manifest | Freeze step (committed manifest + evidence row) |
| C11 independent artifact acceptance | Owner/independent acceptance of the frozen artifact |
| C12 exact-head CI | Push of the freeze commit + workflow verification |

None of the twelve is satisfiable before Human Authorization.

---

## FINAL

```text
FINAL VARIANT:  HUMAN UNRESOLVED
FINAL WINDOWS:  HUMAN UNRESOLVED
FINAL MODEL_ID: HUMAN UNRESOLVED
TRAINING AUTHORIZATION: NOT GRANTED
R4-D:           CONTRACT ACCEPTED / APPLY BLOCKED
```
