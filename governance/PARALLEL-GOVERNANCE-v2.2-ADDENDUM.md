# Parallel Agent Governance v2.2 — Reconciliation Addendum

Status: ACTIVE (Phase 1 contract layer)
Base: e33b649189af17547c73a2e131f808c08baa62ed (tag `governance-v2.1`)
Implementing task: AI2-GOV-V22-ADDENDUM-IMPLEMENT-001 (AI2 / ZCODE-A2, EXECUTOR ONLY)
Provenance: implements the design decisions of AI1-V22-DESIGN-REVIEW-001
(FINAL DESIGN DECISION; IMPLEMENTATION AUTHORIZATION: GRANTED) under Human
Authorization `HUMAN-AUTH-V22-PHASE1-AND-EXECUTABLE-IMPLEMENTATION-2026-10-07`.

This addendum is ADDITIVE. It does not modify PROTOCOL-v1,
PARALLEL-GOVERNANCE-v2, TASK-STATE-MACHINE-v2, SHARED-INTERFACE-LOCK-v2,
GOVERNANCE-GATES-v2, TASK-TEMPLATE-v1, EXECUTION-GUIDE-v2.1, or any tag.
Where this addendum and an older document appear to differ, the Authority
Precedence (§7) decides.

## 1. FORBIDDEN_SET — first-class v2.2 task field

FORBIDDEN_SET is a required task-contract field. It may be an empty list.

The Scope Gate checks every changed file against FORBIDDEN_SET. Any match
FAILS the gate:

```
changed file
   |
   +-- matches FORBIDDEN_SET --------> FAIL   (deny wins)
   |
   +-- no FORBIDDEN_SET match
         +-- matches WRITE_SET ------> allowed
         +-- no WRITE_SET match ------> FAIL (WRITE_SET violation)
```

Deny-wins: a FORBIDDEN_SET match fails the gate EVEN IF the same file also
matches WRITE_SET. WRITE_SET can never override FORBIDDEN_SET. There is no
precedence rule, no negation syntax, and no exemption other than the manifest
self-exemption (§3).

## 2. Path pattern semantics (normative)

Matching is performed on normalized paths (backslashes normalized to forward
slashes). Three pattern forms exist:

### exact
`foo/bar.py` matches exactly `foo/bar.py` and nothing else.

### `*` — single path component
`*` matches within ONE path component only; it never crosses `/`.

- `governance/*.md` matches `governance/A.md`
- `governance/*.md` does NOT match `governance/audits/A.md`

### `**` — recursive (trailing position only)
`dir/**` matches everything under `dir/`:

- `governance/**` matches `governance/A.md`
- `governance/**` matches `governance/audits/A.md`
- `governance/**` matches `governance/a/b/c.md`

`**` in any position other than trailing is an INVALID pattern; a manifest
carrying one fails at load time with a schema/contract error. No negation
syntax exists in v2.2.

## 3. Manifest self-exemption

Only the exact manifest path itself — the single
`.agent/tasks/<TASK-ID>.json` currently being evaluated — is exempt from the
WRITE_SET and FORBIDDEN_SET checks.

The exemption MUST NOT be widened:

- not to `.agent/**`;
- not to `.agent/tasks/**`;
- not to any other manifest or any other file.

## 4. Canonical task state vocabulary

The canonical vocabulary is the 11-state machine of TASK-STATE-MACHINE-v2,
whose state/owner table remains unchanged:

```
PLANNED, ALLOCATED, READY_TO_START, IN_PROGRESS, BLOCKED, READY_FOR_AUDIT,
AUDITING, INTEGRATING, ACCEPTED, REJECTED, ABORTED
```

- No AUTHORIZED state may be added. Authorization is an ENTRY CONDITION of
  READY_TO_START (§5), not a state.
- `READY_FOR_AI1_AUDIT` is NOT a canonical state. It survives only as a
  deprecated display alias of READY_FOR_AUDIT in legacy v1 documents.
  New artifacts MUST use the canonical vocabulary.
- Worker-settable states: IN_PROGRESS, BLOCKED, READY_FOR_AUDIT. A worker may
  clear its own BLOCKED only with a written resolution note; AI1 may clear any
  BLOCKED and owns all other transitions (restates TASK-STATE-MACHINE-v2).

## 5. READY_TO_START entry conditions

READY_TO_START is not an informal "ready" status. It means exactly:

