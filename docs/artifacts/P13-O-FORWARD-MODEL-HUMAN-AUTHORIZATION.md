# P13-O Forward Model — Human Authorization Record (DRAFT) — 2026-10-05

> STATUS: **PROPOSED AUTHORIZATION — NOT YET EXECUTED**.
> This is the formal authorization RECORD DRAFT prepared for the project
> owner's final explicit approval. NOTHING in it authorizes execution by
> its existence: **TRAINING AUTHORIZATION = NOT YET EXECUTED**. No
> training, fitting, calibration, threshold optimization, or artifact
> creation has been performed or is authorized by this document alone.
> Baseline: Exact HEAD `2235471` (CANDIDATES = PASS / INDEPENDENTLY
> ACCEPTED).

## 一、Proposed authorization parameters（拟授权参数，逐字冻结草案）

```text
model_id:              p13o-forward-logistic
model_variant:         industry_5_20
feature_set (ordered):
    1. momentum
    2. volatility
    3. trend
    4. volume_ratio
    5. industry_relative_return_5
    6. industry_relative_return_20
training_start:        2020-01-02
training_end:          2025-01-01
calibration_start:     2025-01-01
calibration_end:       2025-07-01
validation_start:      2025-07-01
validation_end:        2026-09-22
research_end:          2026-09-22
virgin_start:          2026-09-23
training_protocol_id:  p13o-logistic-gd-500x0.05-v1
scope:                 universe-d8c5016b1ded0984
scope file:            data/industry/validation_universe_76.txt
seed:                  20260929
prediction semantics:
    target         = next trading day close-up direction
    horizon        = next_trading_day
    positive_class = next_return > 0
```

## 二、Time-interval semantics（逐字冻结，不得改写）

```text
training    = [2020-01-02, 2025-01-01)
calibration = [2025-01-01, 2025-07-01)
validation  = [2025-07-01, 2026-09-22]
```

Half-open intervals exactly as written — no alternative
inclusive/exclusive combination is permitted.

**Validation last actual decision date**: `2026-09-21`（周一）— the
trading day strictly before `validation_end`; its label closes
**2026-09-22**（周二，research zone 内）— label availability satisfied
(P13O-F-009). No decision date in any window is on or after
`virgin_start` (2026-09-23).

## 三、Variant authority（P13O-F-005/006）

```text
model_variant = industry_5_20
```

This variant is the **Human Authorization decision**. It is NOT:
metric selection · Brier selection · latest selection · first selection
· automatic selection · validation selection. The variant MUST NOT be
changed after validation results are observed (P13O-F-007 — such a
change is leakage and is BLOCKED).

Feature-set implication (consistency fact, recorded at precheck):
this variant's ordered feature tuple coincides with the P13-Q
calibrated 6-factor `factor_list` (config sha256 `f0602bb9…`); the NEW
bound calibration (P13O-F-018/019) is still mandatory — the coincidence
grants nothing.

## 四、feature_set_id（生成于 artifact 冻结时；不得提前伪造）

Per P13O-F-014 + P13O-F-016c:

```text
feature_set_id = "fs-" + SHA256( canonical_json([
    ["momentum",    <definition_version>],
    ["volatility",  <definition_version>],
    ["trend",       <definition_version>],
    ["volume_ratio",<definition_version>],
    ["industry_relative_return_5", <definition_version>],
    ["industry_relative_return_20",<definition_version>],
]) )
```

- The ordered names above are the authorized order (weight-vector order).
- `<definition_version>` candidate lineage: `p13m-local-pipeline-v1`
  (the historical definitions); the exact values are confirmed at the
  execution-authorization record — NOT guessed here.
- `feature_set_id` is COMPUTED at artifact-generation time from the
  canonical frozen list. **No hash is pre-computed or claimed in this
  draft; no short hash is permitted.**

## 五、model_version

```text
model_version = NOT YET AVAILABLE
```

Reason: `model_version` is the full lowercase SHA-256 of the canonical
frozen MODEL_APPLICATION artifact bytes (P13O-F-002) and can only be
computed after the future freeze. It is not generated, simulated, or
pre-claimed here.

## 六、Authorization states（两层区分）

```text
PROPOSED AUTHORIZATION   = the parameter set in §一 (this draft)
EXECUTION AUTHORIZATION  = NOT GRANTED YET

TRAINING AUTHORIZATION   = NOT YET EXECUTED
CALIBRATION AUTHORIZATION = NOT YET EXECUTED
```

This record becomes EXECUTION- BINDING only upon the project owner's
final explicit approval of THIS draft (at which point the training
phase may start under the frozen parameters, C1–C2 satisfied).

## 七、R4-D / boundaries (unchanged)

```text
R4-D   = CONTRACT ACCEPTED / APPLY BLOCKED (IMPLEMENTATION NOT AUTHORIZED)
P14-F  = NOT AUTHORIZED
P13-T  = STOPPED / NOT EXECUTED
P13-U  = PROTECTED
```

No candidate in this record touches the virgin zone; all window decision
dates ≤ 2026-09-22 (research_end). P14-D remains the sole PIT/selection
authority; P14-E the sole evidence/provenance authority; P13-Q the
calibration research authority (its successor issues the new bound
calibration); P13-R the policy authority.
