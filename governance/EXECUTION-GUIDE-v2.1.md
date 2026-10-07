# Parallel Agent Governance v2.1 — Execution Guide

## Purpose

v2.0 defines the governance model. v2.1 adds the first executable enforcement layer.

The baseline tag `governance-v2.0` remains unchanged.

## Required task manifest

Every governed worker task must carry a real `.agent/task.json` manifest.

The manifest freezes:
- task_id
- agent
- base_commit
- READ_SET
- WRITE_SET
- FORBIDDEN_SET
- shared_interfaces
- acceptance gates

Use `.agent/task-template.json` as the starting template.

## Scope Gate

Run:

```bash
python scripts/governance_gate.py \
  --manifest .agent/task.json \
  --base <BASE_COMMIT> \
  --head <HEAD_COMMIT>
```

The gate fails when:
1. the manifest is invalid;
2. the task base does not equal the supplied base commit;
3. a changed file is outside WRITE_SET;
4. a changed file matches FORBIDDEN_SET.

## CI enforcement

`.github/workflows/governance-gate.yml` runs the Scope Gate on pull requests targeting `main`.

A worker PR therefore cannot pass the governance gate unless its declared scope matches its actual changed files.

## Responsibility

This automation does not replace AI1.

AI1 remains responsible for:
- dependency resolution;
- Shared Interface Lock;
- Conflict Gate;
- Test Gate;
- integration;
- final acceptance.

v2.1 automates the mechanical part first and leaves semantic decisions under AI1 control.

## Failure handling

A failed Scope Gate means the task is not ready for integration.

AI1 must either:
- narrow the worker changes;
- update the authorized task manifest before the work proceeds; or
- reject/abort the task.

Do not weaken the gate merely to make a PR pass.
