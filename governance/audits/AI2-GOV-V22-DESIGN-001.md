# AI2-GOV-V22-DESIGN-001 — v2.2 Governance Reconciliation Design

## Status
**DESIGN COMPLETE / READY_FOR_AI1_AUDIT**

Base: `e33b649189af17547c73a2e131f808c08baa62ed`

This task is design-only. No governance rule, executable gate, workflow, schema, manifest, or task state is modified by this task.

## 1. Confirmed baseline
- v1 requires READ_SET, WRITE_SET and FORBIDDEN_SET and makes AI1 the final authority.
- v2 defines the 11-state machine, dependency graph, Shared Interface Lock, Scope/Conflict/Test/Integration gates.
- `TASK-DEPENDENCY-SCHEMA-v2.md` omits `forbidden_set`, while `.agent/task-template.json` and the executable gate require it.
- v2.1 already treats FORBIDDEN_SET as mandatory and fail-closed.
- Shared Interface Lock documents only the main lifecycle; rejection/withdrawal and rework transitions are not explicit.
- Current canonical state vocabulary has 11 states and no AUTHORIZED state.

## 2. Canonical v2.2 task contract
Proposed machine contract:
```yaml
task_id:
agent:
zcode_agent:
base_commit:
depends_on: []
blocks: []
read_set: []
write_set: []
forbidden_set: []
shared_interfaces: []
authorization:
  human_required: false
  human_authorization_ref: null
acceptance:
  tests: []
  gates: [scope, conflict, test]
status:
```
`forbidden_set` is first-class and may be empty. Manifests instantiate the contract and cannot redefine governance rules. Authorization evidence is metadata, not a new state.

## 3. FORBIDDEN_SET semantics
**Deny-wins:** a forbidden match is a hard failure even when WRITE_SET also matches.

Pattern language:
- exact path: `foo/bar.py`
- direct child wildcard: `foo/*.py`
- recursive subtree: `foo/**`

Do not silently inherit generic fnmatch directory-crossing behavior. The PR-local manifest is exempt only for its exact own path; no other file receives that exemption.

## 4. State and authorization
Canonical states remain exactly:
`PLANNED, ALLOCATED, READY_TO_START, IN_PROGRESS, BLOCKED, READY_FOR_AUDIT, AUDITING, INTEGRATING, ACCEPTED, REJECTED, ABORTED`.

Do **not** add AUTHORIZED. READY_TO_START requires:
1. frozen manifest;
2. AI1 allocation/authorization;
3. Human Authorization evidence when `human_required=true`.

Legacy `READY_FOR_AI1_AUDIT` may be a migration alias and should eventually be retired.

## 5. Shared Interface Lock v2.2 FSM
Normative transitions:
- UNLOCKED -> REQUESTED: worker requests.
- REQUESTED -> LOCKED: AI1 approves and assigns exclusive owner.
- REQUESTED -> UNLOCKED: AI1 rejects or worker withdraws.
- LOCKED -> AUDITING: AI1 starts audit after worker completion.
- AUDITING -> UNLOCKED: AI1 accepts.
- AUDITING -> LOCKED: AI1 rejects/requires rework; authorized owner retains lock.

Ownership: requester owns only the request; AI1 controls LOCKED/AUDITING authority. Workers never acquire a lock by editing first.

## 6. Authority precedence
1. v1 constitutional/core principles.
2. Explicit v2 rules govern where v2 specifies the mechanism.
3. Where v2 is silent, v1 remains authoritative.
4. v2.1 executable enforcement binds mechanical behavior; divergence is a governance defect.
5. Manifests are instances, not rules.
6. Unresolved conflicts BLOCK AI1 acceptance.

## 7. Migration
Phase 0: analysis only (current task + AI3 gate design).
Phase 1: additive v2.2 reconciliation addendum — Human Authorization required.
Phase 2: executable gate/workflow alignment — separate Human Authorization required.
Phase 3: optional consolidation of frozen v1/v2 wording — separately authorized.

