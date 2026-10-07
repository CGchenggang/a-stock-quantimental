# P14-F Design Contract — Research-Only Feature Registry & Information-to-Research Integration

> STATUS: DRAFT — P14-F-DESIGN-001 — awaiting independent Contract acceptance.
> **P14-F Implementation is NOT AUTHORIZED** until this contract passes
> independent Contract acceptance AND the project owner grants a
> P14-F-APPLY-HUMAN-AUTHORIZATION record.
>
> 修订历史：
> v1: 初稿（P14-F DESIGN CONTRACT + ACCEPTANCE MATRIX design gate，
>     2026-10-07；审计基线 Exact HEAD `45ce0c4`；前置事实：
>     P14-F Readiness / Gap Audit = PASS / INDEPENDENTLY ACCEPTED
>     （Lead Agent 验收记录 commit `5aa37c9`），其 gap 清单是本
>     契约的输入。规范不变量 P14F2-001..024（"F2" 区分于 forward-model
>     契约的 P13O-F-* 系列）。
> v2: NARROW REPAIR — FEATURE AUTHORITY CLOSURE（2026-10-07）——独立
>     验收发现 P14F2-001 的 "sole feature-definition authority" 与
>     forward_model.py::FROZEN_FEATURE_NAMES（apply_path.py E4 的实际
>     判据，且两文件在实施阶段 forbidden）构成 authority contradiction。
>     修复 = 采纳分层权威模型（方案 B）：P14F2-001 重写为 Research
>     Feature Definition Authority；新增 P14F2-001a 三角色 authority
>     model + binding closure 链；P14F2-019 重写为双向闭合 integrity
>     chain（registry_sha256 存 evidence；authoritative binding = 冻结
>     MODEL_APPLICATION 的 feature_set_id；derived id 交叉验证；双向
>     FAIL CLOSED；frozen set 变化 = 新模型新授权）。文档-only。

---

## 1. Purpose & Scope

### 1.1 What P14-F solves

P14-F establishes the **research-only feature registry** — the formal,
versioned, hash-anchored authority that binds feature NAMES to their
computation identity — and uses it to extend the R4-A research packet
to the full calibrated 6-factor feature set, so that the R4-D resolver's
E4 feature-set gate can transition from the current honest
`INELIGIBLE(feature_set_mismatch)` to a reachable `CALIBRATED` path.

### 1.2 What P14-F does NOT solve (Non-Scope)

- No new factor research, no new factor computation logic (definitions
  are REFERENCED from the frozen implementation blobs, never rewritten).
- No policy, threshold, or calibration change; no registry promotion of
  any P13-Q/P13-R research decision.
- No production promotion of any kind; no P14-G (agent-facing interface);
  no holdout evaluation; no P13-T execution.
- No modification of the frozen MODEL_APPLICATION / CALIBRATION
  artifacts, of the accepted P14-A..E authority surfaces, or of the
  R4-B/C batch/validation semantics.

### 1.3 Boundaries with existing phases

| Phase | Boundary |
|---|---|
| R4-A | The packet assembly point is the ONLY authorized integration surface (mirroring R4D-014); R4-A's factor computation code is referenced, not redesigned |
| R4-D | The resolver is the sole consumer of the registry-derived `feature_set_id`; its E4 gate semantics are untouched — the registry makes the gate PASSABLE, not weaker |
| P14-A..E | Authority surfaces unchanged; P14-D remains the sole PIT/selection authority; P14-E the sole evidence/provenance authority |
| P13-Q/P13-R | Registries remain READ-ONLY research records; the P14-F registry is a NEW authority, not a rewrite of them |
| P13-U | The virgin boundary is inherited verbatim; the registry records no decision dates and can never relax the guard |

## 2. Research-Only Feature Registry (schema, P14F2-001..008)

**P14F2-001 (registry artifact)**: a single committed JSON document
`docs/contracts/p14f/FEATURE_REGISTRY.json` (canonical serialization
per P13O-F-016c semantics: UTF-8, no BOM, no trailing newline,
sort_keys, compact separators). It is the **Research Feature Definition
Authority** — the only authority that defines HOW a feature is computed
(definition_version, computation identity, source lineage). It is NOT
the authority for frozen-model identity: the frozen MODEL_APPLICATION
carries its own immutable feature identity (P14F2-001a), and the two
are cross-validated against a single shared feature_set_id (P14F2-019)
rather than one superseding the other.

**P14F2-001a (authority model — three distinct roles, one identity)**:

