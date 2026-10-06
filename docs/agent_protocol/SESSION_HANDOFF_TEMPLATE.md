# SESSION HANDOFF REPORT — <TASK-ID / TITLE>

> Template: fill every section. Delete nothing. If a section is empty,
> write NONE (or NOT APPLICABLE with one-line reason). The successor
> must be able to take over with ZERO chat-context dependence.

## 1. Session Identity

```text
Agent:              <AI1 / AI2 / AI3>
Date:               <UTC date>
Base HEAD:          <sha stated by the task>
Final HEAD:         <sha after this session's last commit>
Divergence check:   <origin/main vs HEAD, behind/ahead>
```

## 2. Completed Work

- <item: what was done, which task/phase>
- <item…>

## 3. Current State (after this session)

```text
Repository status:  <clean / dirty detail>
Current phase:      <from PROJECT_STATUS, unchanged or updated>
Working gate:       <e.g. READY FOR INDEPENDENT ACCEPTANCE / BLOCKED / …>
```

## 4. Remaining Blockers

| blocker | evidence | who can clear it |
|---|---|---|
| <blocker> | <commit / run / doc reference> | <Human / Independent Acceptance / …> |

## 5. Authorization Status

```text
Granted this session:      <NONE or explicit reference>
Still NOT granted:         <list — e.g. R4-D APPLY, R4-D implementation,
                            P14-F, P13-T execution>
Protected boundaries:      P13-T STOPPED / P13-U PROTECTED (untouched: YES/NO)
```

## 6. Next Recommended Action

<One action, tied to the current gate. Do not start it. Reference the
authorization required to start it.>

## 7. ZCODE Prompt (if needed)

```text
<The exact task prompt the successor should issue to ZCODE for the
implementation step — scope, files, frozen constraints, verification,
and stop conditions. Omit if no ZCODE step is pending.>
```

## 8. Verification Evidence

```text
Full pytest:         <result>
Contract audits:     <P14-C / P14-D / P14-E results>
P13-M regression:    <result>
Exact-head CI:       <run id @ final HEAD, conclusion>
git diff --check:    <clean / issues>
```

## 9. Standing Reminders (copy verbatim — do not edit)

- Implementation Complete != Independent Acceptance.
- Tests Green != Authorization. CI PASS != Production Approval.
- Do not infer authorization from tests passing.
- Do not modify frozen artifacts without a new authorization.
- Do not cross P13-T / P13-U / P14-F boundaries.
- The GitHub repository is the memory — this report is part of it;
  chat history is not.
