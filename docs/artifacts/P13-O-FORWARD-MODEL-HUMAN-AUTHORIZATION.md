# P13-O Forward Model — Human Authorization Record (FROZEN) — 2026-10-05

> STATUS: **FROZEN / HUMAN AUTHORIZED FOR FUTURE TRAINING**
>
> Revision history:
> v1 (draft, commit `0da4b45`): PROPOSED authorization parameters.
> v2 (this record, FROZEN): parameter set FROZEN per the project owner's
> Human Authorization (P13-O-FORWARD-MODEL-HUMAN-AUTHORIZATION-001);
> feature_set_id and scope_sha256 COMPUTED per P13O-F-014/016b/016c;
> label-availability exclusion rules recorded per P13O-F-009.
>
> **This record authorizes the PARAMETER FREEZE for a future training
> phase. It does NOT record any execution:**
>
> ```text
> TRAINING EXECUTION:            NOT YET EXECUTED
> MODEL_APPLICATION artifact:    NOT CREATED
> model_version:                 NOT YET AVAILABLE
> CALIBRATION artifact:          NOT CREATED
> R4-D:                          CONTRACT ACCEPTED / APPLY BLOCKED
>                                (IMPLEMENTATION NOT AUTHORIZED)
> ```

## 一、Frozen identity & parameters

```text
model_id:              p13o-forward-logistic
model_version:         NOT YET AVAILABLE
model_variant:         industry_5_20
feature_set_id:        fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe
training_protocol_id:  p13o-logistic-gd-500x0.05-v1
scope:                 universe-d8c5016b1ded0984
scope_sha256:          b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1
seed:                  20260929
```

- **model_version = NOT YET AVAILABLE**: it is the full lowercase SHA-256
  of the canonical frozen MODEL_APPLICATION artifact bytes (P13O-F-002)
  and can only be computed at the future freeze. Not generated, not
  simulated, not pre-claimed.
- **feature_set_id = `fs-d1f3bdca…3afe`** — COMPUTED per P13O-F-014 +
  P13O-F-016c from the canonical ordered `[name, definition_version]`
  list below (canonical bytes → SHA-256, prefixed `"fs-"`). Not guessed,
  not shortened.
- **scope_sha256 = `b7d807a3…64c1`** — SHA-256 of the canonical scope
  JSON (P13O-F-016b): `{"symbols":[<76 sorted symbols>],
  "universe_id":"universe-d8c5016b1ded0984"}`.

## 二、Variant authority（P13O-F-005/006）

```text
variant = industry_5_20        — by Human Authorization
```

This variant is NOT: metric selection · Brier selection · latest
selection · first selection · automatic selection · validation
selection. Train-all-then-pick is forbidden (P13O-F-007); the variant
MUST NOT change after validation results are observed. Authorized
rationale (verbatim): **it is consistent with the existing P13-Q
calibrated 6-factor feature lineage — lineage / feature-contract
continuity; this is NOT a historical-performance optimization.**

## 三、Frozen feature set (order = weight-vector order)

```text
1. momentum
2. volatility
3. trend
4. volume_ratio
5. industry_relative_return_5
6. industry_relative_return_20
```

**definition_version convention** (the repository has no pre-existing
feature-version mechanism — audited): `definition_version =
"<defining source file path>@<git blob sha of that file at the frozen
HEAD>"` — unambiguous and auditable via `git cat-file`:

| features | definition_version |
|---|---|
| momentum, volatility, trend, volume_ratio | `src/astock_v2/local_pipeline.py@0582f91ef406d329c7ce3d7460db8f467c20ef75` |
| industry_relative_return_5, industry_relative_return_20 | `scripts/run_local_industry_relative_oos.py@0b6c0f140fad636a50cee67d2502d6ce27adc5cb` |

**Canonical hashed input** (the exact bytes hashed for
feature_set_id):

```json
[["momentum","src/astock_v2/local_pipeline.py@0582f91ef406d329c7ce3d7460db8f467c20ef75"],["volatility","src/astock_v2/local_pipeline.py@0582f91ef406d329c7ce3d7460db8f467c20ef75"],["trend","src/astock_v2/local_pipeline.py@0582f91ef406d329c7ce3d7460db8f467c20ef75"],["volume_ratio","src/astock_v2/local_pipeline.py@0582f91ef406d329c7ce3d7460db8f467c20ef75"],["industry_relative_return_5","scripts/run_local_industry_relative_oos.py@0b6c0f140fad636a50cee67d2502d6ce27adc5cb"],["industry_relative_return_20","scripts/run_local_industry_relative_oos.py@0b6c0f140fad636a50cee67d2502d6ce27adc5cb"]]
```

