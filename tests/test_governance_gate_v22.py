"""Tests for the v2.2 executable governance Scope Gate.

Covers the AI1-approved v2.2 contract for AI3-GOV-V22-GATE-IMPLEMENT-001:
- D2: safe path normalization (backslash->slash, only true leading "./"
  stripped, dot-prefixed names such as ".agent" preserved, absolute paths
  and ".." traversal rejected fail-closed).
- D3: component-aware pattern semantics ("*" matches within exactly one
  path component and never crosses "/"; "**" matches any number of whole
  components; exact patterns match only themselves).
- Deny-wins FORBIDDEN_SET: a forbidden match fails even when WRITE_SET
  matches; manifests whose sets overlap are rejected at load time.
- Exact self-exemption of the task's own manifest path (no blanket
  ".agent/**" exemption, foreign manifests not exempt).
- PR-local manifest discovery, base_commit cross-check, fail-closed
  base/head handling.
- Boundary discipline: the Scope Gate holds no Conflict Gate, lock,
  acceptance or production-approval authority.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_SCRIPT = REPO_ROOT / "scripts" / "governance_gate.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "governance-gate.yml"


def _load_gate():
    spec = importlib.util.spec_from_file_location("governance_gate_v22", GATE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gg = _load_gate()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "gate-test@example.invalid")
    git(repo, "config", "user.name", "Gate Test")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    base = commit_all(repo, "seed")
    return repo, base


def put(repo: Path, relpath: str, content: str) -> None:
    target = repo / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_manifest(repo: Path, task_id: str, base_commit: str, **overrides) -> str:
    manifest = {
        "task_id": task_id,
        "agent": "AI3",
        "base_commit": base_commit,
        "depends_on": [],
        "blocks": [],
        "read_set": [],
        "write_set": [],
        "forbidden_set": [],
        "shared_interfaces": [],
        "acceptance": {"tests": [], "gates": ["scope", "conflict", "test"]},
    }
    manifest.update(overrides)
    relpath = f".agent/tasks/{task_id}.json"
    put(repo, relpath, json.dumps(manifest, indent=2))
    return relpath


def run_gate(repo: Path, base: str, head: str, manifest: str | None = None):
    command = [sys.executable, str(GATE_SCRIPT), "--base", base, "--head", head]
    if manifest is not None:
        command += ["--manifest", manifest]
    return subprocess.run(command, cwd=repo, capture_output=True, text=True)


def expect_fail(capsys, function, *args, fragment: str):
    with pytest.raises(SystemExit) as excinfo:
        function(*args)
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "FAIL:" in out
    assert fragment in out, out


def manifest_payload(**overrides) -> dict:
    payload = {
        "task_id": "T",
        "agent": "AI3",
        "base_commit": "0" * 40,
        "depends_on": [],
        "blocks": [],
        "read_set": [],
        "write_set": ["src/a.py"],
        "forbidden_set": ["governance/**"],
        "shared_interfaces": [],
        "acceptance": {"tests": [], "gates": ["scope", "conflict", "test"]},
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# D2: normalization and path safety
# ---------------------------------------------------------------------------

def test_normalize_preserves_dot_prefixed_names():
    assert gg.normalize(".agent/tasks/x.json") == ".agent/tasks/x.json"
    assert gg.normalize("./agent/x") == "agent/x"
    assert gg.normalize("./.agent/tasks/x.json") == ".agent/tasks/x.json"
    assert gg.normalize("a\\b\\c.py") == "a/b/c.py"
    assert gg.normalize("governance/audits/x.md") == "governance/audits/x.md"


def test_safe_relative_rejects_absolute_and_traversal():
    assert not gg.is_safe_relative("../x")
    assert not gg.is_safe_relative("a/../../x")
    assert not gg.is_safe_relative("/abs/x")
    assert not gg.is_safe_relative("//unc/share/x")
    assert not gg.is_safe_relative("C:\\abs\\x")
    assert not gg.is_safe_relative("")
    assert gg.is_safe_relative(".agent/tasks/x.json")
    assert gg.is_safe_relative("governance/audits/x.md")
    assert gg.is_safe_relative("src/astock_v2/x.py")


# ---------------------------------------------------------------------------
# D3: component-aware pattern semantics
# ---------------------------------------------------------------------------

def test_exact_pattern_matches_only_itself():
    assert gg.path_matches("foo/bar.py", "foo/bar.py")
    assert not gg.path_matches("foo/bar.pyx", "foo/bar.py")
    assert not gg.path_matches("foo/baz.py", "foo/bar.py")
    assert not gg.path_matches("x/foo/bar.py", "foo/bar.py")


def test_single_level_star_never_crosses_slash():
    assert gg.path_matches("governance/A.md", "governance/*.md")
    assert not gg.path_matches("governance/audits/A.md", "governance/*.md")
    assert not gg.path_matches("governance/audits/sub/A.md", "governance/*.md")


def test_recursive_doublestar_matches_any_depth():
    assert gg.path_matches("governance/x.md", "governance/**")
    assert gg.path_matches("governance/audits/x.md", "governance/**")
    assert gg.path_matches("governance/audits/deep/x.md", "governance/**")
    assert gg.path_matches("a/b/c.py", "**/c.py")
    assert gg.path_matches("c.py", "**/c.py")
    assert gg.path_matches("a/c.py", "a/**/c.py")
    assert gg.path_matches("a/x/y/c.py", "a/**/c.py")
    assert not gg.path_matches("b/a/c.py", "a/**/c.py")


def test_matches_list_helper():
    assert gg.matches("governance/x.md", ["governance/*.md", "docs/**"])
    assert gg.matches("docs/a/b.md", ["governance/*.md", "docs/**"])
    assert not gg.matches("governance/audits/x.md", ["governance/*.md"])


# ---------------------------------------------------------------------------
# manifest loading
# ---------------------------------------------------------------------------

def test_valid_manifest_loads(tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps(manifest_payload()), encoding="utf-8")
    data = gg.load_manifest(path)
    assert data["task_id"] == "T"


def test_missing_required_fields_rejected(tmp_path, capsys):
    payload = manifest_payload()
    del payload["forbidden_set"]
    path = tmp_path / "m.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    expect_fail(capsys, gg.load_manifest, path, fragment="'forbidden_set'")


def test_invalid_json_rejected(tmp_path, capsys):
    path = tmp_path / "m.json"
    path.write_text("{ not json", encoding="utf-8")
    expect_fail(capsys, gg.load_manifest, path, fragment="invalid JSON")


def test_traversal_pattern_rejected(tmp_path, capsys):
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(manifest_payload(forbidden_set=["../outside/**"])), encoding="utf-8"
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="safe relative path")


def test_absolute_pattern_rejected(tmp_path, capsys):
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(manifest_payload(write_set=["C:\\abs\\x"])), encoding="utf-8"
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="safe relative path")


def test_placeholder_base_commit_rejected(tmp_path, capsys):
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(manifest_payload(base_commit="FREEZE_TO_REAL_COMMIT_SHA")),
        encoding="utf-8",
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="frozen to a real commit SHA")


def test_write_forbidden_overlap_rejected_at_load(tmp_path, capsys):
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(
            manifest_payload(write_set=["src/a.py"], forbidden_set=["src/**"])
        ),
        encoding="utf-8",
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="self-contradictory")


def test_star_writeset_overlap_with_forbidden_rejected(tmp_path, capsys):
    # governance/*.md (write) overlaps governance/*.md (forbidden) exactly;
    # but governance/*.md (write) does NOT overlap governance/audits/*.md.
    path = tmp_path / "m.json"
    path.write_text(
        json.dumps(
            manifest_payload(
                write_set=["governance/*.md"],
                forbidden_set=["governance/*.md"],
            )
        ),
        encoding="utf-8",
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="self-contradictory")


def test_v21_shipped_manifest_still_loads():
    """Backward compatibility: the v2.1 manifest on main is valid under the
    v2.2 loader (its sets are disjoint under component-aware matching)."""
    shipped = REPO_ROOT / ".agent" / "tasks" / "GOV-V21-MANIFEST-FIX-001.json"
    data = gg.load_manifest(shipped)
    assert data["task_id"] == "GOV-V21-MANIFEST-FIX-001"


# ---------------------------------------------------------------------------
# workflow (D1)
# ---------------------------------------------------------------------------

def test_workflow_resolves_pr_base_and_head_explicitly():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_BASE_SHA" not in text
    assert "${{ github.event.pull_request.base.sha }}" in text
    assert "${{ github.event.pull_request.head.sha }}" in text
    assert "fetch-depth: 0" in text
    assert "-z" in text  # fail-closed checks on empty SHAs


# ---------------------------------------------------------------------------
# end-to-end behavior (real gate, throwaway repos)
# ---------------------------------------------------------------------------

def test_legal_write_set_passes_with_auto_selection(tmp_path):
    """Positive: legal WRITE_SET passes AND the PR-local manifest is
    auto-discovered (D2 fixed; no --manifest flag)."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/feature.py", "x = 1\n")
    write_manifest(
        repo,
        "T-LEGAL",
        base,
        write_set=["src/feature.py"],
        forbidden_set=["governance/**", "docs/**"],
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: Scope Gate" in result.stdout
    assert "TASK_ID: T-LEGAL" in result.stdout


def test_own_manifest_exact_exemption(tmp_path):
    """The task's own exact manifest path is exempt from the WRITE_SET
    check even when the manifest does not list itself."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    relpath = write_manifest(
        repo, "T-EXEMPT", base, write_set=["src/a.py"], forbidden_set=["src/b.py"]
    )
    assert relpath not in json.loads((repo / relpath).read_text(encoding="utf-8"))["write_set"]
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 0, result.stdout + result.stderr


def test_forbidden_match_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "evil/thing.py", "x\n")
    put(repo, "src/feature.py", "y\n")
    relpath = write_manifest(
        repo,
        "T-FORB",
        base,
        write_set=["src/feature.py"],
        forbidden_set=["evil/**"],
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "FORBIDDEN_SET violations" in result.stdout
    assert "evil/thing.py" in result.stdout
    assert "src/feature.py" not in result.stdout.split("FORBIDDEN_SET violations:")[1]


def test_denied_even_when_write_set_matches(tmp_path):
    """Deny-wins at scope time: a changed file matching BOTH sets fails the
    gate even though it also matches WRITE_SET.

    The manifest sets are pattern-disjoint under the load-time string
    approximation (so the manifest loads), but the real changed file
    'src/feature.py' matches both 'src/feat*' and 'src/*ure.py'. The scope
    gate is the authoritative deny-wins enforcement for exactly this case:
    FORBIDDEN_SET match -> FAIL, regardless of WRITE_SET match."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/feature.py", "x\n")
    relpath = write_manifest(
        repo,
        "T-DENY",
        base,
        write_set=["src/feat*"],
        forbidden_set=["src/*ure.py"],
    )
    head = commit_all(repo, "scenario")
    # the manifest itself must load (sets are string-disjoint)
    manifest = gg.load_manifest(repo / relpath)
    assert manifest["task_id"] == "T-DENY"
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "FORBIDDEN_SET violations" in result.stdout
    assert "src/feature.py" in result.stdout
    assert "WRITE_SET violations" not in result.stdout


