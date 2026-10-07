#!/usr/bin/env python3
"""Conflict Gate and Shared Interface Lock enforcement for Governance v2.2."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def normalize(value: str) -> str:
    return value.replace("\\", "/").lstrip("./").rstrip("/")


def pattern_overlap(a: str, b: str) -> bool:
    a = normalize(a)
    b = normalize(b)
    if a == b or fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
        return True
    if a.endswith("/**") and b.startswith(a[:-2]):
        return True
    if b.endswith("/**") and a.startswith(b[:-2]):
        return True
    return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"JSON root must be an object: {path}")
    return data


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("version") != "2.2":
        fail("active task registry version must be 2.2")
    if not registry.get("base_commit"):
        fail("active task registry must freeze base_commit")
    if not isinstance(registry.get("tasks"), list):
        fail("active task registry tasks must be a list")
    if not isinstance(registry.get("interface_locks", []), list):
        fail("interface_locks must be a list")

    ids: set[str] = set()
    for task in registry["tasks"]:
        if not isinstance(task, dict):
            fail("each active task must be an object")
        for key in ("task_id", "agent", "write_set", "shared_interfaces"):
            if key not in task:
                fail(f"active task missing key: {key}")
        task_id = task["task_id"]
        if task_id in ids:
            fail(f"duplicate active task_id: {task_id}")
        ids.add(task_id)
        if not isinstance(task["write_set"], list):
            fail(f"{task_id}.write_set must be a list")
        if not isinstance(task["shared_interfaces"], list):
            fail(f"{task_id}.shared_interfaces must be a list")

    for lock in registry["interface_locks"]:
        if not isinstance(lock, dict):
            fail("each interface lock must be an object")
        for key in ("interface", "owner_task", "status"):
            if key not in lock:
                fail(f"interface lock missing key: {key}")
        if lock["status"] not in {"UNLOCKED", "REQUESTED", "LOCKED", "AUDITING"}:
            fail(f"invalid interface lock status: {lock['status']}")


def run_gates(current: dict[str, Any], registry: dict[str, Any]) -> int:
    validate_registry(registry)

    current_id = current["task_id"]
    current_write = current.get("write_set", [])
    current_interfaces = current.get("shared_interfaces", [])

    if not isinstance(current_write, list) or not current_write:
        fail("current task write_set must be a non-empty list")
    if not isinstance(current_interfaces, list):
        fail("current task shared_interfaces must be a list")

    conflicts: list[str] = []
    interface_conflicts: list[str] = []
    lock_violations: list[str] = []

    active_by_id = {task["task_id"]: task for task in registry["tasks"]}

    for other in registry["tasks"]:
        if other["task_id"] == current_id:
            continue
        for mine in current_write:
            for theirs in other["write_set"]:
                if pattern_overlap(mine, theirs):
                    conflicts.append(
                        f"WRITE_SET: {current_id}:{mine} <-> "
                        f"{other['task_id']}:{theirs}"
                    )
        for mine in current_interfaces:
            for theirs in other["shared_interfaces"]:
                if normalize(mine) == normalize(theirs):
                    interface_conflicts.append(
                        f"SHARED_INTERFACE: {current_id}:{mine} <-> "
                        f"{other['task_id']}:{theirs}"
                    )

    locks = {
        normalize(lock["interface"]): lock
        for lock in registry["interface_locks"]
    }
    for interface in current_interfaces:
        lock = locks.get(normalize(interface))
        if lock is None:
            lock_violations.append(
                f"{interface}: no lock exists; AI1 authorization is required"
            )
        elif lock["status"] != "LOCKED":
            lock_violations.append(
                f"{interface}: lock status is {lock['status']}, expected LOCKED"
            )
        elif lock["owner_task"] != current_id:
            lock_violations.append(
                f"{interface}: lock owner is {lock['owner_task']}, not {current_id}"
            )
        elif lock["owner_task"] not in active_by_id:
            lock_violations.append(
                f"{interface}: lock owner task is not active"
            )

    if conflicts:
        print("WRITE_SET conflicts:")
        for item in conflicts:
            print(f"  - {item}")
    if interface_conflicts:
        print("Shared Interface conflicts:")
        for item in interface_conflicts:
            print(f"  - {item}")
    if lock_violations:
        print("Shared Interface Lock violations:")
        for item in lock_violations:
            print(f"  - {item}")

    if conflicts or interface_conflicts or lock_violations:
        print("FAIL: Conflict Gate / Shared Interface Lock")
        return 1

    print("PASS: Conflict Gate")
    print("PASS: Shared Interface Lock")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--registry", default=".agent/active-tasks.json")
    args = parser.parse_args()

    current = load_json(Path(args.manifest))
    registry = load_json(Path(args.registry))

    if not current.get("task_id"):
        fail("current task_id is required")
    if current.get("base_commit") != registry.get("base_commit"):
        fail("current task base_commit does not match active-task registry base_commit")

    print(f"TASK_ID: {current['task_id']}")
    print(f"BASE_COMMIT: {current['base_commit']}")
    return run_gates(current, registry)


if __name__ == "__main__":
    sys.exit(main())