Existing v2.1 manifests remain reviewable; new manifests use the ratified canonical contract. Legacy compatibility must not weaken the executable gate.

## 8. Protected boundaries and FORBIDDEN_SET relationship
The **Always-Protected Boundary** and task-level **FORBIDDEN_SET** are separate governance layers and MUST NOT be modeled as competing patterns inside the same deny-wins mechanism.

### 8.1 Always-Protected Boundary
The Always-Protected Boundary is a higher-level authorization boundary for paths such as:
- `governance/**`
- `.github/workflows/**`
- `.agent/**`
- executable governance scripts
- AI1-designated production schema/config authorities

By default, ordinary worker tasks cannot modify these paths. A task's WRITE_SET MUST NOT be interpreted as an implicit exception to an Always-Protected Boundary.

### 8.2 FORBIDDEN_SET
FORBIDDEN_SET remains a task-local mechanical deny list. Its rule is strictly **deny-wins**:
> If a changed path matches FORBIDDEN_SET, the Scope Gate fails even if the same path also matches WRITE_SET.

Therefore, WRITE_SET never overrides FORBIDDEN_SET.

### 8.3 Authorized exceptions
A governance task that is explicitly authorized to modify an Always-Protected Boundary does **not** obtain that authority by putting the protected path into WRITE_SET while leaving it in FORBIDDEN_SET.

Instead, the v2.2 contract MUST carry an explicit authorization-level exception for the protected boundary. That exception:
1. is granted by the required Human Authorization and AI1 authorization;
2. is evaluated at the authorization/policy layer before task-level scope evaluation;
3. permits the authorized path to become eligible for WRITE_SET evaluation;
4. does not weaken deny-wins for any other FORBIDDEN_SET match.

Thus:
**Always-Protected Boundary → authorization eligibility → WRITE_SET / FORBIDDEN_SET mechanical evaluation.**

The exception mechanism is a v2.2 design requirement; it is NOT implied to exist in the current v2.1 executable gate.

### 8.4 Normative precedence
For a changed path:
1. Check whether the path is inside an Always-Protected Boundary.
2. If protected and no explicit authorized exception exists: **FAIL CLOSED**.
3. If an authorized exception exists, evaluate the task's WRITE_SET and FORBIDDEN_SET normally.
4. If FORBIDDEN_SET matches: **FAIL CLOSED**, regardless of WRITE_SET.
5. Otherwise, if WRITE_SET does not match: **FAIL CLOSED**.
6. Otherwise: Scope Gate may pass for that path.

This removes the previous internal contradiction: an authorized governance task does not override deny-wins; authorization changes whether the protected boundary is eligible for evaluation, while FORBIDDEN_SET deny-wins remains absolute within the task-level scope gate.

## 9. READ_SET and gates
READ_SET declares required audit/input evidence and grants no write authority. Missing required evidence is an audit finding.
Scope Gate = mechanical scope/forbidden checks.
Conflict Gate = AI1 semantic overlap/shared-interface/runtime coupling.
Test Gate = required tests/evidence.
AI1 Integration Gate = cross-task audit and final acceptance.
Passing tests/CI/commit/READY never constitutes Human Authorization or final acceptance.

## 10. Human Authorization required for
- ratifying v2.2;
- changing frozen governance rules or precedence;
- changing executable gate semantics/workflow;
- changing task classes requiring human authorization;
- optional frozen-spec consolidation.

No authorization is implied by this report.

## 11. Open decisions for AI1/Human
1. Exact v2.2 addendum filename/versioning.
2. Exact always-protected boundary list.
3. Exact machine-readable authorization-exception representation for Always-Protected Boundaries.
4. Whether legacy manifest compatibility is time-bounded or version-tagged.
5. Whether `zcode_agent` is mandatory for all governed tasks or only ZCODE-backed tasks.

## Acceptance
**READY_FOR_AI1_AUDIT. No implementation authorization granted.**
