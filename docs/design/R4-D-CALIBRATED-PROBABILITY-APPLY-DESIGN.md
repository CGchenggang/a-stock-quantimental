# R4-D — Calibrated Probability Apply-Path — Design (D1)

> STATUS: DRAFT — R4-D-DESIGN-001 — awaiting independent Contract acceptance.
> Design only; NO implementation is authorized by this document.
> Companion normative contract: `docs/contracts/R4-D-CALIBRATED-PROBABILITY-APPLY-CONTRACT.md`.

## 1. Problem

R4-A's research loop currently stops at `probability = NOT_AVAILABLE`: the
agent computes factors/risk honestly but has no approved path from the
accepted P13 calibration artifacts to a probability-bearing
recommendation. The product gap: a frozen, versioned, independently
accepted calibrated model cannot yet be safely APPLIED inside the
research agent boundary.

## 2. Current Architecture (audited at Exact HEAD `264c59a`)

```text
P13-M local_pipeline            label = int(next trading day close return > 0)
  → P13-O run_local_industry_relative_oos.py
        model = pooled logistic (vectorized NumPy, epochs 500, lr 0.05),
        walk-forward protocol 252/20/20/1, seed 20260929,
        variants baseline / industry_5 / industry_20 / industry_5_20
        artifact data/industry/p13o/oos_predictions_76.json (94,760 rows,
        fields: symbol, decision_time, variant, p, y, baseline_p)
  → P13-Q run_p13q_analysis.py  calibration of raw p
        artifacts data/industry/p13q/* pinned by manifest.json sha256
        (calibration_registry.json = 643a3dcd…, analysis_config.json =
        f0602bb9… with factor_list, calibration_methods.json with
        fitted_parameters)
  → P13-R run_p13r_analysis.py  8 frozen decision policies
        data/industry/p13r/decision_policy_registry.json (361791f8…,
        p13r/manifest.json pins all files), split_date recorded
  → R4-A agent/research_run.py  probability section honestly
        NOT_AVAILABLE; decision scaffold agent/orchestrator.py
        (quality<0.75→NO_ACTION; calibrated∧p5≥0.60→PAPER_TEST; else
        RESEARCH; PAPER_TEST→HOLD)
  → R4-B/C batch & validation   orchestrate run_research unchanged
```

## 3. Existing Authorities (reused, not re-implemented)

| Authority | Identity (frozen) | Notes |
|---|---|---|
| Probability label semantics | P13-M `local_pipeline.py:104,220`: `label = int(next_return > 0)` — **next trading day's close-up**, factors strictly available at decision time | Referenced verbatim; R4-D does not redefine it |
| Raw probability model | P13-O audit config: git `4d792100518937aef6988d61e2311397d553d75f`, protocol 252/20/20/1, seed 20260929, 4 variants, universe = frozen 76 | model scope = the 76 universe symbols |
| Calibration authority | `p13q/calibration_registry.json` (sha256 `643a3dcd…`): `split_date=2025-01-01`, methods raw/platt/isotonic with training/evaluation periods and metrics; `p13q/calibration_methods.json`: **platt fitted_parameters slope=0.16256174917600796, intercept=−0.11864470583968838**; `p13q/manifest.json` pins all sha256 | status `research_only` by design + status_rule recorded |
| Decision policy authority | `p13r/decision_policy_registry.json` (sha256 `361791f8…`): 8 policies (hold_all, threshold_{raw,platt,iso}_p50, topk_platt_k3, percentile_platt_p80, er_platt_0, er_platt_pos_risk) | all `research_only`; calibration_method binding explicit |
| PIT / selection | P14-D `run_query` (available_time ≤ as_of) | sole visibility authority |
| Evidence / provenance | P14-E `create_bundle` / bundle_id | sole evidence authority |
| Research loop | R4-A `run_research`, R4-B `run_research_batch`, R4-C validation | unchanged |

## 4. Apply Path (design)

```text
R4-A ResearchPacket (factors/evidence/risk already resolved)
        ↓
R4-D probability resolver (NEW, read-only):
    load frozen calibration registry + policy registry (paths pinned)
      → eligibility resolution (E1–E5 below)
      → platt apply: sigmoid(a + b·logit(p_raw)), clip ±30   [G1 formula]
      → probability block {status, value, horizon, identities, reason}
        ↓
existing orchestrator decision (single minimal delta: consume the
resolver's probability block instead of the legacy p_up[5] scaffold)
        ↓
existing RecommendationRecord + existing append-only Ledger
        ↓
input_snapshot gains calibration/policy identity (R4-A mechanism reused)
```

Key formulas (pinned from the frozen artifacts — apply code must
reproduce exactly):
- `_logit(p) = ln(p/(1−p))` (clip ±30 both directions);
- `calibrated = sigmoid(a + b·logit(p_raw))`, a=−0.11864470583968838,
  b=0.16256174917600796 (p13q/calibration_methods.json fitted_parameters.platt);
- **platt is the ONLY apply-eligible method**: the isotonic step curve is
  not fully persisted in the registry (only train_min/train_max clips),
  so isotonic = `INELIGIBLE(calibration_params_incomplete)`; raw is
  never a probability source (slope 0.167 compression, P13-Q finding).

## 5. Eligibility Contract (resolver states)

