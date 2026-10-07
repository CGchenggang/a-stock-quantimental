# Worktree / Branch Rules v1

## Layout
- Main worktree: project-main
- AI2 worktree: project-ai2
- AI3 worktree: project-ai3

## Branches
- main
- parallel/AI2/<TASK-ID>
- parallel/AI3/<TASK-ID>

Both worker branches must start from the same approved main base commit.

## Isolation
- Never share a working directory between agents.
- AI2/AI3 never edit main.
- AI2/AI3 never rebase or merge the other worker branch.
- Shared interfaces require AI1 authorization.

## Lifecycle
1. AI1 freezes BASE_COMMIT.
2. Create both worker branches/worktrees from BASE_COMMIT.
3. Run workers independently.
4. AI1 compares each branch with BASE_COMMIT.
5. AI1 performs overlap and semantic conflict audit.
6. AI1 integrates and tests.
7. AI1 accepts or rejects.

## Cleanup
Worker worktrees/branches are retained until AI1 records the integration decision.
