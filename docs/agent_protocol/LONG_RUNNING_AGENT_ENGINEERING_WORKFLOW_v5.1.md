# Long-Running Agent Engineering Workflow v5.1

> STATUS: ACTIVE PROTOCOL — formalizes the multi-agent rotation workflow
> for this repository. Supersedes v5.0.
>
> Scope: governance documentation ONLY. This file changes no code, no
> artifact, no contract semantics, no project status.
>
> Ratified: 2026-10-06 at the state audited by READ-ONLY TAKEOVER
> AUDIT-001 (Exact HEAD `1d82903`).

## 1. Purpose

A long-running engineering project is executed by a rotation of
equivalent Lead Agents across many sessions, months, and model
generations. Chat history is ephemeral and unreliable. This protocol
defines how work survives agent turnover:

**The GitHub Repository is the permanent memory — NOT chat history.**

Everything a successor needs must exist in the repository: status,
contracts, evidence, artifacts, and this protocol.

## 2. Truth Precedence Chain

When sources disagree, the higher entry wins:

```text
1. Repository State        (git: HEAD, files, SHAs — discovered LIVE)
2. PROJECT_STATUS.md       (consolidated governance record)
3. Contracts               (docs/contracts/ — normative definitions)
4. Evidence                (docs/artifacts/, audit records, manifests)
5. CI                      (GitHub Actions runs, exact-head verified)
6. Agent Reports           (session reports, handoff narratives)
7. Chat History            (ephemeral; never a source of truth)
```

Rules:

- NEVER trust a document's claimed HEAD — discover it live
  (`git fetch` + `git rev-parse HEAD` + `git status --short`).
- NEVER trust an agent conclusion without repository verification.
- A document that contradicts the repository state is stale; the state
  wins; report the discrepancy (do not silently fix governance docs —
  apply the Narrow Repair discipline).

## 3. Agent Model

AI1, AI2, AI3 are **equivalent Long-Running Project Lead Agents**. There
are no permanent specialized roles; every agent must be able to take
over the full project at any time.

Capabilities are bounded by PHASE, not by identity:

- Every agent operates strictly inside the active task's scope.
- Every agent ends its session with a SESSION HANDOFF REPORT.
- Every agent begins its session with a READ-ONLY TAKEOVER AUDIT.

## 4. Governance Model (unchanged from v5.0, restated as law)

```text
Human          decides architecture, authorization, progression
Contract       defines truth (normative, versioned, frozen by acceptance)
Authority      defines ownership (P14-D=PIT, P14-E=evidence,
               P14-B=raw, P14-C=reconciliation, P13-Q=calibration,
               P13-R=policy — see accepted contracts)
Agent          executes within boundaries
Tests          verify behavior
CI             produces evidence
Independent    decides status
  Acceptance
```

The three separation laws:

```text
Implementation Complete != Independent Acceptance
Tests Green             != Authorization
CI PASS                 != Production Approval
```

Authorization and acceptance are HUMAN acts, recorded in
`docs/PROJECT_STATUS.md` by explicit owner decision. They are never
inferred from tests, CI, or agent claims.

## 5. Session Lifecycle

```text
TAKEOVER (read-only audit)
   ↓
WORK (within authorized scope)
   ↓
HANDOFF (report + repository state)
```

### 5.1 Takeover — READ-ONLY TAKEOVER AUDIT (mandatory first action)

Reading order (strict):

1. `docs/AI_HANDOFF.md` (takeover entry point + rulebook)
2. `docs/PROJECT_STATUS.md` (consolidated state — read the LAST
   sections first)
3. The active contract(s) for the task at hand
4. Evidence documents for the active artifacts

Live discovery (never copy HEAD from any document):

```text
git fetch
git rev-parse HEAD
git status --short
git log --oneline -10
```

Then the audit: frozen artifact SHAs re-verified; protected boundaries
confirmed; authorization state confirmed; working tree clean; CI
evidence checked for the relevant HEADs. Output: a **TAKEOVER REPORT**
(see AGENT_TAKEOVER_PROTOCOL.md §Report) covering current HEAD,
repository status, current phase, authorization state, frozen
boundaries, protected phases, allowed next actions, forbidden actions.
Any discrepancy → STOP and report (BLOCKED / OBSERVATION); do not
silently fix governance documents.

