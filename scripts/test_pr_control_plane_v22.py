#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

GATE=[sys.executable,"scripts/governance_pr_control_plane_gate.py"]
BASE="e33b649189af17547c73a2e131f808c08baa62ed"

def run(manifest, registry):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); mf=p/"m.json"; rg=p/"r.json"
        mf.write_text(json.dumps(manifest),encoding="utf-8")
        rg.write_text(json.dumps(registry),encoding="utf-8")
        return subprocess.run(GATE+["--manifest",str(mf),"--registry",str(rg)],text=True,capture_output=True)

def manifest(state="READY_TO_START", writes=None, interfaces=None):
    return {
        "task_id":"CP-AI2-PR-001","agent":"AI2","base_commit":BASE,
        "write_set":writes or ["src/portfolio.py"],
        "shared_interfaces":interfaces or []
    }

def registry(state="READY_TO_START", writes=None, locks=None):
    return {
        "version":"2.2","base_commit":BASE,
        "tasks":[{"task_id":"CP-AI2-PR-001","agent":"AI2","state":state,
                  "write_set":writes or ["src/portfolio.py"]}],
        "interface_locks":locks or []
    }

cases=[
    (manifest(),registry(),0),
    (manifest(),registry("IN_PROGRESS"),1),
    (manifest(["src/risk.py"] if False else "READY_TO_START",["src/risk.py"]),registry(),1),
    (manifest(interfaces=["API:RiskService"]),registry("READY_TO_START",["src/portfolio.py"],[]),1),
    (manifest(interfaces=["API:RiskService"]),registry("READY_TO_START",["src/portfolio.py"],
        [{"interface":"API:RiskService","owner_task":"CP-AI2-PR-001","status":"LOCKED"}]),0),
]
for m,r,want in cases:
    got=run(m,r).returncode
    if got != want:
        print(run(m,r).stdout,run(m,r).stderr)
        raise SystemExit("unexpected control-plane gate result")
print("PASS: PR Control Plane authorization drill")
