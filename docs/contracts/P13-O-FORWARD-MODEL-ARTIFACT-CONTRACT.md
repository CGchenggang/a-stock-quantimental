# P13-O Forward Model Artifact — Contract

> STATUS: PASS / INDEPENDENTLY ACCEPTED — P13-O-FORWARD-MODEL-001 CONTRACT + DESIGN.
> **Training / artifact creation remain unauthorized until the Human
> Authorization Record is executed** (P13O-F-027: C1–C12 then final Human
> Authorization); this status line records the CONTRACT acceptance only.
> Companion design: `docs/design/P13-O-FORWARD-MODEL-ARTIFACT-DESIGN.md`.
>
> 修订历史：
> v1: 初稿（P13-O-FORWARD-MODEL-001，设计 gate；基线 Exact HEAD `3cdd1ee`；
>     前置事实：P13-O-ARTIFACT-001 = PASS / NOT RECOVERABLE）
> v2: NARROW REPAIR（2026-10-05，P13-O-FORWARD-MODEL-002）——四处闭环：
>     R1 scope 规范字段（P13O-F-016b + F-022 schema）；R2 预测语义
>     规范冻结（P13O-F-016a）；R3 规范序列化（P13O-F-016c）；
>     R4 model_version = 全长小写 SHA-256（P13O-F-002 修订）。
>     文档-only，零生产代码。

---

## 1. Purpose & Core Semantic

Define the governance for creating ONE new, uniquely identified,
variant-bound, feature-bound, forward-applicable, GitHub-auditable
MODEL_APPLICATION artifact. **P13O-F-000**: the future artifact is a NEW
FORWARD-APPLY MODEL — it MUST NOT be presented as a recovered P13-O
model (the old artifact is frozen NOT RECOVERABLE); it receives new
model_id, model_version, artifact hash, provenance and freeze record.
Normative invariants `P13O-F-001..P13O-F-026`.

## 2. Model Identity

- **P13O-F-001**: `model_id` is a stable semantic name assigned in the
  pre-training authorization record; never derived from metrics or
  results.
- **P13O-F-002**: `model_version` = the **full lowercase SHA-256 hex
  digest (64 characters) of the canonical frozen parameter artifact
  bytes** (canonicalization per P13O-F-016c) — content-addressed. The
  artifact hash IS identity; identity and hash are the same string —
  there is no separate "short" identity. Any byte change → new
  model_version (new artifact); one authorization binds exactly ONE
  version. Shortened display forms (e.g. 12-char prefixes) are
  explicitly NON-NORMATIVE and MUST NOT be used for identity, binding,
  lookup, eligibility, or governance.
- **P13O-F-003**: identity is immutable; retroactive identity changes of
  the frozen NOT-RECOVERABLE P13-O are forbidden.
- **P13O-F-004**: a git commit is provenance only, never identity. The
  committed `MODEL_APPLICATION_MANIFEST` binds artifact_sha256 ↔ all
  identity fields.

## 3. Variant Selection Authority

- **P13O-F-005**: the variant is decided by the **project owner** via
  explicit pre-training Human Authorization; the decision is recorded in
  that authorization BEFORE any fit executes.
- **P13O-F-006**: the decision is immutable after recording; runtime and
  training code must refuse any other variant. Automatic variant
  selection (best / latest / first / highest-metric / arbitrary) is
  forbidden at BOTH training time and apply time; the training entry
  point must assert the authorized variant and fail closed otherwise.
- **P13O-F-007**: train-multiple-variants-then-select is model selection
  and belongs ONLY to a research-comparison protocol; its output can
  never become the apply artifact. Selecting on validation results is
  leakage → BLOCKED.

## 4. Data Windows (pre-registered at authorization)

- **P13O-F-008**: three disjoint decision-date windows — training
  `[training_start, training_end)`, calibration `[calibration_start,
  calibration_end)`, validation `[validation_start, validation_end]` —
  with exact dates fixed in the authorization BEFORE training
  (pre-registration is the leakage guard; the contract fixes structure,
  the owner fixes dates).
- **P13O-F-009**: label availability — the label of decision day t is
  known at the next trading day close; rows whose label was not
  available by their window boundary are excluded.
- **P13O-F-010**: virgin zone (decision dates ≥ 2026-09-23) is excluded
  from ALL windows — never training, calibration, or validation data.
- **P13O-F-011**: `research_end = 2026-09-22`, `VIRGIN_START =
  2026-09-23` unchanged; P13-T STOPPED; P13-U PROTECTED.

## 5. Training Protocol

