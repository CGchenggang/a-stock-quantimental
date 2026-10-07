# Task Dependency Schema v2

Each task contract must define:

```yaml
task_id:
agent:
base_commit:
depends_on: []
blocks: []
read_set: []
write_set: []
shared_interfaces: []
acceptance:
  tests: []
  gates: [scope, conflict, test]
```

Rules:
1. Empty depends_on means the task is eligible after allocation.
2. A task with unmet hard dependencies cannot start.
3. Shared-interface dependencies must be explicit.
4. AI1 is the authority for dependency overrides.
5. Dependency cycles are invalid and block execution.
