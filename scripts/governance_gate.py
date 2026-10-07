#!/usr/bin/env python3
"""Executable Scope Gate for Parallel Agent Governance v2.2.

The Scope Gate is a MECHANICAL scope validator only. Dependency resolution,
the Conflict Gate, the Integration Gate, final acceptance and production
approval remain AI1-owned procedural authorities and are intentionally NOT
implemented here.

v2.2 changes (AI3-GOV-V22-GATE-IMPLEMENT-001, per AI1-approved design):
- D1: the workflow resolves the PR base/head SHA explicitly and fails
  closed; this script also rejects empty --base/--head.
- D2: safe path normalization -- backslashes become slashes, only true
  leading "./" segments are stripped, dot-prefixed names such as ".agent"
  are preserved; absolute paths and ".." traversal are rejected fail-closed.
- D3: component-aware pattern semantics. "*" matches within exactly one
  path component and never crosses "/". "**" matches any number of whole
  components. Everything else matches literally. fnmatch is no longer used.
- Deny-wins: a FORBIDDEN_SET match fails the gate even when the same file
  also matches WRITE_SET; a manifest whose write_set and forbidden_set
  overlap is rejected at load time as self-contradictory.
- Self-exemption is narrowed to the task's own exact manifest path, and
  only from the WRITE_SET check. No blanket ".agent/**" exemption exists.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
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
MANIFEST_DIR_PREFIX = ".agent/tasks/"
MANIFEST_SUFFIX = ".json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def normalize(path: str) -> str:
    """Make a path match-ready.

    Backslashes become slashes; only true leading "./" segments are
    removed (repeatedly). Dot-prefixed components such as ".agent" are
    preserved. No other transformation is applied.
    """
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_safe_relative(path: str) -> bool:
    """True for repo-relative paths usable as manifest patterns/paths.

    Rejects empty paths, absolute paths (POSIX leading "/", UNC "//",
    Windows drive letters) and any ".." traversal component. Dot-prefixed
    components (".agent") are legal.
    """
    if not path:
        return False
    if path.startswith("/"):
        return False
    if len(path) >= 2 and path[0].isalpha() and path[1] == ":":
        return False
    if any(part == ".." for part in path.split("/")):
        return False
    return True


def _segment_to_regex(segment: str) -> str:
    return "".join("[^/]*" if ch == "*" else re.escape(ch) for ch in segment)


@functools.lru_cache(maxsize=None)
def _pattern_regex(pattern: str) -> str:
    """Translate one component-aware glob into an anchored regex.

    "*" matches within exactly one path component ("[^/]*"), so it never
    crosses "/". A bare "**" pattern matches everything. A "**" segment in
    the middle matches zero or more whole components; a trailing "**"
    additionally matches the final component.
    """
    if pattern == "**":
        return "^.*$"
    segments = pattern.split("/")
    parts: list[str] = []
    last = len(segments) - 1
    for index, segment in enumerate(segments):
        if segment == "**":
            if index == last:
                parts.append("(?:[^/]+/)*[^/]+")
            else:
                parts.append("(?:[^/]+/)*")
        else:
            parts.append(_segment_to_regex(segment))
            if index != last:
                parts.append("/")
    return "^" + "".join(parts) + "$"


def path_matches(path: str, pattern: str) -> bool:
    return re.fullmatch(_pattern_regex(pattern), path) is not None


def matches(path: str, patterns: list[str]) -> bool:
    normalized = normalize(path)
    return any(path_matches(normalized, normalize(pattern)) for pattern in patterns)


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
    files = [normalize(line) for line in result.stdout.splitlines() if line.strip()]
    unsafe = sorted({path for path in files if not is_safe_relative(path)})
    if unsafe:
        fail(f"unsafe changed path(s) rejected (absolute or traversal): {unsafe}")
    return files


def select_manifest(changed: list[str], explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            fail(f"manifest not found: {path}")
        return path

    candidates = [
        Path(path)
        for path in changed
        if path.startswith(MANIFEST_DIR_PREFIX) and path.endswith(MANIFEST_SUFFIX)
    ]
    if len(candidates) != 1:
        fail(
            "exactly one PR-local task manifest is required under "
            ".agent/tasks/*.json; found "
            + str(len(candidates))
        )
    return candidates[0]


def _validate_pattern_entries(data: dict[str, Any]) -> None:
    for key in ("write_set", "forbidden_set"):
        for entry in data[key]:
            if not isinstance(entry, str):
                fail(f"{key} entries must be strings; got {entry!r}")
            if not is_safe_relative(normalize(entry)):
                fail(
                    f"{key} entry must be a safe relative path "
                    f"(no absolute paths, no '..' traversal): {entry!r}"
                )


def _write_forbidden_overlap(data: dict[str, Any]) -> list[str]:
    """Report pattern pairs where a write_set entry and a forbidden_set
    entry can describe the same path (checked in both directions)."""
    writes = [normalize(entry) for entry in data["write_set"]]
    forbiddens = [normalize(entry) for entry in data["forbidden_set"]]
    hits = []
    for write_entry in writes:
        for forbidden_entry in forbiddens:
            if path_matches(write_entry, forbidden_entry) or path_matches(
                forbidden_entry, write_entry
            ):
                hits.append(f"{write_entry!r} overlaps {forbidden_entry!r}")
    return hits


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

    _validate_pattern_entries(data)

    overlap = _write_forbidden_overlap(data)
    if overlap:
        fail(
            "manifest is self-contradictory: write_set and forbidden_set "
            "overlap (deny-wins would reject every such path): "
            + "; ".join(overlap)
        )

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
    write_set = [normalize(pattern) for pattern in manifest["write_set"]]
    forbidden_set = [normalize(pattern) for pattern in manifest["forbidden_set"]]
    manifest_name = normalize(str(manifest_path))

    # v2.2 deny-wins order:
    # 1. protected-boundary authorization: the current manifest contract has
    #    no field expressing an always-protected-boundary exception, so no
    #    exception is applied (fail-closed; reported to AI1, not invented).
    # 2. forbidden_set: any match fails the gate even if write_set matches.
    #    This includes the manifest's own path.
    forbidden = [path for path in files if matches(path, forbidden_set)]

    # 3. write_set: everything outside the write set fails, except the
    #    task's own exact manifest path (self-exemption; no blanket
    #    ".agent/**" or other-manifest exemption).
    out_of_scope = [
        path
        for path in files
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
    parser = argparse.ArgumentParser(description="Run governance v2.2 Scope Gate.")
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    if not args.base or not args.head:
        fail("both --base and --head must be non-empty (fail closed)")

    print(f"SCOPE DIFF: {args.base}...{args.head}")
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
