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

## Lifecycle
UNLOCKED -> REQUESTED -> LOCKED -> AUDITING -> UNLOCKED

A worker requesting a shared-interface change must provide:
- task_id
- target
- reason
- proposed change
- impacted agents/tasks
- compatibility plan

AI1 grants or rejects the lock. Workers never acquire a lock by editing first.