- **P13O-F-012**: proposed default, frozen VERBATIM at authorization as
  `training_protocol_id = "p13o-logistic-gd-500x0.05-v1"`: unregularized
  binary logistic; full-batch gradient descent; 500 epochs; lr 0.05;
  zero-init weights + scalar bias; float64; stable sigmoid (clip ±30);
  no scaler (raw factor values); rows sorted by (decision_time, symbol);
  one row per (symbol, decision_time); rows with any missing factor
  dropped deterministically. Same inputs → byte-identical artifact.
- **P13O-F-013**: the apply artifact is a **SINGLE FINAL MODEL** (one
  weight vector + bias fitted on the whole training window). Per-fold
  model collections are validation instruments and MUST NOT be mixed
  into forward apply.

## 6. Feature Contract

- **P13O-F-014**: `feature_set_id = "fs-" + sha256(canonical ordered
  [name, definition_version] list)`; the manifest stores the exact
  ordered feature names.
- **P13O-F-015**: feature_set_id / feature_order / preprocessing
  mismatch → `INELIGIBLE` — no auto-adjustment, no reordering.
- **P13O-F-016**: preprocessing is recorded explicitly (default:
  `"identity"`); a future preprocessing change is a new
  feature_set_id + new authorization.
- **P13O-F-016a (prediction semantics — normatively frozen)**: the NEW
  model's prediction semantics are frozen to exactly:
  `target = "next trading day close-up direction"`;
  `horizon = "next_trading_day"`;
  `positive_class = "next_return > 0"`. The manifest fields
  `target` / `horizon` / `positive_class` MUST equal these literals
  verbatim; any other value → `INELIGIBLE("prediction_semantics_mismatch")`.
  This is a normative invariant of the NEW artifact — historical P13-O
  metadata is NOT relied upon.
- **P13O-F-016b (scope — normative manifest field)**: `scope` is a
  REQUIRED manifest object: `{"universe_id": <string>, "symbols":
  [<sorted unique 6-char-zero-padded symbol strings>], "scope_sha256":
  <sha256 of the canonical scope JSON>}`. Canonicalization: symbols
  deduplicated, zero-padded to 6 characters, sorted ascending (the
  frozen-universe loader semantics); canonical scope JSON =
  `json.dumps({"symbols": symbols, "universe_id": universe_id},
  sort_keys=True, ensure_ascii=False, separators=(",", ":"))`;
  `universe_id` MUST equal the frozen
  `universe-d8c5016b1ded0984` for the current authorization lineage.
  Binding: the artifact is bound to this scope at freeze. Mismatch
  (scope_sha256, universe_id, or symbol not in `symbols`) →
  `INELIGIBLE("scope_mismatch")`. Forward selection (P13O-F-017)
  consumes exactly this field — no implicit scope exists.
- **P13O-F-016c (canonical artifact serialization)**: the frozen
  parameter artifact is a single JSON object serialized canonically:
  UTF-8, no BOM, no trailing newline; `json.dumps(..., sort_keys=True,
  ensure_ascii=False, separators=(",", ":"))` (lexicographic key order);
  floats are float64 serialized via shortest round-trip representation;
  negative zero is canonicalized to `0.0` before serialization; NaN and
  Infinity are forbidden (presence → generation failure). Artifact
  schema (parameters ONLY — execution metadata such as created_at/seed
  lives in the manifest, never in the artifact):
  `{"artifact_type": "MODEL_APPLICATION", "bias": <float>,
    "feature_names": [<exact ordered feature names>],
    "model_family": <string>, "weights": [<float, per feature_names
    order>]}`. The `weights` array is positional in `feature_names`
  order. Hash input = exactly these canonical bytes; there is no
  environment-dependent serialization. Determinism (G20) is executable:
  double-fit on the same authorized inputs → identical canonical bytes
  → identical SHA-256 → identical model_version.

## 7. Forward Model Selection (executable rule)

- **P13O-F-017**: with the single authorized artifact, eligible ⇔
  artifact hash matches manifest AND variant matches the authorization
  AND feature_set_id matches the packet AND prediction semantics match
  (P13O-F-016a) AND `manifest.training_end < as_of` (STRICT — label
  availability makes the model knowable only after training_end) AND
  `symbol ∈ manifest.scope.symbols` AND the resolved
  `manifest.scope` hash/universe_id match the authorized scope
  (P13O-F-016b). Exactly one artifact exists → selected; none eligible
  → `NOT_AVAILABLE`; more than one eligible → governance error, FAIL
  CLOSED. Every field consumed by this rule is normatively defined in
  P13O-F-016a/016b/022 — no implicit fields.

## 8. Calibration (new artifact; P13-Q NOT auto-reused)

- **P13O-F-018**: existing P13-Q (variant-pooled, binding unresolved)
  is NOT the future model's calibration. A NEW calibration artifact MUST
  be issued for the frozen model by the P13-Q-lineage successor under
  separate authorization.
