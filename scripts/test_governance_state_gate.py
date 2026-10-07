#!/usr/bin/env python3
import subprocess, sys

GATE=[sys.executable,"scripts/governance_state_gate.py"]

def run(a,b,actor):
    return subprocess.run(GATE+["--from",a,"--to",b,"--actor",actor],text=True,capture_output=True)

cases=[
    ("PLANNED","ALLOCATED","AI1",0),
    ("ALLOCATED","READY_TO_START","AI1",0),
    ("READY_TO_START","IN_PROGRESS","AI2",0),
    ("IN_PROGRESS","READY_FOR_AUDIT","AI2",0),
    ("READY_FOR_AUDIT","AUDITING","AI1",0),
    ("AUDITING","INTEGRATING","AI1",0),
    ("INTEGRATING","ACCEPTED","AI1",0),
    ("ALLOCATED","IN_PROGRESS","AI2",1),
    ("READY_FOR_AUDIT","AUDITING","AI2",1),
    ("INTEGRATING","ACCEPTED","AI3",1),
]
for a,b,actor,want in cases:
    r=run(a,b,actor)
    if (r.returncode != 0) != bool(want):
        print(r.stdout,r.stderr)
        raise SystemExit(f"unexpected result for {a}->{b} by {actor}")
print("PASS: AI1 Control Plane state-machine drill")
