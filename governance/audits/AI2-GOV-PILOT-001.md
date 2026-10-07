# AI2-GOV-PILOT-001 — Governance Consistency Audit

Status: CONFLICT
Owner: AI2
Executor: ZCODE-A2
Base Commit: 29403bc3a87fc8b885f9589dd265fe19fbdbf5b5
Branch: parallel/AI2/AI2-GOV-PILOT-001
HEAD SHA AUDITED: 5e1e29b84bcc0c7b0b4dfca0ca1388e71e94b773

## Scope
READ_SET was independently inspected in full:
- governance/PROTOCOL-v1.md
- governance/PARALLEL-GOVERNANCE-v2.md
- governance/TASK-TEMPLATE-v1.md
- governance/TASK-DEPENDENCY-SCHEMA-v2.md
- governance/TASK-STATE-MACHINE-v2.md
- governance/SHARED-INTERFACE-LOCK-v2.md
- governance/GOVERNANCE-GATES-v2.md
- governance/AI1-INTEGRATION-CONTROLLER-v2.md
- governance/INTEGRATION-AUDIT-v1.md

No finding below was repaired by this task.

## Findings

### 1. Authority ownership — PASS
AI1 is consistently identified as task allocator, dependency authority, integration authority, and final acceptor. AI2/AI3 are workers; ZCODE-A2/ZCODE-A3 are execution identities. No worker is granted final integration or acceptance authority.

### 2. Authorization / implementation / acceptance ordering — WARN
The intended order is AI1 allocation/dependency readiness -> worker execution -> READY_FOR_AUDIT -> AI1 auditing -> AI1 integration -> AI1 acceptance. Shared-interface changes additionally require AI1 authorization before modification.
However, authorization is not represented as a distinct state in TASK-STATE-MACHINE-v2. READY_TO_START means workspace prepared, while SHARED-INTERFACE-LOCK-v2 represents authorization only for shared interfaces. Ordinary task authorization and shared-interface authorization therefore lack one canonical gate/state.

### 3. State-machine consistency — WARN
TASK-STATE-MACHINE-v2 defines PLANNED, ALLOCATED, READY_TO_START, IN_PROGRESS, BLOCKED, READY_FOR_AUDIT, AUDITING, INTEGRATING, ACCEPTED, REJECTED, and ABORTED. TASK-TEMPLATE-v1 exposes only IN_PROGRESS, BLOCKED, READY_FOR_AUDIT, and REJECTED. The v1 task contract therefore cannot represent the complete v2 lifecycle without an unstated extension.

### 4. Task-template consistency — CONFLICT
TASK-TEMPLATE-v1 requires READ_SET/WRITE_SET/FORBIDDEN_SET plus free-form Acceptance Criteria and Deliverables. TASK-DEPENDENCY-SCHEMA-v2 requires task_id, agent, base_commit, depends_on, blocks, read_set, write_set, shared_interfaces, and structured acceptance.tests/gates. The v1 template has no explicit shared_interfaces field and no structured acceptance.tests/gates fields, while v2 omits forbidden_set. A task can therefore satisfy one contract while being structurally incomplete against the other.

### 5. Shared Interface Lock semantics — CONFLICT
SHARED-INTERFACE-LOCK-v2 defines UNLOCKED -> REQUESTED -> LOCKED -> AUDITING -> UNLOCKED, while PARALLEL-GOVERNANCE-v2 summarizes LOCKED -> authorized worker may modify -> audit -> UNLOCKED. The documents do not explicitly define the owner of REQUESTED -> LOCKED or AUDITING -> UNLOCKED. TASK-STATE-MACHINE-v2 reserves AUDITING to AI1, but that is a task-state rule, not an explicit lock-state transition rule. Lock acquisition, audit completion, and unlock are therefore not one unambiguous executable protocol.

### 6. AI1 final authority — PASS
v1, v2, GOVERNANCE-GATES-v2, AI1-INTEGRATION-CONTROLLER-v2, and INTEGRATION-AUDIT-v1 consistently reserve final integration and acceptance to AI1. Workers cannot self-accept, self-integrate, or clear another worker's BLOCKED/REJECTED state.

### 7. AI2 / AI3 / ZCODE role separation — PASS
AI2/ZCODE-A2 and AI3/ZCODE-A3 execute worker tasks; AI1 controls allocation, dependency resolution, audit, integration, and acceptance. No READ_SET document grants AI2/AI3 integration authority.

