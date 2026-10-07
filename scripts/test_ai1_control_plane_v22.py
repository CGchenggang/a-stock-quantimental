#!/usr/bin/env python3
"""AI1 Control Plane v2.2 drill: allocation, conflict, lock, release."""

import json
import tempfile
from pathlib import Path
import subprocess
import sys

GATE = Path("scripts/governance_conflict_gate.py")
BASE = "e33b649189af17547c73a2e131f808c08baa62ed"


def run(task, registry):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        mf = p / "manifest.json"
        rg = p / "registry.json"
        mf.write_text(json.dumps(task), encoding="utf-8")
        rg.write_text(json.dumps(registry), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(GATE), "--manifest", str(mf), "--registry", str(rg)],
            text=True, capture_output=True
        )


def task(tid, agent, write, interfaces=None):
    return {
        "task_id": tid, "agent": agent, "base_commit": BASE,
        "write_set": write, "shared_interfaces": interfaces or []
    }


def registry(tasks, locks=None):
    return {
        "version": "2.2", "base_commit": BASE,
        "tasks": tasks, "interface_locks": locks or []
    }


events = []

# 1. AI1 allocates two disjoint tasks.
ai2 = task("CP-AI2-001", "AI2", ["src/portfolio.py"])
ai3 = task("CP-AI3-001", "AI3", ["src/risk.py"])
r = run(ai3, registry([ai2, ai3]))
assert r.returncode == 0, r.stdout
events.append("ALLOCATED: CP-AI2-001 + CP-AI3-001")

# 2. AI1 detects a conflicting reallocation.
conflicting = task("CP-AI3-001", "AI3", ["src/portfolio.py"])
r = run(conflicting, registry([ai2, conflicting]))
assert r.returncode != 0 and "WRITE_SET" in r.stdout
events.append("REJECTED: CP-AI3-001 conflicting WRITE_SET")

# 3. AI1 requests a shared interface without granting a lock.
shared = task("CP-AI3-001", "AI3", ["src/risk.py"], ["API:RiskService"])
r = run(shared, registry([ai2, shared]))
assert r.returncode != 0 and "no lock exists" in r.stdout
events.append("BLOCKED: CP-AI3-001 shared interface without lock")

# 4. AI1 grants the lock to AI3.
locks = [{"interface": "API:RiskService", "owner_task": "CP-AI3-001", "status": "LOCKED"}]
r = run(shared, registry([ai2, shared], locks))
assert r.returncode == 0, r.stdout
events.append("LOCKED: API:RiskService -> CP-AI3-001")

# 5. AI1 audits and releases the lock.
released = [{"interface": "API:RiskService", "owner_task": "CP-AI3-001", "status": "UNLOCKED"}]
r = run(shared, registry([ai2, shared], released))
assert r.returncode != 0 and "expected LOCKED" in r.stdout
events.append("RELEASED: API:RiskService")

print("PASS: AI1 Control Plane v2.2 drill")
for e in events:
    print(e)
