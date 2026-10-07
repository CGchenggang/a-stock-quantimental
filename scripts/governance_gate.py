#!/usr/bin/env python3
"""Executable Scope Gate for Parallel Agent Governance v2.2 (rework).

Implements AI3-GOV-V22-GATE-REWORK-001 against the v2.2 contract:
- PARALLEL-GOVERNANCE-v2.2-ADDENDUM (AI2-GOV-V22-ADDENDUM-IMPLEMENT-001):
  section 1 deny-wins FORBIDDEN_SET, section 2 path pattern semantics,
  section 3 manifest self-exemption, section 4 canonical state vocabulary,
  section 8 Always-Protected Boundary.
- AI3-GOV-V22-GATE-DESIGN-001: safe normalization, component-aware
  matching, base/head acquisition, gate boundaries.

The Scope Gate is a MECHANICAL validator only. Dependency resolution, the
Conflict Gate, the Integration Gate, final acceptance and production
approval remain AI1-owned procedural authorities and are intentionally NOT
implemented here.
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

# v2.2 manifest contract (AI3-GOV-V22-GATE-REWORK-001 section 5).
REQUIRED_MANIFEST_KEYS = {
    "task_id",
    "agent",
    "zcode_agent",
    "base_commit",
    "depends_on",
    "blocks",
    "read_set",
    "write_set",
    "forbidden_set",
    "shared_interfaces",
    "authorization",
    "acceptance",
    "status",
}
REQUIRED_AUTHORIZATION_KEYS = {
    "human_required": bool,
    "human_authorization_ref": str,
    "ai1_authorized": bool,
    "protected_boundary_exception": bool,
}
REQUIRED_GATES = {"scope", "conflict", "test"}
MANIFEST_DIR_PREFIX = ".agent/tasks/"
MANIFEST_SUFFIX = ".json"

# Canonical task-state vocabulary (TASK-STATE-MACHINE-v2, restated by
# PARALLEL-GOVERNANCE-v2.2-ADDENDUM section 4). No other state exists.
CANONICAL_STATES = frozenset(
    {
        "PLANNED",
        "ALLOCATED",
        "READY_TO_START",
        "IN_PROGRESS",
        "BLOCKED",
        "READY_FOR_AUDIT",
        "AUDITING",
        "INTEGRATING",
        "ACCEPTED",
        "REJECTED",
        "ABORTED",
    }
)

# Always-Protected Boundary default coverage
# (PARALLEL-GOVERNANCE-v2.2-ADDENDUM section 8): ordinary workers cannot
# modify these regardless of manifest content, unless the manifest carries a
# valid protected_boundary_exception. AI1-designated production schema/config
# authorities have no machine-readable registry yet and are therefore not
# enumerable here (reported as a limitation).
PROTECTED_BOUNDARY_PATTERNS = (
    "governance/**",
    ".github/workflows/**",
    ".agent/**",
    "scripts/governance_*.py",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def normalize(path: str) -> str:
    """Match-ready form: backslashes become slashes; only true leading
    "./" segments are removed. Meaningful leading dots (".agent") and all
    other content are preserved."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_safe_relative(path: str) -> bool:
    """True for repo-relative paths: rejects empty paths, absolute paths
    (POSIX "/", UNC "//", Windows drive letters) and ".." traversal.
    Dot-prefixed components are legal."""
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
    """Translate one valid v2.2 pattern into an anchored regex.

    "*" matches within exactly one path component and never crosses "/".
    A trailing "**" matches everything under the preceding directory.
    (Load-time form validation rejects every other "**" placement, so the
    translator only ever sees the three valid forms; the middle-** branch
    is kept only as unreachable defense.)
    """
    if pattern == "**":  # unreachable: rejected by _validate_pattern_form
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


def matches(path: str, patterns) -> bool:
    normalized = normalize(path)
    return any(path_matches(normalized, normalize(pattern)) for pattern in patterns)


def validate_pattern_form(pattern: str, field: str) -> None:
    """v2.2 section 2: only three pattern forms are valid.

    exact:      foo/bar.py
    single '*': dir/*.py      ('*' inside components is allowed)
    trailing:   dir/**        (the ONLY legal placement of '**')

    '**/file.py', 'a/**/file.py', 'a/**/b/**' and bare '**' are invalid and
    fail closed at manifest load time.
    """
    segments = pattern.split("/")
    if any(segment == "" for segment in segments):
        fail(f"{field} pattern has an empty path component: {pattern!r}")
    recursive_positions = [i for i, seg in enumerate(segments) if seg == "**"]
    if not recursive_positions:
        return
    if len(recursive_positions) > 1:
        fail(
            f"{field} pattern carries multiple '**' segments; only one "
            f"trailing '**' is valid: {pattern!r}"
        )
    if recursive_positions[0] != len(segments) - 1:
        fail(
            f"{field} pattern carries '**' outside trailing position; only "
            f"'dir/**' is valid: {pattern!r}"
        )
    if len(segments) < 2:
        fail(f"{field} pattern is a bare '**'; use 'dir/**': {pattern!r}")


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
            normalized = normalize(entry)
            if not is_safe_relative(normalized):
                fail(
                    f"{key} entry must be a safe relative path "
                    f"(no absolute paths, no '..' traversal): {entry!r}"
                )
            validate_pattern_form(normalized, key)


