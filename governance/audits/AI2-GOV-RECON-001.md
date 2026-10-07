# AI2-GOV-RECON-001 — Governance Contract Reconciliation Analysis

Status: READY_FOR_AI1_DESIGN_REVIEW
Owner: AI2 (Workstream AI2)
Executor: ZCODE-A2
Branch: parallel/AI2/AI2-GOV-RECON-001
Base Commit: e33b649189af17547c73a2e131f808c08baa62ed (see §0 — dispatch placeholder was unfilled)
Task type: DESIGN / RECONCILIATION ANALYSIS — proposes only; repairs nothing.

## 0. Baseline decision (recorded for AI1 review)

The dispatch left `BASE_COMMIT: <AI1 WILL PROVIDE EXACT BASE_COMMIT>` unfilled.
This run selected and froze:

```
BASE_COMMIT = e33b649189af17547c73a2e131f808c08baa62ed
            = origin/main HEAD at dispatch
            = tag governance-v2.1^{commit} (machine-verifiable freeze marker)
```

Rationale:
1. WORKTREE-BRANCH-RULES-v1 requires worker branches to start from "the same
   approved main base commit"; absent an explicit AI1 base, the tagged main
   HEAD is the most defensible conformant choice.
2. READ_SET invariance was verified before the choice: `git diff 29403bc
   e33b649 -- governance/` touches only the ADDED `EXECUTION-GUIDE-v2.1.md`;
   all 12 READ_SET spec files are byte-identical across 29403bc (governance-v2.0),
   d47decf (pilot audit HEAD), and e33b649. The analysis is therefore
   base-invariant for every READ_SET file.
3. Corroboration: the v2.2 drill manifests (DRILL-AI2-001, DRILL-AI3-001) freeze
   the same base_commit e33b649, so this base is consistent with the owner's own
   current practice.
4. The AI2-GOV-PILOT-001 report is NOT on main. It was inspected read-only from
   `origin/parallel/AI2/AI2-GOV-PILOT-001` @ d47decf49a4bbf9d57ef7a24694d6cb997b43f39
   and is cited here by SHA. It is not committed to this branch (WRITE_SET).

AI1 MUST confirm or override this base at design review; the choice changes no
READ_SET content, but it determines which artifacts are in-tree.

## 1. Inputs and evidence

