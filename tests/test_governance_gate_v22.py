"""Tests for the v2.2 executable governance Scope Gate (rework).

Covers AI3-GOV-V22-GATE-REWORK-001 against PARALLEL-GOVERNANCE-v2.2-ADDENDUM:
- section 2 pattern semantics: only exact, dir/*.py and trailing dir/** are
  valid; leading/middle/multiple/bare '**' fail closed at load time;
- section 1 deny-wins FORBIDDEN_SET (load-level set disjointness and
  scope-level enforcement);
- section 3 self-exemption: only the exact current manifest path, exempt
  from WRITE_SET and FORBIDDEN_SET; foreign manifests are not exempt;
- section 4 canonical 11-state vocabulary for status;
- section 8 Always-Protected Boundary: protected hits fail without a valid
  authorization exception; a valid exception never bypasses FORBIDDEN_SET;
- section 5/6 of the rework task: 13-field v2.2 manifest validation and the
  protected-boundary evaluation order;
- fail-closed base/head handling and workflow wiring.
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
    spec = importlib.util.spec_from_file_location("governance_gate_v22_rework", GATE_SCRIPT)
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
    """Emit a full v2.2 manifest; defaults carry a valid protected-boundary
    exception because every PR-local manifest lands under .agent/**."""
    manifest = {
        "task_id": task_id,
        "agent": "AI3",
        "zcode_agent": "ZCODE-A3",
        "base_commit": base_commit,
        "depends_on": [],
        "blocks": [],
        "read_set": [],
        "write_set": [],
        "forbidden_set": [],
        "shared_interfaces": [],
        "authorization": {
            "human_required": True,
            "human_authorization_ref": "HUMAN-AUTH-TEST-REF",
            "ai1_authorized": True,
            "protected_boundary_exception": True,
        },
        "acceptance": {"tests": [], "gates": ["scope", "conflict", "test"]},
        "status": "IN_PROGRESS",
    }
    for key, value in overrides.items():
        if key == "authorization":
            manifest["authorization"].update(value)
        else:
            manifest[key] = value
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
        "zcode_agent": "ZCODE-A3",
        "base_commit": "0" * 40,
        "depends_on": [],
        "blocks": [],
        "read_set": [],
        "write_set": ["src/a.py"],
        "forbidden_set": ["governance/**"],
        "shared_interfaces": [],
        "authorization": {
            "human_required": True,
            "human_authorization_ref": "HUMAN-AUTH-TEST-REF",
            "ai1_authorized": True,
            "protected_boundary_exception": False,
        },
        "acceptance": {"tests": [], "gates": ["scope", "conflict", "test"]},
        "status": "IN_PROGRESS",
    }
    for key, value in overrides.items():
        if key == "authorization":
            payload["authorization"].update(value)
        else:
            payload[key] = value
    return payload


def load_payload(tmp_path: Path, payload) -> Path:
    path = tmp_path / "m.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# path normalization and safety
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


# ---------------------------------------------------------------------------
# pattern semantics: the three valid forms
# ---------------------------------------------------------------------------

def test_exact_pattern_matches_only_itself():
    assert gg.path_matches("foo/bar.py", "foo/bar.py")
    assert not gg.path_matches("foo/bar.pyx", "foo/bar.py")
    assert not gg.path_matches("foo/baz.py", "foo/bar.py")
    assert not gg.path_matches("x/foo/bar.py", "foo/bar.py")


def test_single_level_star_never_crosses_slash():
    assert gg.path_matches("governance/A.md", "governance/*.md")
    assert gg.path_matches("governance/P13x.md", "governance/P*.md")
    assert not gg.path_matches("governance/audits/A.md", "governance/*.md")
    assert not gg.path_matches("governance/audits/sub/A.md", "governance/*.md")


def test_trailing_doublestar_matches_any_depth():
    assert gg.path_matches("governance/A.md", "governance/**")
    assert gg.path_matches("governance/audits/A.md", "governance/**")
    assert gg.path_matches("governance/a/b/c.md", "governance/**")
    assert gg.path_matches("src/astock_v2/deep/x.py", "src/**")
    assert not gg.path_matches("governance", "governance/**")
    assert not gg.path_matches("governancex/A.md", "governance/**")


def test_matches_list_helper():
    assert gg.matches("governance/x.md", ["governance/*.md", "docs/**"])
    assert gg.matches("docs/a/b.md", ["governance/*.md", "docs/**"])
    assert not gg.matches("governance/audits/x.md", ["governance/*.md"])


# ---------------------------------------------------------------------------
# pattern form validation (fail closed at load time)
# ---------------------------------------------------------------------------

def test_leading_doublestar_invalid(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["**/file.py"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="'**/file.py'")


