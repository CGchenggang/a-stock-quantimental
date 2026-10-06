# AGENT TAKEOVER PROTOCOL

> Part of the Long-Running Agent Engineering Workflow v5.1.
> Governs every session start of every Lead Agent (AI1/AI2/AI3).

## 1. First Action (mandatory, in order)

```text
git fetch
git rev-parse HEAD
git status --short
git log --oneline -10
```

Record the **CURRENT LIVE HEAD**. Never copy a HEAD from any document,
chat message, or previous report.

## 2. Required Reading (strict order)

1. `docs/AI_HANDOFF.md` — takeover entry point + rulebook
2. `docs/PROJECT_STATUS.md` — read the LAST sections first (current state)
3. The active contract(s) for the current task
4. Evidence documents for any frozen/active artifact
5. Relevant audit evidence (prior acceptance records)

## 3. Consistency Check

Compare the LIVE HEAD against:

- HANDOFF BASELINE in `docs/AI_HANDOFF.md`
- Current Commit recorded in `docs/PROJECT_STATUS.md`
- Git history

Note whether the delta since the baseline is documentation-only,
scope-consistent, or contains unexpected changes. Unexpected changes →
STOP and report as OBSERVATION (do not revert, do not proceed silently).

## 4. Takeover Report (mandatory output)

Every takeover emits a report containing ALL of:

```text
TAKEOVER REPORT
Repository:            <origin URL>
CURRENT LIVE HEAD:     <full sha>
Baseline:              <HANDOFF BASELINE sha, delta description>
Branch / workspace:    <branch> / clean or dirty (detail)
Current phase:         <from PROJECT_STATUS Current Phase>
Authorization state:   <what is granted / what is NOT granted>
Frozen boundaries:     <artifact SHAs + protected date boundaries>
Protected phases:      <P13-T / P13-U / P14-F states>
Allowed next actions:  <from the current gate>
Forbidden actions:     <from the current gate + standing rules>
Discrepancies:         <BLOCKED / OBSERVATION items, or NONE>
```

## 5. Takeover Stop Conditions

STOP (report only, do not fix) if:

- HEAD does not match the task-stated base commit (STOP — BASE HEAD
  MISMATCH).
- Working tree is dirty with unauthorized changes.
- Frozen artifact SHAs no longer match the evidence record.
- Any decision date ≥ virgin_start appears in research-relevant state.
- Governance documents contradict each other on authorization state.
- The task asks for something the active contract forbids.

## 6. Standing Forbidden Actions (apply to every session)

- Do not trust previous AI conclusions without repository verification.
- Do not infer authorization from tests passing.
- Do not infer production approval from CI green.
- Do not modify frozen artifacts or their SHAs.
- Do not cross protected boundaries (P13-T / P13-U / P14-F).
- Do not start unauthorized phases.
- Do not self-declare PASS / ACCEPTED / AUTHORIZED.
- Do not modify accepted authority surfaces without a contract-level
  authorization.
- Do not treat chat history as a source of truth.

## 7. Work Phase Rules

- Exact HEAD Rule: begin implementation from the stated base commit;
  STOP on mismatch.
- Scope discipline: only the files/surfaces the task authorizes; narrow
  repair discipline for defects (fix the named defect, not the
  neighborhood).
- Frozen/protected rules per WORKFLOW v5.1 §7.
- Verification: full pytest, contract audits, exact-head CI after push.

## 8. Session Close (mandatory)

Produce a SESSION HANDOFF REPORT (SESSION_HANDOFF_TEMPLATE.md), commit
with a scoped message, push with retry, verify exact-head CI for the
final HEAD, and STOP — awaiting Independent Acceptance / Human
Authorization where the gate requires it.
