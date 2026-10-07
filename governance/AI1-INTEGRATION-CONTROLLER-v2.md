# AI1 Integration Controller v2

## Before start
1. Freeze BASE_COMMIT.
2. Build task dependency graph.
3. Allocate disjoint WRITE_SETs.
4. Identify shared interfaces.
5. Prepare isolated worker worktrees.

## During execution
Track each task state.
If a worker requests out-of-scope/shared-interface modification, stop that task and decide whether to reauthorize or reject.

## Before integration
Require:
- dependency satisfaction
- two worker READY_FOR_AUDIT states
- Scope Gate PASS
- Conflict Gate PASS
- Test Gate PASS

## Integration
AI1 integrates one branch at a time or resolves both into a controlled integration result. Never ask workers to merge each other.

## After integration
Run independent regression/build checks. Only then mark ACCEPTED and promote to main.

## Audit record
Record base commit, worker commits, changed files, gate results, conflict decisions, tests, integration commit and acceptance decision.