- **P13O-F-019**: calibration method (default platt):
  `sigmoid(a + b·logit(p_raw))`, clip ±30; the artifact records a, b,
  logit domain, fit population (n + window), fit time boundary, and the
  binding tuple `{model_id, model_version, model_variant,
  feature_set_id}` — never a/b alone.
- **P13O-F-020**: leakage rules — the raw model MUST NOT have seen
  calibration rows; calibration MUST NOT be fitted on validation rows;
  variant selection MUST NOT use calibration results; threshold/policy
  selection MUST NOT use holdout. Every such path is BLOCKED.
- **P13O-F-021**: calibration binding mismatch (model/variant/
  feature_set) → `INELIGIBLE` (mirrors R4-D G12/G13/G14).

## 9. Manifest & Integrity

- **P13O-F-022**: `MODEL_APPLICATION_MANIFEST` = {artifact_type,
  artifact_id, artifact_sha256, model_id, model_version, model_family,
  variant, feature_set_id, feature_names (ordered), preprocessing,
  target, horizon, positive_class, training_start, training_end,
  research_end, training_protocol_id, seed, weights (ordered), bias,
  calibration_id, calibration_binding, provenance, source_commit,
  created_at (execution metadata only), freeze_status,
  scope (P13O-F-016b: {universe_id, symbols, scope_sha256})}.
  Non-applicable fields are explicit `null` — never omitted.
- **P13O-F-023**: integrity chain: artifact bytes → sha256 → manifest →
  manifest hash → committed evidence record (`docs/artifacts/`).
  `created_at` is execution metadata and NEVER part of research
  identity or determinism checks.
- **P13O-F-024**: hash mismatch → **FAIL CLOSED** (abort; no output, no
  regeneration, no retraining, no substitution). Determinism check:
  double-fit on the same window → byte-identical artifact (G20).

## 10. Boundaries of Existing Authorities

- **P13O-F-025**: P13-Q owns calibration research (its successor issues
  the new calibration artifact); P13-R owns policies (untouched; the
  future probability binds to a policy only via the R4-D contract);
  P14-D remains the sole PIT/selection authority (P13O-F-017 consumes
  as_of, it does not re-implement visibility); P14-E remains the sole
  evidence/provenance authority (the committed manifest evidence
  complements, never replaces, P14-E).

## 11. Golden / Anti-Cheat Cases (implementation-time, fixture-based)

**P13O-F-026**: G01 missing artifact → NOT_AVAILABLE · G02 artifact hash
mismatch → FAIL CLOSED · G03 model_id mismatch → INELIGIBLE · G04
model_version mismatch → INELIGIBLE · G05 variant mismatch → INELIGIBLE
· G06 feature_set mismatch → INELIGIBLE · G07 feature_order / prediction-semantics / scope mismatch →
INELIGIBLE · G08 preprocessing mismatch → INELIGIBLE · G09
training_end after as_of → INELIGIBLE(temporal) · G10 no eligible
forward model → NOT_AVAILABLE · G11 ambiguous eligible models → FAIL
CLOSED · G12 calibration bound to another model · G13 to another
variant · G14 to another feature_set · G15 P13-T/U data contamination
attempt → BLOCKED at entry (assert_research_zone) · G16 historical OOS
predictions supplied as model artifact → REJECTED · G17 missing weights
· G18 missing bias · G19 manifest/artifact inconsistency → FAIL CLOSED
· G20 non-deterministic generation → FAIL CLOSED (double-fit check).

## 12. R4-D Unblock Conditions

**P13O-F-027**: `R4-D APPLY = ELIGIBLE FOR AUTHORIZATION` requires ALL
of: C1 unique pre-registered variant · C2 frozen protocol · C3
deterministic artifact (double-run byte-identical) · C4 complete feature
binding · C5 model identity · C6 artifact sha256 · C7 forward selection
rule · C8 new calibration artifact · C9 calibration↔model binding ·
C10 provenance manifest · C11 independent artifact acceptance · C12
exact-head CI. Even then the final state is only `ELIGIBLE FOR
AUTHORIZATION` — **R4-D APPLY unlock additionally requires Human
Authorization**; never an automatic PASS.

## 13. Acceptance Checklist

[×] Identity scheme (F-001..004) · [×] Variant authority pre-registration
(F-005..007) · [×] Window structure + pre-registration (F-008..011) ·
[×] Frozen protocol + determinism (F-012/013) · [×] Feature contract
(F-014..016) · [×] Forward selection rule (F-017) · [×] Calibration
design + binding + leakage rules (F-018..021) · [×] Manifest schema
(F-022) · [×] Integrity chain + fail-closed (F-023/024) · [×] Authority
boundaries (F-025) · [×] Golden G01–G20 (F-026) · [×] R4-D unblock
conditions (F-027) · [×] P13-T/U protected · [×] No production code /
registry / R4-A/B/C / P14 change in this phase.