| role | holder | answers | mutable? |
|---|---|---|---|
| Research Feature **Definition** Authority | `FEATURE_REGISTRY.json` (P14F2-002) | "HOW is each feature computed, from which lineage, at which definition_version?" | via governance commit pair (P14F2-009) |
| Frozen MODEL_APPLICATION **Identity** Boundary | the committed frozen artifact bytes + `forward_model.py::FROZEN_FEATURE_NAMES` (a projection of the artifact's own `feature_names`, which are part of its content-addressed identity) | "WHICH feature vector is the frozen model bound to?" | never (any byte change = new model_version / new authorization) |
| Runtime **Eligibility** | `apply_path.py` E4 gate | "does THIS packet match the bound feature set?" | no (gate semantics fixed; it compares against the bound set) |

Why `FROZEN_FEATURE_NAMES` is NOT a second feature-definition
authority: (a) it carries no computation identity and no
definition_version — it answers nothing about HOW a feature is
computed; (b) it never evolves — it is a projection of the frozen
artifact's own `feature_names` field, which is part of the
content-addressed model identity; (c) its correctness is not
self-asserted — it is cross-validated against the registry-derived
feature_set_id (P14F2-019). It is frozen-model identity evidence, and
the registry is the definition authority: two roles, one shared
feature_set_id, zero competing truth.

**Binding closure (the required chain)**:

```text
Feature Definition (registry, P14F2-002)
        ↓ (ordered per P14F2-007)
Feature Registry ordered set
        ↓ feature_set_id = "fs-" + SHA256(canonical ordered list)
derived feature_set_id
        ↓ MUST EQUAL (cross-validation, P14F2-019)
Frozen MODEL_APPLICATION feature_set_id (fs-d1f3bdca…3afe)
        ↓ consumed by
R4-A packet (six-factor, P14F2-011)
        ↓ gate
R4-D E4 eligibility check (apply_path.py, unchanged)
```

A future implementation that derives the feature set from the registry
and recomputes the id MUST obtain exactly the frozen id; if it does
not, the mismatch is FAIL CLOSED on BOTH sides (the registry loader
refuses to reference a set that does not match the frozen binding, and
the resolver E4 gate rejects any packet that does not match it) — the
repair is a governance act (new definitions / new model authorization),
never a runtime adjustment.

**P14F2-002 (feature definition record)**: each entry is

```json
{
  "name": "<canonical feature name>",
  "definition_version": "<path>@<git blob sha>",
  "computation_identity": {
      "source_file": "<repo path of the defining implementation>",
      "entry_symbol": "<function/builder that computes it>",
      "parameters": {<deterministic parameter map, e.g. lookback>}
  },
  "source_lineage": ["<upstream data source ids, e.g. cn_stock_quote>",
                     "<e.g. sw_official_sw1_membership lineage>"],
  "semantics": "<one-line frozen description>",
  "pit_authority": "P14-D (available_time <= as_of) via local_pipeline decision-time visibility",
  "implementation_identity": "<git blob sha of the defining source file>",
  "ordering_hint": <int — see P14F2-007>
}
```

**P14F2-003 (definition_version)**: `<defining source file path>@<git
blob sha of that file>` — the convention already frozen in the P13-O
Human Authorization Record. The version changes WHENEVER the defining
file's blob changes (any byte change to the computation). Verifiable by
`git cat-file` at any HEAD.

**P14F2-004 (feature identity — when are two features the same)**: two
features are THE SAME feature iff name, definition_version, and
computation_identity are all equal. Same name with a different blob =
a DIFFERENT feature (new definition_version required).

**P14F2-005 (definition_version bump rule)**: any change to the
defining implementation file's content → new blob → new
definition_version → a NEW registry entry (the old entry may remain as
history but the feature_set referencing it changes identity per
P14F2-006). Definitions MUST NOT be hand-written version strings —
they are derived from `git ls-tree` at the implementation HEAD.

## 3. Feature-Set Identity (P14F2-006..009)

**P14F2-006 (feature_set_id)**: for an ORDERED list of feature
definitions,

```text
feature_set_id = "fs-" + SHA256(canonical_json([
    [name_1, definition_version_1], ..., [name_n, definition_version_n]
]))
```

— the exact algorithm already frozen in the R4-D apply-path lineage
(the authorized fs-d1f3bdca…3afe was computed this way). Registry
content and feature_set_id are bound by construction: a registry change
that alters any (name, definition_version) pair or the order CHANGES
the feature_set_id. "Registry content changed but feature_set_id
unchanged" is structurally impossible and is additionally detected by
golden check (recompute at load).

**P14F2-007 (ordering)**: the feature set is ORDERED; the order is the
weight-vector order of the consuming MODEL_APPLICATION. The initial
authorized order (matching the frozen model and the P13-Q calibrated
lineage):

```text
1. momentum
2. volatility
3. trend
4. volume_ratio
5. industry_relative_return_5
6. industry_relative_return_20
```

Order drift = a different feature_set_id (never a silent reorder).

**P14F2-008 (no runtime selection)**: feature sets are NOT chosen at
runtime (no best/latest/first/arbitrary). The consuming packet targets
exactly ONE registry feature set, identified by its feature_set_id,
which must match the binding expected by the R4-D resolver.

**P14F2-009 (registry evolution)**:

- The registry file is READ-ONLY in normal operation; adding a new
  definition_version or a new feature requires a governance commit
  (docs-only for the registry + code commit for any new consuming
  implementation) AND — when it changes a feature set bound to a frozen
  model — a NEW MODEL_APPLICATION lineage (new model authorization),
  never an in-place edit.
- The frozen R4-D model's feature set (`fs-d1f3bdca…3afe`) is
  PERMANENTLY BOUND to model_version `97602f4d…664`: the registry may
  add new entries, but that feature_set_id and its binding never
  change. Changing a frozen model's feature definition = a new model /
  new authorization boundary, not a registry edit.

## 4. Initial Registry Content (ratification target, P14F2-010)

The initial registry contains exactly the 6 calibrated features, whose
definition_versions are already frozen in the P13-O Human Authorization
Record (blob-verified at multiple HEADs):

| # | name | implementation_identity (blob) | source_file |
|---|---|---|---|
| 1 | momentum | `0582f91ef406d329c7ce3d7460db8f467c20ef75` | src/astock_v2/local_pipeline.py |
| 2 | volatility | `0582f91ef406d329c7ce3d7460db8f467c20ef75` | src/astock_v2/local_pipeline.py |
| 3 | trend | `0582f91ef406d329c7ce3d7460db8f467c20ef75` | src/astock_v2/local_pipeline.py |
| 4 | volume_ratio | `0582f91ef406d329c7ce3d7460db8f467c20ef75` | src/astock_v2/local_pipeline.py |
| 5 | industry_relative_return_5 | `0b6c0f140fad636a50cee67d2502d6ce27adc5cb` | scripts/run_local_industry_relative_oos.py |
| 6 | industry_relative_return_20 | `0b6c0f140fad636a50cee67d2502d6ce27adc5cb` | scripts/run_local_industry_relative_oos.py |

The resulting feature_set_id MUST recompute to
`fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe`
(exact match with the R4-D binding; mismatch = STOP).

## 5. R4-A Packet Interface (P14F2-011..015)

**P14F2-011 (six-factor packet requirement)**: for the R4-D resolver to
return `CALIBRATED`, the packet must present factor values for exactly
the 6 registered features, in the registry order, with each value
computed by the registered implementation (identity verifiable by
blob) from PIT-visible inputs.

**P14F2-012 (assembly source)**: the two industry-relative features are
assembled via the accepted
`build_universe_industry_relative_context_maps` + `_factor_rows`
machinery (the same blob-frozen definitions used by the authorized
training executor and the R4-C validation loop); the 4 stock factors
via `build_local_factor_rows`. No new computation is authorized.

**P14F2-013 (missing feature behavior)**: a (symbol, decision_date)
observation missing any registered feature value is DROPPED
deterministically (whole-row, matching the frozen training protocol) —
never imputed, never partially packeted. Drops are counted and visible
in the run result (no silent shrinkage of the universe).

**P14F2-014 (mismatch behavior)**: a packet whose feature set differs
from the registry set is rejected by the R4-D resolver E4 gate
(`feature_set_mismatch`) — the registry does not weaken the gate, and
approximation/fallback/partial-substitution are forbidden (R4D-010
inheritance).

**P14F2-015 (determinism & replay)**: packet assembly is deterministic
(sorted by (decision_time, symbol); one row per (symbol, decision_time));
identical inputs → identical packet → identical resolver block →
identical ledger provenance (R4-A/R4-B replay properties inherited).

## 6. PIT / Protected Boundary (P14F2-016..018)

**P14F2-016**: the boundaries are inherited verbatim:
`research_end = 2026-09-22`, `virgin_start = 2026-09-23`, universe =
`universe-d8c5016b1ded0984`. No registry entry, no feature definition,
and no packet row may reference decision dates ≥ 2026-09-23.

**P14F2-017**: holdout/virgin data MUST NOT participate in feature
definition discovery, registry content, calibration, or policy
decisions. The registry records no decision dates by design.

**P14F2-018**: the P13-U guard (`assert_research_zone`) remains the
sole protection mechanism; the registry does not wrap, replace, or
relax it. P14-D remains the sole PIT/selection authority; P14-E the
sole evidence/provenance authority (registry evidence complements,
never replaces).

## 7. Registry Immutability & Integrity (P14F2-019..020)

**P14F2-019 (integrity chain & dual-binding closure)**:

- `registry_sha256` is stored in the committed P14-F evidence record
  (`docs/artifacts/P14-F-REGISTRY-EVIDENCE.md`) and re-verified by the
  registry loader at every use; the registry bytes are never trusted
  without the hash check.
- The **authoritative binding** for runtime eligibility is the frozen
  MODEL_APPLICATION's `feature_set_id` (`fs-d1f3bdca…3afe`) — the
  identity boundary, immutable per P14F2-001a.
- The **derived feature_set_id** is computed from the registry's
  ordered `[name, definition_version]` list at load time.
- **Cross-validation**: derived feature_set_id MUST equal the frozen
  MODEL_APPLICATION's feature_set_id at every load and at every packet
  assembly. Both sides FAIL CLOSED on mismatch: the registry loader
  refuses to serve a set whose derived id does not match the frozen
  binding, and the R4-D E4 gate rejects any packet that does not carry
  the bound set. The mismatch is a governance error — the repair is new
  definitions and/or a new model authorization (P14F2-009), never a
  runtime adjustment.
- The runtime NEVER modifies the registry.
- The registry MAY add new entries or new definition_versions without
  changing the frozen set (the frozen set is the specific ordered
  subset referenced by `fs-d1f3bdca…3afe`; additions that do not alter
  that subset's ordered content leave the binding untouched).
- Any change to a member of the frozen set (name, definition_version,
  or order) CHANGES the derived feature_set_id, which detaches it from
  the frozen model binding — therefore a frozen-set change REQUIRES a
  new MODEL_APPLICATION lineage under a new Human Authorization (the
  frozen model cannot consume a set it was not trained against).

**P14F2-020**: the registry is never regenerated at runtime; a registry
governance change is a docs+code commit pair with exact-head CI and,
when it affects a frozen binding, a new authorization.

## 8. Recommended Allowed Implementation Files (future phase)

- `docs/contracts/p14f/FEATURE_REGISTRY.json` (the registry itself)
- `src/astock_v2/features/registry.py` (load/verify/feature_set_id — new module)
- `src/astock_v2/agent/research_run.py` (packet extension to 6 factors via the frozen assemblies — the R4D-014 integration surface)
- `tests/test_p14f_feature_registry.py` + golden/harness additions
- `docs/artifacts/P14-F-REGISTRY-EVIDENCE.md`
- `docs/PROJECT_STATUS.md` (minimal sync)

Forbidden at implementation: `src/astock_v2/information/pit.py`,
`research_query.py`, `evidence.py`, `apply_path.py` semantics (the
resolver consumes the registry without semantic change),
`src/astock_v2/model/forward_model.py` constants, frozen artifacts,
registries, CI workflow, P13-T/U.

## 9. Golden Checks (implementation-time, P14F2-021..024)

- GF-01 registry loads; schema valid; ids recompute (fail closed on
  mismatch).
- GF-02 feature_set_id == fs-d1f3bdca…3afe for the initial set.
- GF-03 definition blob exists at HEAD (`git cat-file`) for every entry.
- GF-04 packet assembly yields exactly 6 features in registry order.
- GF-05 missing-feature row drop is deterministic and counted.
- GF-06 resolver E4 accepts the registry-derived set (CALIBRATED path
  reachable with the frozen model on the research_end day, numeric
  golden vs the platt formula).
- GF-07 any registry byte change → feature_set_id change detected.
- GF-08 registry/protected-boundary immutability across a full research
  run (digests unchanged; no virgin dates in any assembled row).

## 10. Out of Scope (this contract)

New factor computation, production promotion, P14-G, policy/threshold/
calibration changes, P13-Q/P13-R registry writes, holdout evaluation,
P13-T execution, performance claims.
