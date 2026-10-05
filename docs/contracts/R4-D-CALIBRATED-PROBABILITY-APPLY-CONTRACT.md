# R4-D Contract — Calibrated Probability Apply-Path

> STATUS: DRAFT — R4-D-DESIGN-001 — awaiting independent Contract acceptance.
> **R4-D Implementation is NOT AUTHORIZED** until this contract passes
> independent acceptance AND the owner grants Human Authorization.
> Companion design: `docs/design/R4-D-CALIBRATED-PROBABILITY-APPLY-DESIGN.md`.
>
> 修订历史：
> v1: 初稿（R4-D-DESIGN-001，设计 gate；审计基线 Exact HEAD `264c59a`）
> v2: NARROW-REPAIR-001（2026-10-05）——独立验收 FAIL 后的三闭环修复：
>     区分三类 artifact（历史 OOS 预测 / 模型应用 / 校准）；新增
>     R4D-002a/002b/003a/003b/003c；golden 增补 G11–G16；建立
>     docs/artifacts/R4-D-APPLY-ARTIFACT-EVIDENCE.md 证据文件。
>     审计结论：仓库内不存在可前向应用的 frozen raw-model
>     artifact（P13-O 折内权重未持久化；p13p 文件为指标对比非
>     模型参数）→ R4-D = BLOCKED — RAW MODEL APPLY AUTHORITY
>     NOT FROZEN（§13）。文档-only，零生产代码。

---

## 1. Purpose & Scope

Define the single authorized path from the accepted P13-Q/P13-R frozen
calibration/policy artifacts to a probability-bearing recommendation
inside the R4-A research loop. This contract DEFINES; it does not
implement. Normative invariants `R4D-001…R4D-020`.

## 2. Existing Authorities (referenced, never re-implemented)

- **R4D-001 (label semantics)**: probability target = P13-M frozen
  definition — `label = int(next trading day close return > 0)`, factors
  strictly visible at decision time. Horizon = `next_trading_day`. The
  probability means `P(next_trading_day close-up | information visible at
  as_of)`. No redefinition permitted.
- **R4D-002 (raw model identity)**: `model_id = "p13o-pooled-industry-relative-logistic"`;
  `model_version` = the pinned tuple recorded in
  `data/industry/p13o/analysis_config.json` (git `4d792100…`, protocol
  252/20/20/1, seed 20260929, variant ∈ {baseline, industry_5,
  industry_20, industry_5_20}). Scope = the frozen 76-stock universe.
- **R4D-003 (calibration authority)**: `calibration_id =
  "p13q-calibration-registry"`; `calibration_version` = sha256 of
  `data/industry/p13q/calibration_registry.json` (`643a3dcd…`, pinned by
  `p13q/manifest.json`). Fitted parameters pinned in
  `p13q/calibration_methods.json`: platt slope `0.16256174917600796`,
  intercept `−0.11864470583968838`; split_date `2025-01-01`.
- **R4D-004 (policy authority)**: `policy_version` = sha256 of
  `data/industry/p13r/decision_policy_registry.json` (`361791f8…`).
  Apply-path policy (frozen): `threshold_platt_p50` (calibrated
  probability ≥ 0.5).
- **R4D-005 (feature set identity)**: `feature_set_id` = the
  `factor_list` of `p13q/analysis_config.json` (sha256 `f0602bb9…`):
  momentum, volatility, trend, volume_ratio, industry_relative_return_5,
  industry_relative_return_20.
- **R4D-002a (raw-model application authority)**: the runtime `p_raw` source is a
  MODEL_APPLICATION artifact — a frozen, forward-applicable set of fitted model
  parameters with complete feature mapping and version identity. **Audit
  conclusion (Exact HEAD `0406abc`): no such artifact exists in this repository**
  (P13-O fold weights were transient; `p13p/incremental_models.json` holds OOS
  metric comparisons, not parameters). Implementation authorization is therefore
  BLOCKED per R4D-003b — no runtime may retrain, refit, or fabricate `p_raw`.
- **R4D-002b (variant identity)**: the exact `model_variant` ∈ {baseline,
  industry_5, industry_20, industry_5_20} MUST be frozen in the future
  MODEL_APPLICATION artifact. Auto-selection (best/latest/first/highest-metric/
  arbitrary) is forbidden at runtime AND at contract level. **Audit finding**: the
  P13-Q calibration is variant-POOLED (no variant dimension in
  `p13q/analysis_config.json` / `probability_audit.json`) → the
  calibration↔variant binding is UNRESOLVED until a variant-bound recalibration
  is issued by a future authorized phase.
- **R4D-003a (calibration binding)**: a calibration artifact is apply-usable only
  against the exact raw-model variant and feature set it was fitted for. The
  current P13-Q registry (variant-pooled) is NOT yet bound; binding requires the
  future artifact pair (variant-bound MODEL_APPLICATION + variant-bound
  calibration re-issue) with matching `model_variant` + `feature_set_id`.
