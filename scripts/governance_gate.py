#!/usr/bin/env python3
"""Executable Scope Gate for Parallel Agent Governance v2.1."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ALLOWED_AGENTS = {"AI1", "AI2", "AI3"}
REQUIRED_MANIFEST_KEYS = {
    "task_id",
    "agent",
    "base_commit",
    "depends_on",
    "blocks",
    "read_set",
    "write_set",
    "forbidden_set",
    "shared_interfaces",
    "acceptance",
}
REQUIRED_GATES = {"scope", "conflict", "test"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def matches(path: str, patterns: list[str]) -> bool:
    path = normalize(path)
    for raw_pattern in patterns:
        pattern = normalize(raw_pattern)
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if pattern.endswith("/**") and (
            path == pattern[:-3].rstrip("/")
            or path.startswith(pattern[:-2])
        ):
            return True
    return False


def changed_files(base: str, head: str) -> list[str]:
    command = ["git", "diff", "--name-only", "--diff-filter=ACMRD", f"{base}...{head}"]
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        fail(f"git diff failed: {exc.stderr.strip()}")
    return [normalize(line) for line in result.stdout.splitlines() if line.strip()]


def select_manifest(changed: list[str], explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            fail(f"manifest not found: {path}")
        return path

    candidates = [
        Path(path)
        for path in changed
        if path.startswith(".agent/tasks/") and path.endswith(".json")
    ]
    if len(candidates) != 1:
        fail(
            "exactly one PR-local task manifest is required under "
            ".agent/tasks/*.json; found "
            + str(len(candidates))
        )
    return candidates[0]


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"manifest not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON manifest: {exc}")

    if not isinstance(data, dict):
        fail("manifest root must be an object")

    missing = REQUIRED_MANIFEST_KEYS - set(data)
    if missing:
        fail(f"manifest missing keys: {sorted(missing)}")

    if data["agent"] not in ALLOWED_AGENTS:
        fail(f"agent must be one of {sorted(ALLOWED_AGENTS)}")

    if not isinstance(data["write_set"], list) or not data["write_set"]:
        fail("write_set must be a non-empty list")

    if not isinstance(data["forbidden_set"], list):
        fail("forbidden_set must be a list")

    acceptance = data["acceptance"]
    if not isinstance(acceptance, dict):
        fail("acceptance must be an object")

    gates = set(acceptance.get("gates", []))
    missing_gates = REQUIRED_GATES - gates
    if missing_gates:
        fail(f"acceptance.gates missing: {sorted(missing_gates)}")

    if not data["base_commit"] or data["base_commit"] == "FREEZE_TO_REAL_COMMIT_SHA":
        fail("base_commit must be frozen to a real commit SHA")

    return data


def run_scope_gate(manifest: dict[str, Any], files: list[str], manifest_path: Path) -> int:
    write_set = [normalize(p) for p in manifest["write_set"]]
    forbidden_set = [normalize(p) for p in manifest["forbidden_set"]]

    forbidden = [path for path in files if matches(path, forbidden_set)]
    manifest_name = normalize(str(manifest_path))
    out_of_scope = [
        path for path in files
        if path != manifest_name and not matches(path, write_set)
    ]

    if forbidden:
        print("FORBIDDEN_SET violations:")
        for path in forbidden:
            print(f"  - {path}")

    if out_of_scope:
        print("WRITE_SET violations:")
        for path in out_of_scope:
            print(f"  - {path}")

    if forbidden or out_of_scope:
        print("FAIL: Scope Gate")
        return 1

    print("PASS: Scope Gate")
    for path in files:
        print(f"  + {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run governance v2.1 Scope Gate.")
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    files = changed_files(args.base, args.head)
    manifest_path = select_manifest(files, args.manifest)
    manifest = load_manifest(manifest_path)

    print(f"TASK_ID: {manifest['task_id']}")
    print(f"AGENT: {manifest['agent']}")
    print(f"MANIFEST: {manifest_path}")
    print(f"BASE_COMMIT: {manifest['base_commit']}")

    if normalize(args.base) != normalize(manifest["base_commit"]):
        fail(
            "CI base commit does not match manifest base_commit; "
            "the task base is not frozen."
        )

    return run_scope_gate(manifest, files, manifest_path)


if __name__ == "__main__":
    sys.exit(main())
