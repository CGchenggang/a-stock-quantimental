#!/usr/bin/env python3
"""Governance v2.2 PR Control-Plane Gate.

Read-only gate: validates that a PR's task manifest is authorized by the
AI1-controlled active-task registry before READY_TO_START.
"""

import argparse
import json
import sys
from pathlib import Path


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot load {path}: {exc}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--registry", required=True)
    args = p.parse_args()

    manifest = load(args.manifest)
    registry = load(args.registry)

    task_id = manifest.get("task_id")
    base = manifest.get("base_commit")
    agent = manifest.get("agent")
    if not task_id or not base or not agent:
        fail("manifest must contain task_id, base_commit and agent")

    if base != registry.get("base_commit"):
        fail("manifest base_commit does not match AI1 control-plane base_commit")

    tasks = registry.get("tasks", [])
    matches = [t for t in tasks if t.get("task_id") == task_id]
    if len(matches) != 1:
        fail(f"task {task_id} is not uniquely registered by AI1")

    record = matches[0]
    if record.get("agent") != agent:
        fail(f"task {task_id} is registered to {record.get('agent')}, not {agent}")

    if record.get("state") != "READY_TO_START":
        fail(f"task {task_id} state is {record.get('state')!r}; expected READY_TO_START")

    manifest_writes = set(manifest.get("write_set", []))
    registry_writes = set(record.get("write_set", []))
    if manifest_writes != registry_writes:
        fail("manifest WRITE_SET differs from AI1 allocation")

    interfaces = set(manifest.get("shared_interfaces", []))
    locks = registry.get("interface_locks", [])
    for interface in interfaces:
        valid = any(
            lock.get("interface") == interface
            and lock.get("owner_task") == task_id
            and lock.get("status") == "LOCKED"
            for lock in locks
        )
        if not valid:
            fail(f"shared interface {interface} is not AI1-LOCKED for {task_id}")

    print(f"PASS: PR Control Plane authorized {task_id} ({agent})")
    print("PASS: task state READY_TO_START")
    print("PASS: WRITE_SET matches AI1 allocation")
    print("PASS: shared interfaces are AI1-authorized")


if __name__ == "__main__":
    main()
