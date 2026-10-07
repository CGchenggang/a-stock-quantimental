# AI2-GOV-V22-DESIGN-001 — v2.2 Governance Reconciliation Design

## 1. Execution status

**DESIGN COMPLETE / READY_FOR_AI1_AUDIT**

This artifact is design-only. No governance rule, executable gate, workflow, schema, manifest, or task state was modified by this task.

Base: `e33b649189af17547c73a2e131f808c08baa62ed`

## 2. Confirmed baseline facts

1. v1 defines AI1 as allocator/integrator/final acceptor and requires READ_SET, WRITE_SET, FORBIDDEN_SET.
2. v2 defines the 11-state task machine, dependency graph, Shared Interface Lock, Scope/Conflict/Test/Integration/GitHub gates.
3. `TASK-DEPENDENCY-SCHEMA-v2.md` currently omits `forbidden_set`, while `.agent/task-template.json` and `scripts/governance_gate.py` require it.
4. v2.1 execution guidance already treats FORBIDDEN_SET as mandatory and fail-closed.
5. Current Shared Interface Lock documents only the main lifecycle `UNLOCKED -> REQUESTED -> LOCKED -> AUDITING -> UNLOCKED`; rejection/withdrawal and rework transitions are implicit rather than normative.
6. Current state vocabulary contains 11 states and no explicit AUTHORIZED state.

## 3. Canonical v2.2 task contract

The machine-readable canonical contract should be:

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

Rules:
- `forbidden_set` is first-class and may be empty.
- `zcode_agent` identifies the execution actor when applicable; it does not gain authority.
- Authorization evidence is metadata/evidence, not a new task state.
- `status` uses the canonical 11-state vocabulary.
- Manifests instantiate the contract; they do not redefine governance rules.

## 4. FORBIDDEN_SET semantics

**Deny-wins.** A changed path matching FORBIDDEN_SET is a hard scope failure even if it also matches WRITE_SET. There is no write-set precedence.

Pattern language is intentionally minimal:
- exact path: `foo/bar.py`
- direct children: `foo/*.py`
- recursive subtree: `foo/**`

The semantics of `*` are direct-child matching for governance purposes; `/**` is the explicit recursive operator. The implementation must not silently depend on Python `fnmatch` semantics where a broad pattern can unexpectedly cross directory boundaries.

The PR-local manifest is mechanically exempt from its own WRITE_SET/FORBIDDEN_SET evaluation only for the manifest file itself. This does not exempt any other file.

## 5. State vocabulary and authorization

Canonical states remain exactly:

`PLANNED, ALLOCATED, READY_TO_START, IN_PROGRESS, BLOCKED, READY_FOR_AUDIT, AUDITING, INTEGRATING, ACCEPTED, REJECTED, ABORTED`.

Do not add an AUTHORIZED state.

A task may enter `READY_TO_START` only when the following evidence is present:
1. frozen manifest;
2. AI1 allocation/authorization;
3. Human Authorization evidence when `human_required=true`.

A worker may report `READY_FOR_AUDIT`; only AI1 may enter `AUDITING`, `INTEGRATING`, or `ACCEPTED`.

Legacy labels such as `READY_FOR_AI1_AUDIT` should be treated as aliases during migration and retired after the v2.2 transition period.

## 6. Shared Interface Lock v2.2 FSM

Normative transitions:

- `UNLOCKED -> REQUESTED`: worker requests a change.
- `REQUESTED -> LOCKED`: AI1 approves and assigns ownership.
- `REQUESTED -> UNLOCKED`: AI1 rejects or worker withdraws request.
- `LOCKED -> AUDITING`: AI1 begins audit after worker reports completion.
- `AUDITING -> UNLOCKED`: AI1 accepts the interface change.
- `AUDITING -> LOCKED`: AI1 rejects/requires rework; same authorized owner retains the lock.

Ownership:
- REQUESTED: requester owns the request, not the interface.
- LOCKED: AI1 grants exclusive modification authority to the named worker.
- AUDITING: AI1 owns the audit decision.
- UNLOCKED: no worker has modification authority.

Workers never acquire a lock by editing first.

## 7. Authority precedence

The v2.2 corpus should establish this precedence:

1. v1 constitutional/core governance principles.
2. Explicit v2 rules govern where v2 intentionally specifies the mechanism.
3. Where v2 is silent, v1 remains authoritative.
4. v2.1 executable enforcement binds mechanical behavior; any divergence from the normative contract is a governance defect, not a new rule.
5. Task manifests are instances of the contract and cannot override it.
6. Unresolved conflict blocks AI1 acceptance.

## 8. Migration path

**Phase 0 — analysis:** this task and AI3 gate design; no implementation.

**Phase 1 — additive addendum:** Human Authorization required. Add a v2.2 reconciliation addendum without deleting frozen v1/v2 material.

**Phase 2 — executable alignment:** separate Human Authorization required. Align gate/workflow with the ratified addendum.

**Phase 3 — optional consolidation:** separately authorized cleanup of v1/v2 frozen wording; never bundled implicitly with Phase 1/2.

Existing valid v2.1 manifests should remain reviewable. New manifests use the canonical v2.2 fields. During migration, absence of `forbidden_set` is a schema-version compatibility issue, not permission to weaken the executable gate.

## 9. Always-protected boundaries

At minimum, governance implementation should remain protected from ordinary worker scope:
- `governance/**`
- `.github/workflows/**`
- `.agent/**`
- executable governance scripts
- production-critical schema/config authorities identified by AI1

A task explicitly authorized to modify one of these boundaries must declare it in WRITE_SET and receive the required AI1/Human Authorization; deny-wins still applies to all other forbidden paths.

## 10. READ_SET and acceptance semantics

READ_SET is an audit/input contract:
- it declares authoritative files the worker is expected to inspect;
- it does not grant modification authority;
- missing or inaccessible required READ_SET evidence is an audit finding.

Acceptance gates remain mechanical/semantic layers:
- Scope Gate: file scope and forbidden checks.
- Conflict Gate: semantic overlap/shared-interface/runtime coupling.
- Test Gate: required tests/evidence.
- AI1 Integration Gate: cross-task audit and final acceptance.

Passing mechanical gates never constitutes Human Authorization or final acceptance.

## 11. Human Authorization boundaries

Human Authorization is required for:
- ratifying the v2.2 governance addendum;
- changing frozen governance rules or authority precedence;
- changing executable governance gate semantics;
- changing workflow enforcement;
- changing task classes that require human authorization;
- optional consolidation of frozen specifications.

No Human Authorization is implied by this report, a worker READY state, tests, CI, commit, or branch existence.

## 12. Unresolved decisions for AI1/Human

1. Exact document name/versioning for the v2.2 addendum.
2. Exact definition of the always-protected boundary list.
3. Whether compatibility support for legacy manifests is time-bounded or version-tagged.
4. Whether `zcode_agent` is mandatory for all governed execution or only ZCODE-backed tasks.

## 13. Acceptance

**READY_FOR_AI1_AUDIT**

No implementation authorization is granted.