### 8. Forbidden-set enforcement — WARN
The v2 Scope Gate enforces changed_files against WRITE_SET and forbidden-file changes, but the v2 dependency schema does not require FORBIDDEN_SET as a first-class field. Enforcement therefore depends on a field present in v1 but absent from the v2 schema.
The task-local pattern governance/*.md is a direct-child pattern and does not cover governance/audits/*.md; this is consistent with the intended audit WRITE_SET but should be explicit rather than relying on glob interpretation.

### 9. Main / source-of-truth rules — PASS
v1 and v2 preserve worker branch isolation and prohibit direct main modification. v2 identifies /governance as the versioned governance source of truth and keeps runtime locks/task queues/ephemeral status local unless intentionally published. Integration remains AI1-only.

### 10. v1 / v2 semantic contradictions — CONFLICT
The strongest contradiction is structural:
- v1 TASK-TEMPLATE requires READ_SET/WRITE_SET/FORBIDDEN_SET and a limited worker-facing status vocabulary.
- v2 TASK-DEPENDENCY-SCHEMA requires shared_interfaces and structured acceptance gates but omits forbidden_set.
- v2 TASK-STATE-MACHINE defines a larger lifecycle that v1 TASK-TEMPLATE cannot represent.
- v1 describes READY_FOR_AI1_AUDIT -> AI1 integration -> independent acceptance, while v2 makes AUDITING and INTEGRATING explicit states. Intent is compatible, but the canonical task-status vocabulary is not.

These differences affect whether a task manifest is structurally valid and which state transitions can be represented.

## Gate Assessment
- Authority ownership: PASS
- Authorization / implementation / acceptance ordering: WARN
- State-machine consistency: WARN
- Task-template consistency: CONFLICT
- Shared Interface Lock semantics: CONFLICT
- AI1 final authority: PASS
- AI2/AI3/ZCODE role separation: PASS
- Forbidden-set enforcement: WARN
- Main/source-of-truth rules: PASS
- v1/v2 semantic consistency: CONFLICT

Overall audit result: **CONFLICT**

## Scope / Change Audit
At the audited HEAD, the branch was exactly 1 commit ahead of BASE_COMMIT and that commit added only:
- governance/audits/AI2-GOV-PILOT-001.md

No READ_SET file, forbidden implementation area, main branch, or AI3 branch was modified by this task.

## Task Completion
Audit performed against exact audited HEAD:
5e1e29b84bcc0c7b0b4dfca0ca1388e71e94b773

Final task status: CONFLICT

No repair, authorization, merge, or acceptance action was performed. DONE is not acceptance; final acceptance remains AI1-only.

---

## Re-execution Verification (2026-10-07, second AI2 executor run)

A second independent AI2 execution re-inspected the governance corpus and
verified every finding above in place, without repairing any of them.

### READ_SET coverage correction
The original report lists 9 READ_SET files. The governance corpus at
BASE_COMMIT contains 12 rule files. This run inspected all 12 independently;
the three additional files confirm the original conclusions and add no
contradiction:

- governance/WORKTREE-BRANCH-RULES-v1.md — "Never share a working directory
  between agents", branch naming, and the single approved BASE_COMMIT
  lifecycle are consistent with PROTOCOL-v1 and PARALLEL-GOVERNANCE-v2.
  Both pilot branches start from 29403bc, satisfying this rule.
- governance/ZCODE-A2-PROMPT-v1.md / governance/ZCODE-A3-PROMPT-v1.md —
  worker role separation (dimension 7) re-confirmed from the role
  definitions themselves.
- Self-compliance note (minor, observed): commits on this branch use
  conventional messages ("governance: ...", "audit: ...") instead of the
  required `[AI2][<TASK-ID>] <short description>` format from
  ZCODE-A2-PROMPT-v1. Recorded here; not repaired.

### Corrected finding 5 — Shared Interface Lock semantics: CONFLICT -> WARN
The original text states the owner of REQUESTED -> LOCKED is not explicitly
defined. That half is incorrect: SHARED-INTERFACE-LOCK-v2 states
"AI1 grants or rejects the lock.", which explicitly assigns lock granting
(REQUESTED -> LOCKED) to AI1. The remaining gaps are real but are
underspecification, not contradiction:

- the lifecycle line does not draw the rejection edge (REQUESTED -> UNLOCKED);
- the owner of AUDITING -> UNLOCKED is undefined (TASK-STATE-MACHINE-v2
  reserves the task state AUDITING to AI1, but that is a task-state rule,
  not a lock-state rule);
- PARALLEL-GOVERNANCE-v2 §3 summarizes the lifecycle without REQUESTED —
  a compatible shorthand, not a contradiction.

Dimension 5 is downgraded to WARN on this basis.

### Corrected Gate Assessment
- Authority ownership: PASS
- Authorization / implementation / acceptance ordering: WARN
- State-machine consistency: WARN
- Task-template consistency: CONFLICT
- Shared Interface Lock semantics: WARN (downgraded from CONFLICT)
- AI1 final authority: PASS
- AI2/AI3/ZCODE role separation: PASS
- Forbidden-set enforcement: WARN
- Main/source-of-truth rules: PASS
- v1/v2 semantic consistency: CONFLICT

Overall audit result remains: **CONFLICT**. Dimensions 4 and 10 are genuine
structural contradictions (v1 template requires FORBIDDEN_SET and a
4-vocabulary status line, v2 schema requires shared_interfaces and
structured acceptance while omitting forbidden_set; 4-state vs 11-state
lifecycle vocabulary), so the downgrade of dimension 5 does not change the
overall result.

### Scope / CI facts at final HEAD
- Final branch HEAD:
  fe8fca66fbef6eeb3fef638e1e572d7a44216b5b — 2 commits ahead of BASE_COMMIT
  29403bc3a87fc8b885f9589dd265fe19fbdbf5b5; both commits touch only
  governance/audits/AI2-GOV-PILOT-001.md. The original "exactly 1 commit
  ahead" statement was accurate at its audited HEAD
  5e1e29b84bcc0c7b0b4dfca0ca1388e71e94b773 and is superseded by this pin.
- CI: no workflow runs exist for this branch HEAD. tests.yml at BASE_COMMIT
  triggers only on push/pull_request to main, so worker-branch pushes do not
  invoke CI; governance-gate.yml was added to main after BASE_COMMIT and is
  absent on this branch.
- No file outside governance/audits/AI2-GOV-PILOT-001.md was modified, no
  finding was repaired, nothing was merged, and acceptance remains AI1-only.
