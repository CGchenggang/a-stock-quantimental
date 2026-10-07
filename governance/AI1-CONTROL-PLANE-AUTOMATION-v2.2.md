# AI1 Control Plane v2.2 — Automation Increment

This increment makes the task-state machine executable and CI-verifiable.

## Enforcement

`scripts/governance_state_gate.py` rejects invalid state transitions and prevents non-AI1 actors from entering `AUDITING`, `INTEGRATING`, `ACCEPTED`, `REJECTED`, or `ABORTED`.

`test_governance_state_gate.py` exercises valid worker/AI1 transitions and negative unauthorized transitions.

The existing Scope Gate remains the first CI gate. This state gate is an additional control-plane check.

## Important boundary

This increment does not yet mutate GitHub PR labels or task records automatically. It verifies the control-plane transition contract. The next increment can connect these transitions to GitHub events/API while preserving AI1 authority.
