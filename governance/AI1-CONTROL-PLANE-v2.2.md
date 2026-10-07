# AI1 Control Plane v2.2 — Executable State Machine

## States

`PLANNED -> ALLOCATED -> READY_TO_START -> IN_PROGRESS -> BLOCKED/READY_FOR_AUDIT -> AUDITING -> INTEGRATING -> ACCEPTED`

Failure states: `REJECTED`, `ABORTED`.

## AI1 authority

Only AI1 may transition a task into `AUDITING`, `INTEGRATING`, or `ACCEPTED`.
Only AI1 may grant or release a Shared Interface Lock.

## Control-plane record

Each active task record contains: task_id, agent, base_commit, state, write_set, shared_interfaces, interface locks, and audit events.

## Valid transitions

| From | To | Authority |
|---|---|---|
| PLANNED | ALLOCATED | AI1 |
| ALLOCATED | READY_TO_START | AI1 after Scope + Conflict + Lock gates |
| READY_TO_START | IN_PROGRESS | Worker |
| IN_PROGRESS | BLOCKED | Worker / AI1 |
| IN_PROGRESS | READY_FOR_AUDIT | Worker |
| READY_FOR_AUDIT | AUDITING | AI1 |
| AUDITING | INTEGRATING | AI1 |
| INTEGRATING | ACCEPTED | AI1 |
| any active state | REJECTED | AI1 |
| any non-final state | ABORTED | AI1 |

## Guard rules

`READY_TO_START` requires frozen `base_commit`, valid task manifest, Scope Gate PASS, Conflict Gate PASS, and an AI1-owned `LOCKED` record for every declared shared interface.

A state transition without its guard must fail CI.

## Control-plane principle

Worker branches contain task work. The control plane records allocation and authorization. Worker code must not self-authorize a lock or final acceptance.
