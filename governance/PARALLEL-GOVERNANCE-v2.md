# Parallel Agent Governance Protocol v2

v2 extends v1 with executable coordination gates while preserving worker isolation.

## 1. Execution State Machine
Task states:
PLANNED -> ALLOCATED -> READY_TO_START -> IN_PROGRESS -> BLOCKED/READY_FOR_AUDIT -> AUDITING -> INTEGRATING -> ACCEPTED
Failure states: REJECTED, ABORTED.

Only AI1 may transition a task to AUDITING, INTEGRATING or ACCEPTED.

## 2. Task Dependency Graph
Each task declares:
- task_id
- depends_on
- blocks
- shared_interfaces
- write_set

A task may start only when every hard dependency is SATISFIED. AI1 owns dependency resolution.

## 3. Shared Interface Lock
Any change to a declared shared interface requires an AI1 lock:
LOCKED -> one authorized worker may modify -> audit -> UNLOCKED.
Workers may read locked interfaces but may not modify them.

## 4. Scope Gate
For every worker commit:
changed_files must be a subset of WRITE_SET.
Violations cause REJECTED until AI1 explicitly reauthorizes the scope.

## 5. Conflict Gate
AI1 evaluates:
- file overlap
- API/signature overlap
- schema/config overlap
- dependency/version overlap
- behavioral/runtime assumptions
No automatic conflict resolution is performed by workers.

## 6. Test Gate
A worker cannot become READY_FOR_AUDIT unless required tests pass or AI1 records an explicit exception.
AI1 reruns relevant tests after integration.

## 7. Integration Gate
Integration requires:
- both workers READY_FOR_AUDIT
- scope gate PASS
- conflict gate PASS or documented resolution
- test gate PASS
- no unresolved BLOCKED task
- AI1 audit decision APPROVED

## 8. GitHub Gate
Worker branches may be pushed to GitHub, but main remains protected by process. Recommended PR labels:
agent:ai2, agent:ai3, gate:pending, gate:approved, gate:rejected.
Only AI1 closes the governance cycle.

## 9. Recovery
A blocked worker does not change another worker's branch. AI1 may reassign, narrow scope, or abort the task. A failed integration returns to AUDITING or BLOCKED.

## 10. Source of Truth
Governance rules live in /governance and are versioned in GitHub.
Runtime state, locks, task queues and ephemeral status remain local and are not committed unless a later audit artifact is intentionally published.
