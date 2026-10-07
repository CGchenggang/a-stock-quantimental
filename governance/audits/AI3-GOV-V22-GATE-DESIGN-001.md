# AI3-GOV-V22-GATE-DESIGN-001

## Status
DESIGN ONLY — no executable governance implementation authorized.

## Base
e33b649189af17547c73a2e131f808c08baa62ed

## Purpose
Design the minimum executable-gate v2.2 repair plan based on AI1-GOV-DESIGN-REVIEW-001 and AI3-GATE-VALIDATION-001.

## READ_SET
- governance/GOVERNANCE-GATES-v2.md
- governance/EXECUTION-GUIDE-v2.1.md
- governance/TASK-DEPENDENCY-SCHEMA-v2.md
- governance/TASK-STATE-MACHINE-v2.md
- governance/SHARED-INTERFACE-LOCK-v2.md
- governance/AI1-INTEGRATION-CONTROLLER-v2.md
- .agent/task-template.json
- .agent/tasks/GOV-V21-MANIFEST-FIX-001.json
- scripts/governance_gate.py
- .github/workflows/governance-gate.yml
- AI3-GATE-VALIDATION-001 findings

## WRITE_SET
- governance/audits/AI3-GOV-V22-GATE-DESIGN-001.md

## FORBIDDEN_SET
- governance/*.md except the audit file above
- governance/**
- scripts/**
- .github/**
- .agent/**
- src/**
- tests/**
- data/**
- P14-F related files

## REQUIRED DESIGN COVERAGE
1. Correct PR base/head acquisition.
2. PR-local manifest discovery and normalization.
3. WRITE_SET/FORBIDDEN_SET matching semantics.
4. deny-wins behavior and manifest self-exemption.
5. Schema/gate alignment.
6. Positive/negative executable test matrix.
7. Scope Gate vs Conflict Gate vs Test Gate boundary.
8. CI behavior on worker PRs.
9. Failure behavior and fail-closed semantics.
10. Minimal-change implementation plan, with exact files and Human Authorization needs.
11. Do not modify executable gate/workflow/specs.

## ACCEPTANCE
The report must separate confirmed defects from proposed fixes and provide an end-to-end validation matrix.

## EXECUTION RULE
No existing governance specification, gate, workflow, schema, manifest, or task state may be modified by this task.