```
READY_TO_START =
    frozen task manifest
  + AI1 authorization evidence
  + Human Authorization evidence (when the task class requires it)
```

- Frozen task manifest: task_id, base_commit (the Task Frozen Base),
  read_set, write_set, forbidden_set are recorded and unmodified after freeze.
- AI1 authorization evidence: `authorization.ai1_authorized: true` backed by
  an AI1 allocation record.
- Human Authorization evidence: when
  `authorization.human_required: true`, `authorization.human_authorization_ref`
  MUST resolve to a real authorization record; if it does not, the task cannot
  reach READY_TO_START.

## 6. Shared Interface Lock FSM v2.2

The lock lifecycle with all edges and owners:

```
UNLOCKED --(worker request)----------> REQUESTED
REQUESTED --(AI1 grants)------------> LOCKED
REQUESTED --(AI1 reject | worker withdrawal)--> UNLOCKED
LOCKED   --(AI1 starts audit)-------> AUDITING
AUDITING --(AI1 pass)---------------> UNLOCKED
AUDITING --(AI1 fail / rework)------> LOCKED
```

- While LOCKED, exactly the one authorized worker may modify the locked
  interface; all other workers have read-only access.
- A worker can never acquire a lock by editing the interface first
  (restates SHARED-INTERFACE-LOCK-v2).
- Lock requests carry the six required fields defined in
  SHARED-INTERFACE-LOCK-v2 (task_id, target, reason, proposed change,
  impacted agents/tasks, compatibility plan).
- The lock state AUDITING is distinct from the task state AUDITING. They are
  read as `lock:AUDITING` and `task:AUDITING`. A token rename is deferred to
  the Phase 3 consolidation and is not part of v2.2.

## 7. Authority precedence

When governance sources appear to conflict, they rank as follows:

```
1. v1 constitutional / core governance
2. explicit v2 rules
3. v1 rules where v2 is silent
4. v2.1 executable behavior
5. task manifests
6. unresolved conflict  ->  block AI1 acceptance
```

If an executable implementation is inconsistent with a normative governance
contract, the implementation is the defect. The defect is repaired through an
authorized change to the implementation; the contract is not reinterpreted to
match the code.

## 8. Always-Protected Boundary

The Always-Protected Boundary is separate from, and higher than, the
task-level FORBIDDEN_SET. It is an authorization boundary, not a manifest
field.

Default coverage (ordinary workers cannot modify these regardless of manifest
content):

- `governance/**`
- `.github/workflows/**`
- `.agent/**`
- executable governance scripts (including `scripts/governance_*.py` and
  successors designated by AI1)
- AI1-designated production schema/config authorities

Protected boundary exception: with Human Authorization AND an explicit AI1
designation, named paths may receive a
`authorization.protected_boundary_exception`. Such an exception only allows
the named paths to enter the normal WRITE_SET / FORBIDDEN_SET judgment. It
never bypasses FORBIDDEN_SET deny-wins (§1) or any other gate.

This addendum's own implementing task operates under such an exception,
recorded in its manifest.

## 9. Migration v2.1 → v2.2

```
Phase 0  Analysis
         AI2-GOV-PILOT-001, AI3-GOV-PILOT-001, AI2-GOV-RECON-001,
         AI3-GATE-VALIDATION-001, AI1-V22-DESIGN-REVIEW-001        [COMPLETE]

Phase 1  Additive Reconciliation Addendum
         this document + TASK-DEPENDENCY-SCHEMA-v2 alignment
         + .agent/task-template.json alignment                     [THIS TASK]

Phase 2  Executable Alignment
         scripts/governance_gate.py,
         .github/workflows/governance-gate.yml,
         tests/test_governance_gate_v22.py
         owned by AI3 — OUT OF SCOPE for this task                 [SEPARATE TASK]

Phase 3  Optional Consolidation
         editing v1/v2/v2.1 documents; requires its own
         Human Authorization                                       [DEFERRED]
```

Migration rules: tags `governance-v2.0` and `governance-v2.1` are never
modified or moved; in-flight v2.1 tasks continue under v2.1 unchanged; no
existing manifest is retrofitted.

## 10. Relationship to the executable layer

At the frozen base the executable gate still implements fnmatch semantics and
lacks the load-time checks defined here. Under §7 that divergence is a defect
of the implementation, to be repaired by the Phase 2 executable-alignment
task. Until that repair lands and is accepted, the normative contract of this
addendum governs design and review; it does not change what the current
binary behavior of the gate is.