def _validate_authorization(data: dict[str, Any]) -> None:
    authorization = data["authorization"]
    if not isinstance(authorization, dict):
        fail("authorization must be an object")
    for key, expected_type in REQUIRED_AUTHORIZATION_KEYS.items():
        if key not in authorization:
            fail(f"authorization missing key: {key}")
        value = authorization[key]
        if expected_type is str:
            if not isinstance(value, str) or not value.strip():
                fail(f"authorization.{key} must be a non-empty string")
        elif not isinstance(value, bool):
            fail(f"authorization.{key} must be a boolean")


def _write_forbidden_exact_duplicate(data: dict[str, Any]) -> list[str]:
    """Normalized patterns that appear verbatim in BOTH write_set and
    forbidden_set.

    v2.2 AI1 D4 ruling (B-V22-GATE-001 R3): load-time rejection is scoped
    to exact string-equality after normalization. Full pattern-intersection
    analysis (e.g. write 'src/a.py' with forbidden 'src/**' — where the
    write set is a subset of the forbidden set's language) is DEFERRED to
    v2.3. Overlapping-but-not-identical patterns load successfully; the
    runtime deny-wins rule still fails any concrete path that matches a
    forbidden pattern, regardless of whether it also matches a write
    pattern.
    """
    writes = {normalize(entry) for entry in data["write_set"]}
    forbiddens = {normalize(entry) for entry in data["forbidden_set"]}
    return sorted(writes & forbiddens)


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

    if not isinstance(data["zcode_agent"], str) or not data["zcode_agent"].strip():
        fail("zcode_agent must be a non-empty string")

    for key in ("depends_on", "blocks", "read_set", "shared_interfaces"):
        if not isinstance(data[key], list):
            fail(f"{key} must be a list")

    if not isinstance(data["write_set"], list) or not data["write_set"]:
        fail("write_set must be a non-empty list")

    if not isinstance(data["forbidden_set"], list):
        fail("forbidden_set must be a list")

    _validate_pattern_entries(data)
    _validate_authorization(data)

    duplicates = _write_forbidden_exact_duplicate(data)
    if duplicates:
        fail(
            "manifest is self-contradictory: write_set and forbidden_set "
            "contain identical patterns (deny-wins would reject every such "
            "path): " + "; ".join(repr(d) for d in duplicates)
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

    if not isinstance(data["status"], str) or data["status"] not in CANONICAL_STATES:
        fail(
            "status must be a canonical TASK-STATE-MACHINE-v2 state: "
            + ", ".join(sorted(CANONICAL_STATES))
        )

    return data


def protected_boundary_exception_valid(manifest: dict[str, Any]) -> bool:
    """PARALLEL-GOVERNANCE-v2.2-ADDENDUM section 8: a valid exception
    requires Human Authorization AND explicit AI1 designation."""
    authorization = manifest["authorization"]
    return (
        authorization["protected_boundary_exception"] is True
        and authorization["ai1_authorized"] is True
        and authorization["human_required"] is True
        and isinstance(authorization["human_authorization_ref"], str)
        and bool(authorization["human_authorization_ref"].strip())
    )


def run_scope_gate(manifest: dict[str, Any], files: list[str], manifest_path: Path) -> int:
    write_set = [normalize(pattern) for pattern in manifest["write_set"]]
    forbidden_set = [normalize(pattern) for pattern in manifest["forbidden_set"]]
    manifest_name = normalize(str(manifest_path))

    # Rework section 6, steps 1-3 — Always-Protected Boundary (addendum
    # section 8): the check applies to every changed file. A protected hit
    # without a valid exception FAILS closed; a valid exception only allows
    # the file to continue into the ordinary checks below.
    protected_hits = [path for path in files if matches(path, PROTECTED_BOUNDARY_PATTERNS)]
    exception_valid = protected_boundary_exception_valid(manifest)
    if protected_hits and not exception_valid:
        print("PROTECTED BOUNDARY violations (no authorized exception):")
        for path in protected_hits:
            print(f"  - {path}")
        print("FAIL: Scope Gate")
        return 1
    if protected_hits:
        print("PROTECTED BOUNDARY (authorized exception active):")
        for path in protected_hits:
            print(f"  ~ {path}")

    # Rework section 6, steps 4-5 — deny-wins FORBIDDEN_SET, then
    # WRITE_SET. The exact current manifest path is exempt from BOTH checks
    # (addendum section 3); any other manifest and every other file is not.
    forbidden = [
        path
        for path in files
        if path != manifest_name and matches(path, forbidden_set)
    ]
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

    sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
    if not args.base or not args.head:
        fail("both --base and --head must be non-empty (fail closed)")
    if not sha_pattern.fullmatch(args.base) or not sha_pattern.fullmatch(args.head):
        fail("--base and --head must be full 40-hex commit SHAs (fail closed)")

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
