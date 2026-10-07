# AI2-GOV-PILOT-001 — Governance Consistency Audit

Status: EXECUTION_AUTHORIZED
Owner: AI2
Executor: ZCODE-A2
Base Commit: 29403bc3a87fc8b885f9589dd265fe19fbdbf5b5
Branch: parallel/AI2/AI2-GOV-PILOT-001

## Objective
Independently audit the current parallel-governance documents for semantic conflicts, duplicate authority, missing gates, authorization ambiguity, and state-machine inconsistencies.

## READ_SET
- governance/PROTOCOL-v1.md
- governance/PARALLEL-GOVERNANCE-v2.md
- governance/TASK-TEMPLATE-v1.md
- governance/TASK-DEPENDENCY-SCHEMA-v2.md
- governance/TASK-STATE-MACHINE-v2.md
- governance/SHARED-INTERFACE-LOCK-v2.md
- governance/GOVERNANCE-GATES-v2.md
- governance/AI1-INTEGRATION-CONTROLLER-v2.md
- governance/INTEGRATION-AUDIT-v1.md

## WRITE_SET
Only:
- governance/audits/AI2-GOV-PILOT-001.md

## FORBIDDEN_SET
- src/**
- tests/**
- data/**
- docs/contracts/**
- docs/authorizations/**
- docs/AI_HANDOFF.md
- docs/PROJECT_STATUS.md
- governance/*.md
- any AI3 branch
- main
- P14-F implementation or authorization artifacts
- production code, models, registries, calibration, factors, policies, recommendations, trading logic

## Rules
1. Do not modify any READ_SET file.
2. Do not create or modify authorization.
3. Do not infer authorization for any other task.
4. Report findings as PASS, WARN, CONFLICT, or BLOCK.
5. Do not repair findings in this task.
6. If a forbidden boundary must change to continue, STOP.
7. The audit file must state the exact HEAD SHA audited and the final task status.

## Required Checks
- authority ownership consistency
- authorization/implementation/acceptance gate ordering
- state-machine consistency
- task package field consistency
- shared-interface lock semantics
- AI1 final authority consistency
- AI2/AI3/ZCODE role separation
- forbidden-set enforcement
- main/source-of-truth rules
- contradiction between v1 and v2 governance documents

## Completion
Before reporting READY_FOR_AUDIT:
- git status clean except the allowed audit file
- git diff --name-only matches WRITE_SET exactly
- audit file identifies baseline and branch HEAD
- no forbidden file changed
- commit the audit file
- push only this branch
- do not open/merge to main
