#!/usr/bin/env python3
"""Validate Governance v2.2 AI1 task-state transitions."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path

STATES = {
    "PLANNED", "ALLOCATED", "READY_TO_START", "IN_PROGRESS",
    "BLOCKED", "READY_FOR_AUDIT", "AUDITING", "INTEGRATING",
    "ACCEPTED", "REJECTED", "ABORTED"
}
TRANSITIONS = {
    "PLANNED": {"ALLOCATED", "REJECTED", "ABORTED"},
    "ALLOCATED": {"READY_TO_START", "REJECTED", "ABORTED"},
    "READY_TO_START": {"IN_PROGRESS", "REJECTED", "ABORTED"},
    "IN_PROGRESS": {"BLOCKED", "READY_FOR_AUDIT", "REJECTED", "ABORTED"},
    "BLOCKED": {"IN_PROGRESS", "REJECTED", "ABORTED"},
    "READY_FOR_AUDIT": {"AUDITING", "REJECTED", "ABORTED"},
    "AUDITING": {"INTEGRATING", "REJECTED", "ABORTED"},
    "INTEGRATING": {"ACCEPTED", "REJECTED", "ABORTED"},
    "ACCEPTED": set(),
    "REJECTED": set(),
    "ABORTED": set(),
}
AI1_ONLY = {"AUDITING", "INTEGRATING", "ACCEPTED", "REJECTED", "ABORTED"}

def fail(msg):
    print("FAIL:", msg)
    raise SystemExit(1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="old", required=True)
    p.add_argument("--to", dest="new", required=True)
    p.add_argument("--actor", required=True)
    args = p.parse_args()

    if args.old not in STATES or args.new not in STATES:
        fail("unknown state")
    if args.new not in TRANSITIONS[args.old]:
        fail(f"invalid transition: {args.old} -> {args.new}")
    if args.new in AI1_ONLY and args.actor != "AI1":
        fail(f"{args.new} transition requires AI1")
    print(f"PASS: {args.old} -> {args.new} by {args.actor}")

if __name__ == "__main__":
    main()
