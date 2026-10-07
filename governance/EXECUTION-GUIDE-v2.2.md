# Parallel Agent Governance v2.2 — Executable Conflict & Interface Gates

## Purpose

v2.2 extends v2.1 with two executable controls:

1. **Conflict Gate** — rejects overlapping `WRITE_SET` declarations among active tasks.
2. **Shared Interface Lock** — rejects a worker that declares a shared-interface change unless AI1 has explicitly locked that interface for the same task.

v2.0 and v2.1 remain frozen baselines. This document describes v2.2 only.

## Active Task Registry

`.agent/active-tasks.json` is AI1-controlled state.

It freezes the allocation base commit and records active task IDs, agents, write sets, shared interfaces, and explicit interface locks.

Worker PRs must not edit the registry. AI1 updates it when allocating, locking, auditing, or releasing parallel work.

## Conflict Gate

For the current PR manifest, the gate compares `write_set` against every other active task. A conflict is reported when patterns are equal, glob-match each other, or one `/**` pattern contains the other path. A conflict blocks the PR; AI1 must resolve the allocation.

## Shared Interface Lock

For every interface in `shared_interfaces`, the registry must contain the same interface with `owner_task` equal to the current task and `status` equal to `LOCKED`. Missing lock, wrong owner, or another status fails the gate.

Lifecycle: `UNLOCKED -> REQUESTED -> LOCKED -> AUDITING -> UNLOCKED`

Only AI1 may grant the transition into `LOCKED`.

## PR enforcement

`.github/workflows/governance-gate.yml` runs the v2.1 Scope Gate, then the v2.2 Conflict Gate and Shared Interface Lock check.

Implementation: `scripts/governance_conflict_gate.py`.

## Self-test

Run locally:

    python scripts/test_governance_v22.py

The self-test covers disjoint write sets, overlapping write sets, an interface without a lock, and an AI1-authorized lock.

## AI1 allocation procedure

1. Freeze the common `base_commit`.
2. Add each active task to `.agent/active-tasks.json`.
3. Check that all `write_set`s are disjoint.
4. For a shared-interface change, create a lock owned by exactly one task.
5. Workers branch from the frozen base.
6. Workers include their PR-local task manifest.
7. CI enforces Scope + Conflict + Interface Lock.
8. AI1 audits and later releases the lock.

The registry is control-plane state, not worker-owned code.