## 四、Frozen time windows & label availability（P13O-F-008/009）

Interval semantics frozen VERBATIM (half-open as written):

```text
training    = [2020-01-02, 2025-01-01)
calibration = [2025-01-01, 2025-07-01)
validation  = [2025-07-01, 2026-09-22]
research_end = 2026-09-22
virgin_start = 2026-09-23
```

**Label-availability exclusion rule** (P13O-F-009; the label of decision
day t is the NEXT trading day's close, so a row is included only when
its label closes on or before its window's boundary date). Verified
against the real trading calendar (all dates below confirmed as trading
days in the local store):

| window | first decision date | last INCLUDED decision date | label close of last row | boundary-excluded decision rows |
|---|---|---|---|---|
| training [2020-01-02, 2025-01-01) | 2020-01-02 | **2024-12-30** (Mon) | 2024-12-31 (≤ boundary) | 2024-12-31 — its label would close 2025-01-02 > boundary |
| calibration [2025-01-01, 2025-07-01) | 2025-01-02 | **2025-06-30** (Mon) | 2025-07-01 (≤ boundary) | 2025-07-01 — belongs to validation |
| validation [2025-07-01, 2026-09-22] | 2025-07-01 | **2026-09-21** (Mon) | 2026-09-22 (≤ boundary) | 2026-09-22 — its label would close 2026-09-23 (past boundary AND first virgin date) |

No decision date on or after 2026-09-23 exists in any window. The
boundary decision rows listed above are explicitly EXCLUDED by the
label-availability rule and MUST NOT be silently re-included at training
time.

## 五、Frozen scope（P13O-F-016b）

```text
universe_id  = universe-d8c5016b1ded0984   (loader convention, matches frozen value)
scope file   = data/industry/validation_universe_76.txt   (committed at a1a8d32)
symbol count = 76 (unique, 6-digit canonical, sorted — verified)
scope_sha256 = b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1
```

## 六、Frozen training protocol（P13O-F-012）

`training_protocol_id = "p13o-logistic-gd-500x0.05-v1"`:
unregularized binary logistic regression · full-batch gradient descent ·
500 epochs · learning rate 0.05 · zero initialization (weights + scalar
bias) · float64 · stable sigmoid (clip ±30) · no scaler · preprocessing
= identity · rows sorted by `(decision_time, symbol)` · one row per
`(symbol, decision_time)` · missing-factor rows dropped
deterministically · **SINGLE FINAL MODEL** fitted on the whole training
window · no fold-model collection as production artifact.

**seed = 20260929** — execution/manifest metadata only; the protocol is
deterministic full-batch GD and the seed is NOT a model-selection
mechanism.

**prediction semantics** (verbatim, P13O-F-016a): `target = "next
trading day close-up direction"` · `horizon = "next_trading_day"` ·
`positive_class = "next_return > 0"`.

## 七、Authorization semantics（两层区分）

```text
Proposed / Candidate:      recorded in AUTHORIZATION-CANDIDATES (accepted)
Final Human Authorization: THIS RECORD — the parameter freeze above
TRAINING EXECUTION:        NOT YET EXECUTED
MODEL_APPLICATION artifact: NOT CREATED
model_version:             NOT YET AVAILABLE
Calibration artifact:      NOT CREATED
```

This record authorizes the parameter freeze for a FUTURE training phase;
it does not record any execution and does not make the model "ready" or
"calibrated".

## 八、R4-D & boundaries（unchanged）

```text
R4-D   = CONTRACT ACCEPTED / APPLY BLOCKED
R4-D implementation = NOT AUTHORIZED
P14-F  = NOT AUTHORIZED
P13-T  = STOPPED / NOT EXECUTED
P13-U  = PROTECTED
```

Human Authorization Record 完成 ≠ R4-D implementation authorization.
P14-D remains the sole PIT/selection authority; P14-E the sole
evidence/provenance authority; P13-Q the calibration research authority
(its successor issues the new bound calibration under a separate
authorization); P13-R the policy authority.