def test_middle_doublestar_invalid(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["a/**/file.py"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="'a/**/file.py'")


def test_multiple_recursive_forms_invalid(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["a/**/b/**"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="multiple '**'")


def test_bare_doublestar_invalid(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["**"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="bare '**'")


def test_valid_pattern_forms_accepted(tmp_path):
    path = load_payload(
        tmp_path,
        manifest_payload(
            write_set=["src/exact.py", "src/dir/*.py", "src/dir/**", "src/x*.py"],
            forbidden_set=["governance/**"],
        ),
    )
    assert gg.load_manifest(path)["task_id"] == "T"


def test_empty_path_component_invalid(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["a//b.py"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="empty path component")


# ---------------------------------------------------------------------------
# v2.2 manifest validation (13 fields, authorization block, status)
# ---------------------------------------------------------------------------

def test_valid_v22_manifest_loads(tmp_path):
    path = load_payload(tmp_path, manifest_payload())
    assert gg.load_manifest(path)["task_id"] == "T"


def test_missing_v22_field_rejected(tmp_path, capsys):
    payload = manifest_payload()
    del payload["zcode_agent"]
    path = load_payload(tmp_path, payload)
    expect_fail(capsys, gg.load_manifest, path, fragment="'zcode_agent'")


def test_missing_authorization_rejected(tmp_path, capsys):
    payload = manifest_payload()
    del payload["authorization"]
    path = load_payload(tmp_path, payload)
    expect_fail(capsys, gg.load_manifest, path, fragment="'authorization'")


def test_invalid_authorization_type_rejected(tmp_path, capsys):
    path = load_payload(
        tmp_path, manifest_payload(authorization={"human_required": "yes"})
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="boolean")


def test_missing_authorization_subkey_rejected(tmp_path, capsys):
    payload = manifest_payload()
    del payload["authorization"]["protected_boundary_exception"]
    path = load_payload(tmp_path, payload)
    expect_fail(
        capsys, gg.load_manifest, path, fragment="protected_boundary_exception"
    )


def test_invented_status_rejected(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(status="AUTHORIZED"))
    expect_fail(capsys, gg.load_manifest, path, fragment="canonical")


def test_noncanonical_ready_for_ai1_audit_rejected(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(status="READY_FOR_AI1_AUDIT"))
    expect_fail(capsys, gg.load_manifest, path, fragment="canonical")


def test_canonical_status_accepted(tmp_path):
    for state in ("READY_TO_START", "IN_PROGRESS", "BLOCKED", "READY_FOR_AUDIT"):
        path = load_payload(tmp_path / state, manifest_payload(status=state))
        assert gg.load_manifest(path)["status"] == state


def test_placeholder_base_commit_rejected(tmp_path, capsys):
    path = load_payload(
        tmp_path, manifest_payload(base_commit="FREEZE_TO_REAL_COMMIT_SHA")
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="frozen to a real commit SHA")


def test_write_forbidden_overlap_rejected_at_load(tmp_path, capsys):
    path = load_payload(
        tmp_path,
        manifest_payload(write_set=["src/a.py"], forbidden_set=["src/**"]),
    )
    expect_fail(capsys, gg.load_manifest, path, fragment="self-contradictory")


def test_v21_manifest_fails_v22_load():
    """Migration boundary (addendum section 9): no existing manifest is
    retrofitted. The v2.1-era manifest lacks the v2.2 fields and must be
    rejected by the v2.2 loader."""
    shipped = REPO_ROOT / ".agent" / "tasks" / "GOV-V21-MANIFEST-FIX-001.json"
    with pytest.raises(SystemExit) as excinfo:
        gg.load_manifest(shipped)
    assert excinfo.value.code == 1


def test_traversal_pattern_rejected(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(forbidden_set=["../outside/**"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="safe relative path")


def test_absolute_pattern_rejected(tmp_path, capsys):
    path = load_payload(tmp_path, manifest_payload(write_set=["C:\\abs\\x"]))
    expect_fail(capsys, gg.load_manifest, path, fragment="safe relative path")


def test_invalid_json_rejected(tmp_path, capsys):
    path = load_payload(tmp_path, "{ not json")
    expect_fail(capsys, gg.load_manifest, path, fragment="invalid JSON")


# ---------------------------------------------------------------------------
# workflow (rework section 7)
# ---------------------------------------------------------------------------

def test_workflow_resolves_pr_base_and_head_explicitly():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_BASE_SHA" not in text
    assert "${{ github.event.pull_request.base.sha }}" in text
    assert "${{ github.event.pull_request.head.sha }}" in text
    assert "fetch-depth: 0" in text
    assert "-z" in text  # fail-closed checks on missing SHAs
    assert "merge" not in text.lower().replace("merge ref", "")
    assert "pull_request" in text  # PR-scoped; no push/promotion surface


# ---------------------------------------------------------------------------
# end-to-end behavior (real gate, throwaway repos)
# ---------------------------------------------------------------------------

def test_legal_write_set_passes_with_auto_selection(tmp_path):
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


def test_own_manifest_exempt_from_write_and_forbidden(tmp_path):
    """The own manifest path is exempt from BOTH checks: it is not listed in
    write_set, and forbidden_set deliberately covers .agent/** — the gate
    must still pass on the strength of the exact self-exemption."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    relpath = write_manifest(
        repo, "T-SELF", base, write_set=["src/a.py"], forbidden_set=[".agent/**"]
    )
    assert relpath not in json.loads((repo / relpath).read_text(encoding="utf-8"))["write_set"]
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FORBIDDEN_SET violations" not in result.stdout


def test_foreign_manifest_not_exempt(tmp_path):
    """A second task's manifest is a protected-boundary file that the valid
    exception lets through to the ordinary checks, where FORBIDDEN_SET
    (.agent/**) catches it — only the own exact path is exempt."""
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    own = write_manifest(
        repo, "T-OWN", base, write_set=["src/a.py"], forbidden_set=[".agent/**"]
    )
    foreign = write_manifest(repo, "T-FOREIGN-TASK", base, write_set=["src/b.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=own)
    assert result.returncode == 1
    assert "FORBIDDEN_SET violations" in result.stdout
    assert foreign in result.stdout


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


def test_deny_wins_enforced_at_scope(tmp_path):
    """Scope-level deny-wins backstop: the manifest sets are string-disjoint
    under the load-time approximation, but the real changed file
    'src/feature.py' matches both 'src/feat*' and 'src/*ure.py'. The
    FORBIDDEN_SET match must fail the gate regardless of WRITE_SET match."""
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
    assert gg.load_manifest(repo / relpath)["task_id"] == "T-DENY"
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "FORBIDDEN_SET violations" in result.stdout
    assert "src/feature.py" in result.stdout
    assert "WRITE_SET violations" not in result.stdout


def test_write_set_mismatch_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/other.py", "x\n")
    relpath = write_manifest(repo, "T-MISS", base, write_set=["src/a.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "WRITE_SET violations" in result.stdout
    assert "src/other.py" in result.stdout


def test_protected_path_without_exception_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, ".github/workflows/injected.yml", "on: push\n")
    relpath = write_manifest(
        repo,
        "T-PROT-NO",
        base,
        write_set=[".github/workflows/injected.yml"],
        authorization={"protected_boundary_exception": False},
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "PROTECTED BOUNDARY violations" in result.stdout
    assert ".github/workflows/injected.yml" in result.stdout


def test_protected_path_with_valid_exception_passes(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, ".github/workflows/governance-gate.yml", "name: governance-gate\n")
    relpath = write_manifest(
        repo,
        "T-PROT-YES",
        base,
        write_set=[".github/workflows/governance-gate.yml"],
        forbidden_set=["governance/**"],
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PROTECTED BOUNDARY (authorized exception active)" in result.stdout
    assert "PASS: Scope Gate" in result.stdout


def test_protected_exception_requires_ai1_authorization(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "scripts/governance_gate.py", "print('x')\n")
    relpath = write_manifest(
        repo,
        "T-PROT-NOAI1",
        base,
        write_set=["scripts/governance_gate.py"],
        authorization={"ai1_authorized": False},
    )
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "PROTECTED BOUNDARY violations" in result.stdout


def test_protected_exception_never_bypasses_forbidden(tmp_path):
    """A valid exception lets a protected file reach the ordinary checks;
    there a FORBIDDEN_SET match still fails the gate (addendum section 8)."""
    repo, base = init_repo(tmp_path)
    put(repo, ".github/workflows/gate-v2.yml", "name: x\n")
    relpath = write_manifest(
        repo,
        "T-PROT-FORB",
        base,
        write_set=[".github/workflows/gate*.yml"],
        forbidden_set=[".github/workflows/*v2.yml"],
    )
    head = commit_all(repo, "scenario")
    assert gg.load_manifest(repo / relpath)["task_id"] == "T-PROT-FORB"
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "FORBIDDEN_SET violations" in result.stdout
    assert ".github/workflows/gate-v2.yml" in result.stdout


def test_wrong_base_commit_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    relpath = write_manifest(repo, "T-BASE", "1" * 40, write_set=["src/a.py"])
    result = run_gate(repo, base, head, manifest=relpath)
    assert result.returncode == 1
    assert "does not match manifest base_commit" in result.stdout


def test_non_sha_base_fails_closed(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    result = run_gate(repo, "main", head)
    assert result.returncode == 1
    assert "40-hex" in result.stdout


def test_empty_base_fails_closed(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    relpath = write_manifest(repo, "T-EMPTY", base, write_set=["src/a.py"])
    head = commit_all(repo, "scenario")
    result = run_gate(repo, "", head, manifest=relpath)
    assert result.returncode == 1
    assert "non-empty" in result.stdout


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


def test_missing_explicit_manifest_fails(tmp_path):
    repo, base = init_repo(tmp_path)
    put(repo, "src/a.py", "x\n")
    head = commit_all(repo, "scenario")
    result = run_gate(repo, base, head, manifest=".agent/tasks/NOPE.json")
    assert result.returncode == 1
    assert "manifest not found" in result.stdout


def test_cross_pr_write_set_conflict_is_not_scope_gate_business(tmp_path):
    """Boundary: two independent PRs claiming the same file each PASS in
    isolation. Cross-PR overlap is AI1 Conflict Gate territory and the
    Scope Gate must not (and does not) decide it."""
    verdicts = []
    for index, agent in (("A2", "AI2"), ("A3", "AI3")):
        repo, base = init_repo(tmp_path / index)
        put(repo, "src/shared.py", "shared\n")
        write_manifest(
            repo,
            f"T-{index}",
            base,
            agent=agent,
            write_set=["src/shared.py"],
        )
        head = commit_all(repo, "scenario")
        verdicts.append(run_gate(repo, base, head).returncode)
    assert verdicts == [0, 0]


# ---------------------------------------------------------------------------
# authority boundaries pinned statically
# ---------------------------------------------------------------------------

def test_gate_does_not_hold_ai1_authority():
    source = GATE_SCRIPT.read_text(encoding="utf-8")
    # "ACCEPTED" exists only inside the canonical state vocabulary constant;
    # the gate can never produce or transition to it.
    assert source.count('"ACCEPTED"') == 1
    assert "PRODUCTION_APPROVED" not in source
    assert "git merge" not in source
    assert "git push" not in source
    # Shared Interface Lock semantics untouched: the manifest key is only
    # declared (required-keys list) and type-checked as a list; the gate
    # contains no lock lifecycle machinery.
    assert source.count("shared_interfaces") == 2
    assert '"LOCKED"' not in source
    assert '"REQUESTED"' not in source
