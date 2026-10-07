# Parallel Agent Governance Protocol v1

## Roles
- AI1: Chief Agent, task allocator, integrator, independent final acceptor.
- AI2/ZCODE-A2: Worker A.
- AI3/ZCODE-A3: Worker B.

## Core flow
AI1 allocates two independent tasks -> AI2 and AI3 execute in isolated worktrees/branches -> both report READY_FOR_AI1_AUDIT -> AI1 performs integration audit -> AI1 integrates -> AI1 independently accepts -> main.

> Vocabulary note (v2.2 addendum §4): `READY_FOR_AI1_AUDIT` in this v1
> protocol is a deprecated display alias of the canonical state
> `READY_FOR_AUDIT`. The canonical 11-state vocabulary is defined in
> `governance/TASK-STATE-MACHINE-v2.md`.

## Hard rules
1. AI2/AI3 never modify main directly.
2. Each worker uses a dedicated worktree.
3. Branches use `parallel/AI2/<TASK-ID>` and `parallel/AI3/<TASK-ID>`.
4. Every task has READ_SET, WRITE_SET and FORBIDDEN_SET.
5. Shared interfaces, schemas, APIs, configs and dependency contracts require AI1 authorization when changed.
6. AI1 is the only authority for final integration and acceptance.
7. Worker READY does not mean ACCEPTED.
8. Workers do not rebase against each other.

## Completion
Workers report task ID, base commit, commit, changed files, tests, results, risks and limitations. Final acceptance belongs only to AI1.