### 5.2 Work

- Execute strictly within the authorized scope (Exact HEAD Rule: start
  from the stated base commit; STOP on mismatch).
- Frozen artifacts, protected boundaries, and accepted authority
  surfaces are untouchable without a new explicit authorization.
- Contract violations found mid-work → Narrow Repair discipline or STOP
  (never "fix it in passing").

### 5.3 Handoff — SESSION HANDOFF REPORT (mandatory close)

Every completed session produces a **SESSION HANDOFF REPORT**
(SESSION_HANDOFF_TEMPLATE.md) covering: completed work, current state,
remaining blockers, authorization status, next recommended action, and
a ZCODE prompt if needed. The repository state after the session must
let a successor take over with ZERO chat-context dependence.

## 6. ZCODE Relationship

```text
AI Agent (Lead):    architecture · contract · planning · acceptance
ZCODE (Executor):   implementation execution only
```

- The Lead Agent defines WHAT (contract, scope, frozen parameters,
  acceptance criteria); ZCODE executes HOW within that scope.
- ZCODE output is subject to the same gates as any other
  implementation: scope diff, golden tests, exact-head CI, and
  Independent Acceptance.
- A ZCODE session is itself governed by this protocol (takeover audit
  → execution → handoff report).

## 7. Frozen & Protected Boundaries (standing)

- Frozen artifacts (MODEL_APPLICATION, MANIFEST, CALIBRATION,
  CALIBRATION_MANIFEST and their SHAs) are immutable without a new
  authorization; any byte change = a new model_version.
- Protected boundaries: P13-T (STOPPED / NOT EXECUTED), P13-U
  (PROTECTED — decision dates ≥ 2026-09-23 excluded everywhere),
  P14-F (NOT AUTHORIZED).
- Accepted authority surfaces (pit.py / research_query.py / evidence.py
  semantics, registries) are not modified without a contract-level
  authorization.
- Historical OOS predictions are never forward models (R4D-003c);
  predictions are never "recovered" into artifacts.

## 8. Lessons Codified (v5.0 → v5.1)

| Lesson (source event) | Codified rule |
|---|---|
| P13-O artifact recovery failure — historical OOS predictions cannot be re-created into a model artifact | Three-artifact taxonomy (HISTORICAL_OOS_PREDICTION / MODEL_APPLICATION / CALIBRATION) is normative; recovery claims are audited, never assumed; re-fitting requires a fresh pre-registered authorization (R4D-002a/003b/003c) |
| R4-D governance — "additive and conceptually sound" changes to frozen surfaces are still scope violations | Do-Not-Modify is interpreted literally per file; narrow repairs fix exactly the named defect; contract-level changes require contract-level gates |
| Exact HEAD verification — documents drift, self-reference recurses | Live discovery always; AI_HANDOFF carries a HANDOFF BASELINE (not its own SHA); CURRENT HEAD is discovered live, never copied |
| Frozen artifact protection — parameter identity is content-addressed | Artifact bytes → SHA-256 → manifest → evidence chain; hash mismatch → FAIL CLOSED; canonical serialization normative |
| Independent Acceptance — implementation, tests, CI are never status | The three separation laws (§4); status records cite owner decisions with evidence chains |
| AI rotation handoff — successors cannot trust chat | Repository-as-memory; mandatory TAKEOVER AUDIT and HANDOFF REPORT; templates enforce completeness |

## 9. Protocol Change Control

This protocol is itself versioned. Changes require: (a) a documentation-
only commit, (b) an explicit statement of what rule changed and why,
(c) no retroactive reinterpretation of completed phases. The repository
state always outranks the protocol text in describing what IS; the
protocol governs what MAY be done next.

## 10. Current Standing Decisions (as of ratification)

- R4-D = CONTRACT ACCEPTED / APPLY BLOCKED / **ELIGIBLE FOR
  AUTHORIZATION** (C1–C12 satisfied; unlock = Human Authorization act).
- P14-F = NOT AUTHORIZED.
- P13-T = STOPPED / NOT EXECUTED; P13-U = PROTECTED.
- Frozen forward model: `p13o-forward-logistic`, model_version
  `97602f4d…664`, variant `industry_5_20` (see
  docs/artifacts/P13-O-FORWARD-MODEL-ARTIFACT-EVIDENCE.md).
