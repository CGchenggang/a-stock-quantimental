# AI3-GOV-V22-GATE-DESIGN-001 — Executable Gate v2.2 Design

## Status
**DESIGN COMPLETE / READY_FOR_AI1_AUDIT**

Base: `e33b649189af17547c73a2e131f808c08baa62ed`

Design-only. No executable gate, workflow, schema, manifest, or governance specification is modified by this task.

## 1. Confirmed defects
**D1 — workflow base reference:** current workflow passes `$GITHUB_BASE_SHA`; v2.2 must use an explicit reliable PR base/head source and fail closed if unresolved.

**D2 — manifest normalization:** current `normalize()` uses `lstrip("./")`. Python removes any leading characters from that set, so `.agent/tasks/...` can become `agent/tasks/...`, breaking manifest discovery. Only an exact leading `./` should be removed; meaningful leading dots must be preserved.

**D3 — glob semantics:** generic `fnmatch.fnmatchcase` permits directory-crossing behavior inconsistent with direct-child `*` semantics.

**D4 — schema/gate mismatch:** executable gate requires `forbidden_set`; normative v2 dependency schema does not declare it.

**D5 — deny-wins must be normative:** current behavior rejects forbidden matches independently of WRITE_SET; v2.2 should define and test this explicitly.

## 2. Proposed gate contract
Required manifest fields should align with the ratified v2.2 contract:
task_id, agent, base_commit, depends_on, blocks, read_set, write_set, forbidden_set, shared_interfaces, authorization, acceptance.

The gate must reject missing required fields, invalid types, invalid JSON, placeholder base commits, and base mismatches.

## 3. Safe path normalization
1. Replace backslashes with `/`.
2. Remove only an exact leading `./`.
3. Reject absolute paths and traversal components such as `../`.
4. Preserve `.agent/` and other meaningful leading dots.
5. Use one repository-relative canonical form everywhere.

Manifest discovery must match canonical paths beginning `.agent/tasks/` and ending `.json`.

## 4. Pattern language
Implement only:
- exact: `a/b.txt`
- direct child: `a/*.txt`
- recursive: `a/**`

Component-aware matching is preferred:
- `*` matches one path component;
- `**` matches zero or more components;
- literal components require equality.
Thus `governance/*.md` must not match `governance/audits/x.md`, while `governance/**` must.

## 5. Manifest self-exemption
Only the exact selected PR-local manifest may be exempt from scope evaluation. Another manifest, governance file, or unexpected file is not exempt. Exactly one PR-local manifest must be discoverable.

## 6. Scope evaluation
For each changed file except the selected manifest:
1. FORBIDDEN_SET match -> **FAIL**;
2. otherwise WRITE_SET mismatch -> **FAIL**;
3. otherwise PASS.

This is explicit deny-wins. A path in both sets is never accepted.

## 7. Base/head acquisition
Workflow supplies explicit PR base/head values; the gate remains a pure comparator over supplied commits.
Fail closed on missing base/head, invalid commits, diff failure, or manifest base mismatch. Never infer the base from a mutable local branch name.

## 8. CI sequence
1. resolve PR base/head;
2. compute changed paths;
3. discover exactly one manifest;
4. validate manifest;
5. verify manifest.base_commit == supplied base;
6. evaluate scope;
7. emit PASS/FAIL.

Checkout must retain enough history for the comparison.

## 9. Gate boundaries
Scope Gate owns only manifest structure, frozen base, changed-file scope and forbidden deny-wins.
Conflict Gate remains AI1-owned semantic analysis: file/API/schema/config overlap, shared interfaces and runtime coupling.
Test Gate validates required tests/evidence.
The executable Scope Gate must not silently implement dependency resolution, Shared Interface Lock ownership, or final acceptance.

## 10. Required validation matrix
| Case | Expected |
|---|---|
| one valid manifest + only WRITE_SET file | PASS |
| manifest + unrelated file | FAIL |
| manifest + forbidden file | FAIL |
| file in both WRITE_SET and FORBIDDEN_SET | FAIL |
| governance/*.md vs governance/audits/x.md | no match |
| governance/** vs nested audit | match |
| .agent/tasks/x.json discovery | PASS |
| ./.agent/tasks/x.json normalization | PASS |
| two manifests | FAIL |
| zero manifests | FAIL |
| missing forbidden_set | FAIL |
| invalid JSON | FAIL |
| manifest base mismatch | FAIL |
| missing base/head | FAIL |
| invalid git diff | FAIL |

## 11. Minimal implementation plan
**Phase A — Human Authorization:** ratify pattern semantics, deny-wins, manifest/schema alignment, and workflow base/head source.

**Phase B — separately authorized implementation:** modify only the ratified files, primarily `scripts/governance_gate.py`, `.github/workflows/governance-gate.yml`, and synchronized manifest/schema documents if required.

**Phase C — independent validation:** positive/negative tests, a real worker PR to main, branch-base/manifest/diff traceability, then AI1 independent acceptance.

## Risks / non-goals
Broad legacy patterns may need review. Local/manual invocation assumptions may change. No P14-F implementation, conflict auto-resolution, authorization inference, or worker self-acceptance is included.

## Acceptance
**READY_FOR_AI1_AUDIT. No implementation authorization granted.**