def test_write_set_mismatch_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/other.py", "x\n")
    relpath = write_manifest(
        repo, "T-MISS", base, write_set=["src/a.py"], forbidden_set=[]
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "WRITE_SET violations" in result.stdout
    assert "src/other.py" in result.stdout


def test_nested_governance_audits_not_matched_by_star(tmp_path):
    """The AI3-GOV-PILOT-001 conflict is eliminated: governance/*.md in
    FORBIDDEN_SET no longer reaches governance/audits/*.md deliverables."""
    repo, base = init_repo(tmp_path)
    put(repo, "governance/audits/report.md", "audit\n")
    relpath = write_manifest(
        repo,
        "T-AUDIT",
        base,
        write_set=["governance/audits/report.md"],
        forbidden_set=["governance/*.md"],
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: Scope Gate" in result.stdout


def test_wrong_base_commit_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    relpath = write_manifest(
        repo, "T-BASE", "1" * 40, write_set=["src/a.py"], forbidden_set=[]
    )
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "does not match manifest base_commit" in result.stdout


def test_zero_manifest_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head)
    assert result.returncode == 1
    assert "found 0" in result.stdout


def test_multiple_manifests_fail(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    write_manifest(repo, "T-ONE", base, write_set=["src/a.py"])
    write_manifest(repo, "T-TWO", base, write_set=["src/a.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head)
    assert result.returncode == 1
    assert "found 2" in result.stdout


def test_manifest_of_another_task_is_not_exempt(tmp_path):
    """Only the task's own exact manifest path is exempt; a second task's
    manifest carried in the PR is a WRITE_SET violation."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    own = write_manifest(repo, "T-OWN", base, write_set=["src/a.py"])
    foreign = write_manifest(repo, "T-FOREIGN-TASK", base, write_set=["src/b.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=own)
    assert result.returncode == 1
    assert "WRITE_SET violations" in result.stdout
    assert foreign in result.stdout


def test_empty_base_fails_closed(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    relpath = write_manifest(repo, "T-EMPTY", base, write_set=["src/a.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, "", head, manifest=relpath)
    assert result.returncode == 1
    assert "must be non-empty" in result.stdout


def test_missing_explicit_manifest_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=".agent/tasks/NOPE.json")
    assert result.returncode == 1
    assert "manifest not found" in result.stdout


def test_cross_pr_write_set_conflict_is_not_scope_gate_business(tmp_path):
    """Boundary: two independent PRs claiming the same file each PASS in
    isolation. Cross-PR overlap is the AI1 Conflict Gate's procedural
    responsibility and must NOT be (and is not) decided by the Scope Gate."""
    verdicts = []
    for index in ("A2", "A3"):
        repo, base = init_repo(tmp_path / index)
        put(repo, "src/shared.py", "shared\n")
        write_manifest(
            repo,
            f"T-{index}",
            base,
            agent=("AI2" if index == "A2" else "AI3"),
            write_set=["src/shared.py"],
        )
        head = commit_all(repo, "scenario")
        result = run_gate(repo, base, head)
        verdicts.append(result.returncode)
    assert verdicts == [0, 0]


# ---------------------------------------------------------------------------
# authority boundaries pinned statically
# ---------------------------------------------------------------------------

def test_gate_does_not_hold_ai1_authority():
    """AI1-only final states: the gate implements no acceptance, merge,
    promotion or lock machinery."""
    source = GATE_SCRIPT.read_text(encoding="utf-8")
    assert "ACCEPTED" not in source
    assert "PRODUCTION_APPROVED" not in source
    assert "git merge" not in source
    assert "git push" not in source
    # Shared Interface Lock semantics are untouched: the manifest key is
    # declared but never evaluated.
    assert source.count("shared_interfaces") == 1
