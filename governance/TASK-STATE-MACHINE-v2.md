# Task State Machine v2

| State | Meaning | Allowed transition owner |
|---|---|---|
| PLANNED | Task defined | AI1 |
| ALLOCATED | Contract assigned | AI1 |
| READY_TO_START | Workspace prepared | AI1 |
| IN_PROGRESS | Worker executing | Worker |
| BLOCKED | Cannot safely continue | Worker/AI1 |
| READY_FOR_AUDIT | Worker complete | Worker |
| AUDITING | AI1 verification | AI1 |
| INTEGRATING | AI1 applying changes | AI1 |
| ACCEPTED | Final acceptance | AI1 |
| REJECTED | Failed gate | AI1 |
| ABORTED | Cancelled | AI1 |

Workers cannot self-accept, self-integrate or clear another worker's BLOCKED/REJECTED state.
