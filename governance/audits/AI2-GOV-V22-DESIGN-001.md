# AI2-GOV-V22-DESIGN-001

## Status
DESIGN ONLY — no governance implementation authorized.

## Base
e33b649189af17547c73a2e131f808c08baa62ed

## Purpose
Design the minimum backward-compatible v2.2 governance reconciliation addendum based on AI1-GOV-DESIGN-REVIEW-001.

## READ_SET
- governance/PROTOCOL-v1.md
- governance/PARALLEL-GOVERNANCE-v2.md
- governance/TASK-TEMPLATE-v1.md
- governance/TASK-DEPENDENCY-SCHEMA-v2.md
- governance/TASK-STATE-MACHINE-v2.md
- governance/SHARED-INTERFACE-LOCK-v2.md
- governance/GOVERNANCE-GATES-v2.md
- governance/AI1-INTEGRATION-CONTROLLER-v2.md
- governance/EXECUTION-GUIDE-v2.1.md
- governance/INTEGRATION-AUDIT-v1.md
- .agent/task-template.json
- scripts/governance_gate.py

## WRITE_SET
- governance/audits/AI2-GOV-V22-DESIGN-001.md

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
1. Canonical task contract and FORBIDDEN_SET semantics.
2. Canonical state vocabulary and legacy aliases.
3. READY_TO_START authorization evidence without unnecessary new state.
4. Shared Interface Lock complete transition/ownership model.
5. Authority precedence and corpus layering.
6. Pattern language: exact, direct-child *, recursive /**.
7. Always-protected defaults.
8. read_set consumer and acceptance-gate semantics.
9. Minimum backward-compatible migration path.
10. Explicit Human Authorization boundaries.
11. Distinguish design proposals from existing facts.
12. Do not authorize implementation.

## ACCEPTANCE
The report must identify exact affected documents, proposed semantic rules, compatibility impact, unresolved decisions, and which changes require Human Authorization.

## EXECUTION RULE
No existing governance specification, gate, workflow, schema, manifest, or task state may be modified by this task.