Inspected in full (READ_SET, 12/12; byte-identical across the three refs above,
so the earlier pilot reads and this run's reads are the same evidence):
- governance/PROTOCOL-v1.md
- governance/PARALLEL-GOVERNANCE-v2.md
- governance/TASK-TEMPLATE-v1.md
- governance/TASK-DEPENDENCY-SCHEMA-v2.md
- governance/TASK-STATE-MACHINE-v2.md
- governance/SHARED-INTERFACE-LOCK-v2.md
- governance/GOVERNANCE-GATES-v2.md
- governance/AI1-INTEGRATION-CONTROLLER-v2.md
- governance/INTEGRATION-AUDIT-v1.md
- governance/WORKTREE-BRANCH-RULES-v1.md
- governance/ZCODE-A2-PROMPT-v1.md
- governance/ZCODE-A3-PROMPT-v1.md

Inspected as required inputs:
- governance/audits/AI2-GOV-PILOT-001.md @ d47decf (10-dimension audit, CONFLICT;
  includes this workstream's re-execution verification).
- governance/audits/AI3-GOV-PILOT-001.md @ 582085f (read-only cross-worker
  corroboration; 10 findings, CONFLICT).

Inspected as implementation-layer context (on main, outside READ_SET, read-only):
- governance/EXECUTION-GUIDE-v2.1.md
- scripts/governance_gate.py
- .github/workflows/governance-gate.yml
- .agent/task-template.json
- .agent/tasks/DRILL-AI2-001.json (drill instance)

No file outside this report was modified by this task.

## 2. Classification inventory (Requirement 8)

### Contradictions (C) — two statements cannot both hold

| ID | Statement A | Statement B | Evidence |
|----|-------------|-------------|----------|
| C1 | TASK-TEMPLATE-v1 makes FORBIDDEN_SET a mandatory task-contract field | TASK-DEPENDENCY-SCHEMA-v2 defines the task contract without forbidden_set (but with shared_interfaces and structured acceptance that v1 lacks) | both documents claim to define the task contract; a manifest can satisfy either while violating the other (AI2 pilot #4/#10; AI3 #10) |
| C2 | v1 documents make the task status vocabulary {IN_PROGRESS, BLOCKED, READY_FOR_AUDIT, REJECTED} (+ alias READY_FOR_AI1_AUDIT) the worker-facing contract | TASK-STATE-MACHINE-v2 defines an 11-state lifecycle as the task state space; the v1 template Status line cannot represent it | template Status line vs state-machine table (AI2 pilot #3/#10) |
| C3 | Documentation implies glob direct-child semantics for `governance/*.md` (so audit deliverables under `governance/audits/` are not covered) | Executable gate resolves the same pattern as cross-directory: `fnmatch.fnmatchcase('governance/audits/AI2-GOV-RECON-001.md', 'governance/*.md') == True` (re-verified by this run, not taken from AI3 on trust); forbidden check runs over all changed files with no write_set precedence and no manifest exemption | scripts/governance_gate.py `matches()` (fnmatch use) and `run_scope_gate()` (forbidden over all files; only out_of_scope exempts the manifest). Live consequence: the drill-PR gate failures observed by AI3 (#8) |

### Underspecifications (U) — something needed is not stated

| ID | Gap | Source |
|----|-----|--------|
| U1 | Lock lifecycle draws no rejection edge (REQUESTED→UNLOCKED); owner of AUDITING→UNLOCKED undefined; trigger of LOCKED→AUDITING undefined; no failed-audit rework edge (AUDITING→LOCKED) | AI2 pilot #5 as corrected by its re-execution verification (REQUESTED→LOCKED itself IS defined: "AI1 grants or rejects the lock.") |
| U2 | Task-level authorization is not modeled: no state/gate between ALLOCATED and IN_PROGRESS records "contract accepted / scope authorized"; READY_TO_START means only "workspace prepared" | AI2 pilot #2 |
| U3 | Name collision: the lock lifecycle reuses the token AUDITING for a different state machine than the task lifecycle's AUDITING, with no scoping statement | SHARED-INTERFACE-LOCK-v2 vs TASK-STATE-MACHINE-v2 |
| U4 | FORBIDDEN_SET pattern language is defined nowhere: direct-child (`dir/*.md`) vs recursive (`dir/**`) semantics are implied only by glob convention; the executable layer picks crossing-`*` semantics | AI2 pilot #8; AI3 #9; §2 C3 |
| U5 | read_set is a required manifest key but no gate or process consumes it | TASK-DEPENDENCY-SCHEMA-v2 vs scripts/governance_gate.py (read_set never read after validation) |
| U6 | acceptance.gates requires {scope, conflict, test}, but only scope is executable; conflict/test have no automation or invocation contract; GOVERNANCE-GATES-v2 defines five gates (adds Integration, Acceptance) | gate script vs GOVERNANCE-GATES-v2 |
| U7 | BLOCKED exit path unstated: the state table lists owner "Worker/AI1" for BLOCKED but not who clears it and with what evidence | TASK-STATE-MACHINE-v2 |
| U8 | READY_FOR_AUDIT→AUDITING trigger unstated (worker reports completion vs AI1 picks up) | TASK-STATE-MACHINE-v2 |

### Compatible differences (D) — different wording, no conflict

| ID | Difference | Why compatible |
|----|------------|----------------|
| D1 | PARALLEL-GOVERNANCE-v2 §3 summarizes the lock lifecycle without REQUESTED | compressed narrative of the same lifecycle (AI2 pilot #5 as corrected) |
| D2 | v1 narrative Acceptance Criteria vs v2 structured acceptance{tests, gates} | complementary layers once C1 is resolved: prose for humans, schema for machines |
| D3 | v1 hard rules (isolation, no cross-rebase, AI1-only acceptance) restated by v2 | v2 is a superset; nothing in v2 weakens a v1 hard rule |
| D4 | v1 Final Report block vs AI1 integration audit record | different artifacts at different layers (worker completion report vs integration record) |

### Implementation risks (R)

| ID | Risk | Evidence |
|----|------|----------|
| R1 | The gate deterministically blocks legitimate deliverables (C3) and is already failing on open drill PRs | AI3 #8/#9; this run's fnmatch verification |
| R2 | Dual-contract window (C1): manifests validated against either shape leave enforcement gaps until reconciled | both contract documents coexist |
| R3 | Enforcement is procedural, not cryptographic: one GitHub identity pushes main and worker branches alike; branch protection unverifiable without authentication | AI3 #8 |
| R4 | Worker branches cannot run the scope gate from their own tree (gate exists only on main, post-pilot-base); compliance is visible only at PR time | AI3 #7/#10 |
| R5 | If forbidden_set is adopted with an empty-default and nothing else, a task whose manifest omits negative scope has no protection against touching protected paths by accident | TASK-TEMPLATE-v1 (FORBIDDEN_SET mandatory) vs drill manifests (forbidden_set: []) |

## 3. Requirement analyses and proposals

### 3.1 Canonical relationship: TASK-TEMPLATE-v1 ↔ TASK-DEPENDENCY-SCHEMA-v2 (Req 1)

**Answer.** The schema (extended per §3.2) is the canonical machine-readable
task contract; TASK-TEMPLATE-v1 is demoted to the human-facing rendering of the
same contract: narrative fields (Objective, Requirements, Non-Goals, prose
Acceptance Criteria) plus the worker's Final Report artifact. Neither is
deleted; the template displays and narrates what the schema declares.

Field mapping (v1 → canonical):

| TASK-TEMPLATE-v1 | Canonical (schema, extended) | Note |
|---|---|---|
| Task ID / Agent | task_id / agent | agent ∈ {AI1, AI2, AI3} (gate-enforced) |
| ZCODE Agent | zcode_agent (new, informational) | executor identity, not an authority |
| Base Branch | (dropped) | derivable: base_commit + branch naming rule |
| Base Commit | base_commit | frozen; must equal CI base (v2.1 gate enforces) |
| READ_SET | read_set | required; consumed by audit, see §3.9 |
| WRITE_SET | write_set | non-empty; gate-enforced |
| FORBIDDEN_SET | forbidden_set | see §3.2 |
| Non-Goals, Requirements | (template prose) | no machine semantics proposed |
| Dependencies | depends_on / blocks | v2 schema fields |
| Acceptance Criteria | acceptance.gates + acceptance.tests + prose criteria | structured + narrative |
| Deliverables / Final Report | (unchanged artifacts) | worker completion report |
| Status | display subset of canonical v2 vocabulary | see §3.3 |

Decisive fact: `.agent/task-template.json` on main already implements this
superset (task_id, agent, base_commit, depends_on, blocks, read_set,
write_set, forbidden_set, shared_interfaces, acceptance). §3.1 therefore
ratifies existing executable practice rather than inventing a third contract.

### 3.2 FORBIDDEN_SET as a first-class v2 field (Req 2)

**Answer: YES — and it already is de facto.** The v2.1 manifest schema requires
`forbidden_set` and the gate enforces it; only the v2 specification document
lags behind the executable layer. Leaving the spec behind is itself a
contradiction (C1), so the spec must be brought up to the practice, with the
semantics made explicit:

1. **First-class and required** in the extended schema (may be an empty list).
2. **Deny wins**: a changed file matching forbidden_set fails the gate even if
   it also matches write_set. Scope authorization is granted by listing a file
   in write_set; forbidden_set records what is never grantable for this task
   class. This keeps FORBIDDEN_SET meaningful (absolute no-go zones, belt and
   suspenders) instead of redundant.
3. **Pattern language (resolves C3/U4)** — two token forms, stated in the spec:
   - `dir/file.ext` — exact path;
   - `dir/*` and `dir/*.ext` — DIRECT CHILDREN of dir only (one path segment);
   - `dir/**` — everything under dir, including dir itself (recursive).
   The executable layer must be aligned to this language (currently fnmatch
   makes bare `*` cross directories). Until alignment is authorized, manifests
   MUST express recursive intent only with `/**` and must never use bare
   `dir/*.ext` to mean "everything under dir" — the v2.1 template's own
   example (`governance/**`) is already correct under this rule.
4. **Always-protected defaults (resolves R5)**: regardless of manifest content,
   main, the other worker's branch, and the twelve READ_SET governance spec
   files are protected by corpus-level default; a manifest may add to, never
   subtract from, this default set.
5. **Gate hygiene (resolves the C3 asymmetry)**: the manifest file itself is
   exempt from the write_set check (already implemented) and must also be
   exempt from the forbidden check — a manifest must never fail on itself.

### 3.3 Canonical task-state vocabulary and v1→v2 map (Req 3)

**Answer.** TASK-STATE-MACHINE-v2's 11 states are canonical. Mapping:

| v1 token | Canonical v2 state | Relationship |
|---|---|---|
| READY_FOR_AI1_AUDIT (PROTOCOL-v1, ZCODE prompts, INTEGRATION-AUDIT-v1) | READY_FOR_AUDIT | deprecated alias; retire after one release |
| IN_PROGRESS | IN_PROGRESS | identical |
| BLOCKED | BLOCKED | identical |
| READY_FOR_AUDIT (template) | READY_FOR_AUDIT | identical |
| REJECTED | REJECTED | identical name; ownership clarified below |
| (not representable in v1 template) | PLANNED, ALLOCATED, READY_TO_START, AUDITING, INTEGRATING, ACCEPTED, ABORTED | AI1-lifecycle states; workers observe but never set |

Ownership matrix (proposed clarification):

| State | May enter | May exit (to) |
|---|---|---|
| PLANNED, ALLOCATED, READY_TO_START | AI1 | AI1 |
| IN_PROGRESS | Worker (from READY_TO_START/BLOCKED) | Worker → BLOCKED/READY_FOR_AUDIT |
| BLOCKED | Worker (self) or AI1 | Worker (self-BLOCK only, with written resolution note) → IN_PROGRESS; AI1 (any BLOCK) → IN_PROGRESS/ABORTED |
| READY_FOR_AUDIT | Worker | AI1 → AUDITING |
| AUDITING, INTEGRATING, ACCEPTED, REJECTED, ABORTED | AI1 | AI1 |

Template Status line: redefined as a worker-VISIBLE display vocabulary
(what a worker may report), not the state space. This resolves C2 without
changing the template's shape.

### 3.4 Is authorization a state/gate separate from READY_TO_START? (Req 4)

**Answer: authorization must be explicit and auditable, but the minimal
compatible path extends READY_TO_START rather than adding a 12th state.**

Today authorization exists operationally (AI1's dispatch, the frozen manifest)
but is invisible to the state machine: READY_TO_START means "workspace
prepared" only (AI2 pilot #2/U2). Two options:

- **Option A (recommended): extend READY_TO_START entry evidence.**
  READY_TO_START requires a recorded evidence triple: (a) manifest frozen
  (task_id, base_commit, sets), (b) AI1 allocation/authorization decision,
  (c) human authorization IF the task class requires it. No new state; the
  v1 template is untouched; AI1-INTEGRATION-CONTROLLER gains one checklist
  item.
- Option B: insert an AUTHORIZED state between ALLOCATED and READY_TO_START.
  More explicit, but adds a 12th state and re-maps every consumer for no
  additional enforcement power.

Task classes that always require Human Authorization: those editing frozen
governance specs, changing authority boundaries, or implementing against a
four-phase contract-acceptance path (project precedent: the P14-D contract's
Contract Acceptance → Human Authorization → Implementation → Independent
Acceptance separation). Proposed manifest field (additive):

```yaml
authorization:
  authorized_by: AI1
  human_authorization_required: false   # true for the task classes above
  human_authorization_ref: null         # pointer to the human decision record
```

Note: shared-interface authorization remains a separate lock lifecycle (§3.5);
task authorization and interface locks must not be conflated.

### 3.5 Shared Interface Lock: full transition analysis (Req 5)

Canonical lock FSM (proposed completion of SHARED-INTERFACE-LOCK-v2):

| Edge | Owner | Trigger / required evidence |
|---|---|---|
| UNLOCKED → REQUESTED | Worker | lock request carrying all six required fields (task_id, target, reason, proposed change, impacted agents/tasks, compatibility plan) |
| REQUESTED → LOCKED | AI1 | explicit grant ("AI1 grants or rejects the lock" — already defined, SHARED-INTERFACE-LOCK-v2) |
| REQUESTED → UNLOCKED | AI1 or requesting Worker | explicit rejection (AI1) or withdrawal (worker); **edge must be added to the lifecycle line** |
| LOCKED (hold state) | authorized Worker | the one authorized worker modifies the locked interface in-state; all other workers read-only |
| LOCKED → AUDITING | AI1 | worker reports the interface change complete (its task READY_FOR_AUDIT); **trigger must be stated** |
| AUDITING → UNLOCKED | AI1 | interface audit PASS; **owner must be stated** |
| AUDITING → LOCKED | AI1 | interface audit FAIL → rework by the same authorized worker; **new edge, prevents silent unlock on failure** |

Residual points this FSM adds beyond the documents:
- U1 closed (rejection edge, audit-exit owner, audit-fail rework edge, audit
  trigger).
- U3 acknowledged and contained: the lock machine's AUDITING is a different
  state from the task machine's AUDITING. Containment: scope the tokens
  (`lock:AUDITING` vs `task:AUDITING`) in the addendum; a rename to LOCK_AUDIT
  is proposed for the next major revision only (editing the frozen v2 file
  needs Human Authorization).
- Invariant to state in the spec: workers never acquire a lock by editing
  first (already written); acquisition must precede any IN_PROGRESS
  modification of the locked interface.

### 3.6 Which document is authoritative when v1 and v2 differ? (Req 6)

**Proposed precedence rule (canonical authority declaration):**

1. PROTOCOL-v1 hard rules are constitutional: no later statement may weaken
   them; an apparent weakening escalates to Human, not to interpretation.
2. Among governance model documents, an explicit v2 statement governs over v1
   where the two conflict.
3. Where v2 is silent, v1 governs unchanged.
4. The v2.1 execution layer (EXECUTION-GUIDE-v2.1, gate script, CI workflow)
   binds executable enforcement; where it diverges from the written semantics,
   that divergence is a finding (C3) to be repaired in the layer that is wrong —
   never reinterpreted silently.
5. PR-local task manifests are instances of the contract, never rules.
6. Every adjudication under this rule is recorded (as this document records
   C1–C3); unresolved conflicts are BLOCKED items for AI1, not worker judgment
   calls.

Corpus layering (proposed): PROTOCOL-v1 (constitutional) → PARALLEL-GOVERNANCE-v2
(model) → per-domain v2 specs (schema / state machine / lock / gates) →
EXECUTION-GUIDE-v2.1 (executable binding) → task manifests (instances).
Tags governance-v2.0 / governance-v2.1 are the freeze markers.

### 3.7 Minimum backward-compatible migration path (Req 7)

Four phases; each is independently revertible and nothing existing breaks at
any step:

- **Phase 0 (this document).** Analysis only; zero changes. DONE.
- **Phase 1 — one additive addendum** (new file, e.g.
  `governance/RECONCILIATION-ADDENDUM-v2.2.md`): extended manifest schema
  (§3.1/§3.2 including authorization object), canonical vocabulary + alias
  table (§3.3), READY_TO_START evidence (§3.4), completed lock FSM (§3.5),
  precedence rule + layering (§3.6), always-protected defaults, pattern
  language. No existing v1/v2 file is edited; all current references stay
  valid; conflicts resolve per the precedence rule. Requires Human
  ratification because it re-weights ratified documents (see §5).
- **Phase 2 — executable alignment** (separately authorized): align
  `scripts/governance_gate.py` to the pattern language (direct-child `*`),
  add manifest self-exemption from forbidden check, optional read_set lint
  (§3.9); CI unchanged. Requires Human Authorization (enforcement code).
- **Phase 3 — consolidation (optional)**: edit TASK-TEMPLATE-v1 /
  TASK-DEPENDENCY-SCHEMA-v2 / SHARED-INTERFACE-LOCK-v2 texts to reference the
  addendum, retire the READY_FOR_AI1_AUDIT alias, cut a new baseline tag.
  Requires Human Authorization; only start after Phase 1 has operated across
  at least one full task cycle.

In-flight tasks continue under the v1 template unchanged throughout.

### 3.8 Proposed canonical contract (Req 9 — PROPOSAL ONLY, nothing modified)

```yaml
task_id: <id>                     # required
agent: AI2                        # AI1 | AI2 | AI3 (required)
zcode_agent: ZCODE-A2             # informational executor identity
base_commit: <40-char sha>        # frozen; must equal CI base (v2.1)
depends_on: []                    # task_ids; hard deps must be SATISFIED to start
blocks: []
read_set: []                      # required; audit-consumed (no gate today)
write_set:                        # non-empty; the ONLY grantable change area
  - <path or pattern>
forbidden_set:                    # required, may be []; deny wins over write_set
  - dir/file.ext                  # exact
  - dir/*                         # direct children only
  - dir/**                        # recursive, includes dir
shared_interfaces:                # each declares a lock target
  - target: <interface>
    lock_state: UNLOCKED          # UNLOCKED|REQUESTED|LOCKED|AUDITING (lock FSM)
    lock_ref: null
authorization:                    # §3.4; additive with defaults
  authorized_by: AI1
  human_authorization_required: false
  human_authorization_ref: null
acceptance:
  tests: []
  gates: [scope, conflict, test]  # executable set; integration/acceptance stay AI1-manual
  criteria: []                    # narrative (v1 rendering) — no machine semantics
status: IN_PROGRESS               # canonical v2 vocabulary; worker-settable
                                  # subset = {IN_PROGRESS, BLOCKED, READY_FOR_AUDIT}
```

Defaults (implicit, corpus-level, never listed per task): main, the sibling
worker branch, and the twelve governance spec files are always protected.

### 3.9 Additional closure items surfaced by the analysis

- **read_set (U5)**: keep required; give it a consumer — minimum: the
  integrator's audit must show read_set was honored (no evidence of
  modification of read-only inputs); the gate MAY lint read_set ∩ write_set = ∅.
- **Gate coverage (U6)**: rename nothing; document that gates {scope} are
  executable and {conflict, test, integration, acceptance} are AI1-manual until
  automation is separately authorized.
- **BLOCKED exit (U7) / READY_FOR_AUDIT→AUDITING trigger (U8)**: one sentence
  each in the addendum per §3.3's ownership matrix.

## 4. Consolidated change register (Req 10)

| # | Proposed change | Affected document | Affected field/state | Semantic reason | Compatibility impact | Human Authorization required? |
|---|---|---|---|---|---|---|
| 1 | forbidden_set into the spec (deny-wins, required-may-be-empty) | TASK-DEPENDENCY-SCHEMA-v2 (via addendum) | task contract field | closes C1; spec lags the already-executing v2.1 layer | additive; Phase 1 | YES — ratified-spec change (addendum ratification) |
| 2 | Pattern language: direct-child `*`, recursive `/**` | GOVERNANCE-GATES-v2 Scope Gate + EXECUTION-GUIDE-v2.1 (via addendum) | forbidden_set/write_set matching | closes C3/U4: documented semantics and executable semantics must agree | semantic-only until code aligns; manifests using `/**` are already correct | YES (code change in Phase 2; spec wording in Phase 1 addendum) |
| 3 | Manifest self-exemption from forbidden check | scripts/governance_gate.py (Phase 2) | run_scope_gate | a manifest must never fail on its own existence | behavioral, narrow | YES — enforcement code |
| 4 | Canonical vocabulary + alias retirement plan | TASK-STATE-MACHINE-v2 (via addendum now; file edit only Phase 3) | state tokens; READY_FOR_AI1_AUDIT alias | closes C2 | additive alias table; template unchanged | Phase 1 addendum YES; Phase 3 file edits YES |
| 5 | READY_TO_START entry evidence + manifest authorization object | PARALLEL-GOVERNANCE-v2 §1 / AI1-INTEGRATION-CONTROLLER-v2 (via addendum) | READY_TO_START; authorization{} | closes U2: pre-work authorization becomes auditable | additive with defaults; no new state | NO for modeling; task classes with human_authorization_required=true are Human-gated at execution |
| 6 | Lock FSM completion (4 edges + owners) | SHARED-INTERFACE-LOCK-v2 (via addendum) | lock lifecycle | closes U1/U3-containment | additive | Phase 1 addendum YES; rename to LOCK_AUDIT deferred, YES |
| 7 | Precedence rule + corpus layering | corpus-level (via addendum) | interpretation authority | closes C1/C2 adjudication permanently | no text edited; adjudication rule only | YES — re-weights ratified documents |
| 8 | Always-protected defaults | corpus/gate (via addendum + Phase 2) | default forbidden set | closes R5 | additive; cannot be subtracted by manifests | YES (affects every future task's scope) |
| 9 | read_set consumer + lint | AI1-INTEGRATION-CONTROLLER-v2 checklist / gate lint (Phase 2) | read_set | closes U5 | additive | NO (checklist) / YES (gate code) |
| 10 | BLOCKED-exit and AUDITING-trigger sentences | TASK-STATE-MACHINE-v2 (via addendum) | BLOCKED, READY_FOR_AUDIT→AUDITING | closes U7/U8 | additive | Phase 1 addendum YES |

## 5. Conclusions

RECONCILIATION STATUS: **READY_FOR_AI1_DESIGN_REVIEW**

HUMAN AUTHORIZATION REQUIRED: **YES** — required for: ratification of the
Phase 1 addendum and the precedence rule (re-weights ratified documents);
any Phase 2 change to `scripts/governance_gate.py` (enforcement code); any
Phase 3 edit of frozen v1/v2 specification files; and at execution time, any
task whose class sets `human_authorization_required: true`. NOT required for
the AI1 design review of this document itself.

PROPOSED_CANONICAL_AUTHORITY: **TASK-DEPENDENCY-SCHEMA-v2, extended with
forbidden_set and the authorization object (i.e., the ratified v2.1 PR-local
manifest schema), is the canonical machine-readable task contract;
TASK-STATE-MACHINE-v2 is the canonical state vocabulary
(READY_FOR_AI1_AUDIT = deprecated alias of READY_FOR_AUDIT); PROTOCOL-v1 hard
rules remain constitutional; on explicit conflict the v2 statement governs,
where v2 is silent v1 governs, and apparent weakenings of PROTOCOL-v1 escalate
to Human; EXECUTION-GUIDE-v2.1 binds executable enforcement and its divergence
from written semantics is repairable only as an authorized finding; PR-local
manifests are instances, never rules.**

PROPOSED_NEXT_ACTION: **AI1 performs design review of this document; if
endorsed, AI1 drafts ONE additive addendum (proposed name
governance/RECONCILIATION-ADDENDUM-v2.2.md) carrying items 1, 2, 4, 5, 6, 7,
8, 10 of §4; the Human ratifies addendum + precedence; then — separately
authorized — the gate script is aligned to the pattern language (items 3, 8,
9); new PR-local manifests adopt the extended schema while in-flight tasks
continue unchanged; no existing v1/v2 file is edited before Phase 3
consolidation is separately authorized.**

## 6. Scope / Change Audit

This branch (parallel/AI2/AI2-GOV-RECON-001, based on e33b649) adds exactly one
file: governance/audits/AI2-GOV-RECON-001.md. No governance specification, no
executable governance code, no workflow file, no task manifest, no
docs/contracts/, docs/authorizations/, AI_HANDOFF, or PROJECT_STATUS file was
modified; no authorization was created or inferred; no finding was repaired;
main and all AI3 branches are untouched; nothing was merged.

## 7. Task Completion

Analysis complete against BASE_COMMIT e33b649 (tag governance-v2.1) with pilot
inputs pinned at AI2 d47decf and AI3 582085f.

DONE is not acceptance; design review, ratification, implementation
authorization, and acceptance remain with AI1 and the Human as partitioned in
§5. Final status: READY_FOR_AI1_DESIGN_REVIEW.
