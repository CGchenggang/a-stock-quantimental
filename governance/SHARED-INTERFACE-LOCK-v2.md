# Shared Interface Lock v2

## Lock targets

Examples:
- public APIs
- function/class signatures
- schemas
- config contracts
- database models
- message/data formats
- dependency versions

## Machine-readable control plane

v2.2 makes the lock executable through `.agent/active-tasks.json`.

A lock entry has:

    {
      "interface": "API:OrderService",
      "owner_task": "TASK-123",
      "status": "LOCKED"
    }

The current task may list `API:OrderService` in its `shared_interfaces` only when the registry contains a matching `LOCKED` entry owned by that task.

## Lifecycle

`UNLOCKED -> REQUESTED -> LOCKED -> AUDITING -> UNLOCKED`

A worker requesting a shared-interface change must provide task_id, target, reason, proposed change, impacted agents/tasks, and a compatibility plan.

AI1 grants or rejects the lock. Workers never acquire a lock by editing first.

## Enforcement

`scripts/governance_conflict_gate.py` enforces:

1. no duplicate active interface ownership;
2. no worker use of an interface without a lock;
3. no use of a lock owned by another task;
4. no use of a lock whose status is not `LOCKED`.

The CI gate fails before integration when any condition is violated.
