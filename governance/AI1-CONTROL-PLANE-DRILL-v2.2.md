# AI1 Control Plane v2.2 Drill

This drill validates the AI1 control-plane lifecycle without modifying the frozen v2.1 baseline.

## Scenario

- AI2 owns `src/portfolio.py`.
- AI3 initially owns `src/risk.py`.
- AI1 rejects a reallocation of AI3 onto `src/portfolio.py`.
- AI1 blocks AI3 from using `API:RiskService` without a lock.
- AI1 grants `LOCKED` ownership of that interface to AI3.
- AI1 later releases the lock to `UNLOCKED`.

## Expected state transitions

`PLANNED -> ALLOCATED -> READY_TO_START`

Conflict:

`ALLOCATED -> REJECTED`

Interface request:

`ALLOCATED -> BLOCKED`

Authorized interface:

`BLOCKED -> READY_TO_START`

Release:

`LOCKED -> AUDITING -> UNLOCKED`

The drill intentionally uses the existing v2.2 gate as the enforcement primitive. It does not yet automate GitHub issue/PR labels or a remote lock service; those belong to the next Control Plane increment.

Base commit: `e33b649189af17547c73a2e131f808c08baa62ed`