- **R4D-003b (reproducibility gate)**: R4-D implementation authorization requires
  a MODEL_APPLICATION artifact independently frozen and auditable per
  `docs/artifacts/R4-D-APPLY-ARTIFACT-EVIDENCE.md` (identity fields: artifact_id,
  sha256, model_id/version/variant, feature_set_id, protocol, scope, status,
  provenance). Until that act, **R4-D = BLOCKED — RAW MODEL APPLY AUTHORITY NOT
  FROZEN**.
- **R4D-003c (historical/forward separation)**: HISTORICAL_OOS_PREDICTION
  artifacts (`oos_predictions_76.json`) MUST NOT be used as `p_raw` for any
  current or future research run — they are records of past runs, not a forward
  model. Supplying one where a forward artifact is required is
  `INELIGIBLE("historical_prediction_as_model")` (G16) and fails closed.
- **R4D-006 (PIT/evidence)**: P14-D remains the sole PIT/selection
  authority; P14-E the sole evidence/provenance authority. R4-D adds NO
  time filter and NO second visibility rule; virgin protection stays
  `assert_research_zone`.

## 3. Apply Formula (frozen)

**R4D-007**: apply method = **platt only**.
`calibrated = sigmoid(a + b · logit(p_raw))`, `_logit(p)=ln(p/(1−p))`,
all clips ±30; a/b from R4D-003. Reproduction must be bit-exact against
a fixture golden. `isotonic` = `INELIGIBLE("calibration_params_incomplete")`
(its step curve is not registry-persisted); `raw` is never a probability
source (never surfaced as calibrated; P13-Q: slope 0.167 compression).

## 4. Eligibility (resolver states — exhaustive)

**R4D-008**: the resolver returns exactly one state:
- `CALIBRATED` — all of E1–E5 hold;
- `NOT_AVAILABLE(reason)` — registry/artifact unreadable or required
  fields absent (E1/E2 fail on read);
- `INELIGIBLE(reason)` — E3–E5 fail, reason ∈
  {`temporal_below_split`, `temporal_after_research_end`,
  `feature_set_mismatch`, `symbol_out_of_scope`,
  `calibration_params_incomplete`}.

Eligibility rules:
- **E1 (artifact readable)**: registry JSON parses; required fields
  present (split_date, methods.platt params via calibration_methods.json).
- **E2 (status)**: registry method status is `research_only` — apply is
  authorized ONLY inside the research agent loop (RESEARCH/PAPER_TEST/
  NO_ACTION posture); production trading use remains forbidden.
- **E3 (temporal)**: `split_date ≤ as_of ≤ RESEARCH_END` — the accepted
  P13-Q a-priori protocol (fit strictly on discovery rows < split_date,
  65,795 rows; evaluated OOS ≥ split_date, 28,965 rows) normatively
  fixes the temporal reading of these artifacts. Below split_date the
  calibration is in-sample → ineligible; ≥ VIRGIN_START is already
  fail-fast upstream.
- **E4 (feature compatibility)**: the packet's factor set (names +
  computation identity) equals `feature_set_id` (R4D-005). TODAY this
  fails honestly (R4-A packet carries 4 of the 6 factors) — the resolver
  must return `INELIGIBLE("feature_set_mismatch")`, never approximate.
- **E5 (scope)**: symbol ∈ frozen 76 universe (`universe-d8c5016b1ded0984`).

## 5. Probability Semantics & No-Silent-Fallback

**R4D-009**: the resolver's probability block is
`{probability_status, probability, probability_horizon="next_trading_day",
model_id, model_version, calibration_id, calibration_version,
policy_id, policy_version, feature_set_id, eligibility_reason}`
— `probability` present **iff** `probability_status == "CALIBRATED"`.
**R4D-010**: no silent fallback — a missing/ineligible calibration never
yields a default or raw score as `probability`; downstream decisions
consume the STATUS explicitly (NOT_AVAILABLE → existing R4-A behavior:
RESEARCH/NO_ACTION with reason). **R4D-011**: `confidence` remains None
(no frozen definition exists; honesty over decoration).

## 6. Recommendation & Ledger Integration

**R4D-012**: decision mapping when `CALIBRATED`: frozen policy
`threshold_platt_p50` — calibrated p ≥ 0.5 → decision class
`PAPER_TEST` (action HOLD); else `RESEARCH`; the existing quality
(<0.75 → NO_ACTION) and risk gates apply unchanged. `policy unavailable`
→ NO_ACTION with explicit reason (never silent).
**R4D-013**: ledger `input_snapshot` gains the full R4D-009 block — the
provenance chain Recommendation → Probability → Calibration → Model →
Features → ResearchPacket → P14-E bundle → P14-D selection state is
mechanically traceable.
**R4D-014**: the ONLY R4-A production touch at implementation (under
separate authorization) is the orchestrator consuming R4D-009 in place
of the legacy `p_up[5]` scaffold key (the calibrated horizon is
next-trading-day; the 5-day key is semantically wrong for this
probability). Everything else in R4-A/B/C is unchanged.