| State | Condition |
|---|---|
| `CALIBRATED` | all E1–E5 pass → probability value present |
| `NOT_AVAILABLE` | registry/artifact unreadable or required fields missing (reason recorded) |
| `INELIGIBLE(temporal)` | as_of < split_date (2025-01-01, calibration in-sample) or as_of > RESEARCH_END |
| `INELIGIBLE(feature_set)` | packet factor set ≠ frozen factor_list (TODAY'S REAL STATE: R4-A computes 4 factors; calibrated feature set = 6 incl. industry_relative_return_5/20 → honest mismatch until the packet carries the calibrated set) |
| `INELIGIBLE(scope)` | symbol outside the frozen 76 universe |
| `INELIGIBLE(params)` | method ≠ platt / fitted params absent (isotonic) |

No silent fallback: a raw model score is NEVER surfaced as a calibrated
probability; uncalibrated paths keep R4-A's `NOT_AVAILABLE` semantics
with an explicit reason.

## 6. Temporal Safety

Sole rule: `eligible ⇔ split_date ≤ as_of ≤ RESEARCH_END` — read from
the registry's own `split_date` and the frozen `research_boundary`
constants. The future-calibration problem (artifact knowledge-time) is
superseded by the ACCEPTED P13-Q a-priori protocol (fit strictly on
discovery rows < split_date; evaluated OOS on ≥ split_date — 28,965
rows): the contract normative-fixes this boundary reading. No second
time filter is created; virgin-zone protection remains
`assert_research_zone` in R4-A/P14-D.

## 7. Provenance & Ledger

Resolver output block (consumed verbatim by decision + ledger):
`{probability_status, probability, probability_horizon="next_trading_day",
model_id, model_version, calibration_id, calibration_version,
policy_id, policy_version, feature_set_id, eligibility_reason}`.
Ledger `input_snapshot` (existing R4-A mechanism) gains exactly these
fields — the chain Recommendation → Probability → Calibration → Model →
Features → ResearchPacket → P14-E bundle → P14-D selection state becomes
fully traceable.

## 8. Registry Mutation Boundary

Resolver is **READ-ONLY** over `data/industry/p13q/` and
`data/industry/p13r/`. No writes, no promotion, no threshold changes.
Ledger appends remain the existing R4-A mechanism (a ledger append is
never a registry promotion).

## 9. Recommendation Integration (minimal delta)

Unchanged: research_run.py pipeline, orchestrator rule SHAPE, ledger.
Single implementation-phase delta (requires separate authorization):
orchestrator consumes the resolver's probability block (replacing the
legacy `p_up[5]` key — the calibrated horizon is next-trading-day, so
the legacy 5-day key is semantically wrong for this probability).
Decision mapping (frozen policy `threshold_platt_p50`): probability
CALIBRATED ∧ p ≥ 0.5 → PAPER_TEST (action HOLD); else RESEARCH;
NO_ACTION per the existing quality/risk gates. Confidence: resolver
reports `1 − brier` context? NO — confidence stays None until a frozen
definition exists (honest).

## 10. Golden Cases

G1 valid apply (fixture registry, formula pinned) · G2 calibration
unavailable → NOT_AVAILABLE · G3 policy unavailable → NO_ACTION +
reason · G4 as_of < split_date → INELIGIBLE(temporal) · G5 as_of >
RESEARCH_END → INELIGIBLE(temporal) · G6 symbol outside 76 →
INELIGIBLE(scope) · G7 feature mismatch → INELIGIBLE(feature_set) ·
G8 replay byte-identical · G9 ledger provenance complete · G10 registry
bytes unchanged after apply (read-only).

## 11. Harness Requirement

ONE new minimal pytest harness group `tests/contracts/r4d/` covering
G1–G10 (critical authority/temporal/registry-read-only/provenance
boundaries). No new standalone audit script, no docs scanner — closure
is by these tests + independent review.

## 12. Failure Modes & Boundaries

Never: silent raw-as-calibrated fallback; silent default probability;
registry writes; virgin consumption; P13-T execution. P13-T STOPPED /
P13-U PROTECTED unchanged. No performance claims: applying the
calibration makes the probability honest, not alpha (P13-R: no policy
beat hold-all).

## 13. Raw-Model Application Authority — NOT FROZEN (NARROW-REPAIR-001)

NARROW-REPAIR-001 audit (Exact HEAD `0406abc`): the apply path's `p_raw`
source has **no frozen forward-applicable artifact**. P13-O fold models
were transient; `p13p/incremental_models.json` is OOS metric comparisons
(A/B/C/D), not parameters; the only persisted prediction records
(`oos_predictions_76.json`) are HISTORICAL_OOS_PREDICTION and forbidden
as runtime input (R4D-003c). The P13-Q calibration is variant-POOLED —
no calibration↔variant/feature binding is recorded. Evidence inventory
with audited sha256 values:
`docs/artifacts/R4-D-APPLY-ARTIFACT-EVIDENCE.md`.

Consequence: **R4-D = BLOCKED — RAW MODEL APPLY AUTHORITY NOT FROZEN.**
A future authorized phase must produce a variant-bound, feature-bound
MODEL_APPLICATION artifact (re-fitted under the accepted protocol with a
fresh a-priori window decision) and append its evidence row; only that
unblocks implementation. New invariants R4D-002a/002b/003a/003b/003c and
golden G11–G16 (contract v2) freeze the requirement; runtime
auto-selection of variant/calibration/policy is forbidden.

## 14. Acceptance Criteria

See contract §12 checklist (mirrors task §18 — all items answered
above; implementation explicitly NOT authorized by this design).
