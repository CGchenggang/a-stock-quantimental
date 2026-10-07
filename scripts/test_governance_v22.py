#!/usr/bin/env python3
"""Self-test for Governance v2.2 Conflict Gate and Shared Interface Lock."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "governance_conflict_gate.py"
BASE = "e33b649189af17547c73a2e131f808c08baa62ed"


def run(manifest, registry):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        m = path / "manifest.json"
        r = path / "registry.json"
        m.write_text(json.dumps(manifest), encoding="utf-8")
        r.write_text(json.dumps(registry), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(GATE), "--manifest", str(m), "--registry", str(r)],
            text=True,
            capture_output=True,
        )


def manifest(task_id, writes, interfaces=None):
    return {
        "task_id": task_id,
        "agent": "AI2",
        "base_commit": BASE,
        "write_set": writes,
        "shared_interfaces": interfaces or [],
    }


def registry(tasks, locks=None):
    return {
        "version": "2.2",
        "base_commit": BASE,
        "tasks": tasks,
        "interface_locks": locks or [],
    }


# 1. Disjoint tasks must pass.
r = run(
    manifest("TASK-B", ["src/b.py"]),
    registry([manifest("TASK-A", ["src/a.py"])]),
)
assert r.returncode == 0, r.stdout + r.stderr

# 2. Overlapping WRITE_SET must fail.
r = run(
    manifest("TASK-B", ["src/shared.py"]),
    registry([manifest("TASK-A", ["src/shared.py"])]),
)
assert r.returncode != 0 and "WRITE_SET" in r.stdout

# 3. Shared interface without AI1 lock must fail.
r = run(
    manifest("TASK-B", ["src/b.py"], ["API:OrderService"]),
    registry([manifest("TASK-B", ["src/b.py"], ["API:OrderService"])], []),
)
assert r.returncode != 0 and "no lock exists" in r.stdout

# 4. AI1-authorized lock must pass.
r = run(
    manifest("TASK-B", ["src/b.py"], ["API:OrderService"]),
    registry(
        [manifest("TASK-B", ["src/b.py"], ["API:OrderService"])],
        [{"interface": "API:OrderService", "owner_task": "TASK-B", "status": "LOCKED"}],
    ),
)
assert r.returncode == 0, r.stdout + r.stderr

print("PASS: Governance v2.2 self-test")