## 7. Registry Read-Only Boundary

**R4D-015**: the apply path is READ-ONLY over `data/industry/p13q/` and
`data/industry/p13r/` — no writes, no promotion, no threshold change, no
registry rewrite. Ledger appends (existing mechanism) are not registry
promotions.

## 8. Temporal/Virgin Boundaries

**R4D-016**: no virgin-zone consumption in any form; P13-T remains
STOPPED / NOT EXECUTED; P13-U remains PROTECTED. If a future calibrated
apply claim requires holdout data: STOP.

## 9. Golden Cases (implementation-time, fixture-based)

**R4D-017**: G1 valid apply (bit-exact formula vs fixture) · G2
calibration unavailable → NOT_AVAILABLE · G3 policy unavailable →
NO_ACTION + reason · G4 as_of < split_date → INELIGIBLE(temporal) · G5
as_of > RESEARCH_END → INELIGIBLE(temporal) · G6 symbol out of scope ·
G7 feature mismatch · G8 replay byte-identical · G9 ledger provenance
complete (R4D-013 fields) · G10 registry bytes unchanged by apply · G11 raw-model artifact missing →
NOT_AVAILABLE, no fabricated p_raw · G12 model_variant mismatch →
INELIGIBLE(`model_variant_mismatch`) · G13 calibration bound to a different
variant → INELIGIBLE(`calibration_model_mismatch`) · G14 feature-set
identity mismatch → INELIGIBLE(`feature_set_mismatch`) · G15 frozen-artifact
hash mismatch → FAIL CLOSED (abort, no output) · G16 historical OOS
prediction artifact supplied where a forward model artifact is required →
REJECTED / NOT_AVAILABLE (R4D-003c).

## 10. Harness

**R4D-018**: one minimal pytest harness group `tests/contracts/r4d/`
covering R4D-017 G1–G10 (authority, temporal, read-only, provenance
boundaries). No new standalone audit script; no additional governance
phases.

## 11. Out of Scope (forbidden at implementation)

**R4D-019**: no retraining, no recalibration, no threshold search, no
registry writes/promotions, no new probability semantics, no policy
redesign, no P14-D/E changes, no R4-A/B/C redesign (beyond R4D-014), no
P14-F, no holdout use, no performance claims (P13-R: no policy
significantly beat hold-all — a calibrated probability is honesty, not
alpha).

## 13. Raw-Model Application Authority — NOT FROZEN (blocker record)

Audit at Exact HEAD `0406abc` (R4-D-NARROW-REPAIR-001): **no forward-applicable
frozen raw-model artifact exists in this repository.** P13-O fold weights were
transient (fit_predict returns predictions; weights discarded); the only persisted
model-adjacent files are HISTORICAL_OOS_PREDICTION records (forbidden as p_raw by
R4D-003c) and OOS metric comparisons (not parameters). The P13-Q calibration is
variant-pooled with no binding record.

```text
R4-D BLOCKED — RAW MODEL APPLY AUTHORITY NOT FROZEN

R4-D Contract cannot authorize implementation until a raw-model
application authority (MODEL_APPLICATION artifact, variant-bound and
feature-bound, with independent evidence per
docs/artifacts/R4-D-APPLY-ARTIFACT-EVIDENCE.md) is frozen by a future
authorized phase.
```

This is a legal outcome, not a failure: R4D-002a/002b/003a/003b/003c and
G11–G16 define exactly what must exist before re-acceptance can authorize
implementation. Everything else in this contract (semantics, eligibility
states, read-only boundary, provenance chain, fallback rules) is already
specified and remains frozen text.

## 12. Acceptance Checklist (task §18 mapping)

[×] Existing probability/calibration/policy authorities identified
    (R4D-002/003/004) · [ ] **raw-model application authority frozen
    (R4D-002a/003b) — UNMET: BLOCKED** · [×] Probability semantics frozen (R4D-001) ·
    [×] Calibration semantics frozen (R4D-003/007) · [×] Apply
    eligibility (R4D-008) · [×] PIT/temporal rule (R4D-006/R4D-008-E3) ·
    [×] Model/calibration/policy version rules (R4D-002/003/004) · [×]
    Feature compatibility (R4D-005/E4) · [×] Scope eligibility (E5) ·
    [×] NOT_AVAILABLE semantics + no silent fallback (R4D-009/010) ·
    [×] Registry read-only (R4D-015) · [×] Recommendation integration
    point (R4D-012/014) · [×] Ledger provenance (R4D-013) · [×] Golden
    cases (R4D-017) · [×] Harness assessed (R4D-018) · [×] P13-T/U
    protected (R4D-016) · [×] No production code / registry / policy
    change in THIS phase · [×] R4-A/B/C unchanged in THIS phase.
