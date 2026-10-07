# AI3-GATE-VALIDATION-001 — Executable Governance Gate Validation

Status: READY_FOR_AI1_DESIGN_REVIEW (validation complete; findings await AI1 design decisions)
Owner: AI3
Executor: ZCODE-A3
Branch: parallel/AI3/AI3-GATE-VALIDATION-001
BASE_COMMIT: e33b649189af17547c73a2e131f808c08baa62ed (origin/main HEAD, tag governance-v2.1)
HEAD SHA AUDITED: e33b649189af17547c73a2e131f808c08baa62ed

BASE_COMMIT deviation note: the task assignment left BASE_COMMIT as
"<AI1 WILL PROVIDE EXACT BASE_COMMIT>" and no value was provided at execution
time. The READ_SET requires inspecting scripts/governance_gate.py,
.github/workflows/governance-gate.yml, .agent/task-template.json and
.agent/tasks/GOV-V21-MANIFEST-FIX-001.json — none of which exist at the
pilot base 29403bc; they exist only on main. The base was therefore frozen to
origin/main HEAD e33b649 (the commit that introduces the objects under
validation, tagged governance-v2.1). This choice is reversible (rebase) and
is flagged here for explicit AI1 ratification; all findings are anchored to
this SHA.

## Method

All 9 READ_SET specification files were read in full; the 6 files shared with
AI3-GOV-PILOT-001 are byte-identical between 29403bc and e33b649 (verified:
the only governance/ change between the two bases is the addition of
EXECUTION-GUIDE-v2.1.md). The AI2 pilot audit (at its final HEAD d47decf,
including its re-execution appendix) and the AI3 pilot audit (582085f) were
re-inspected.

The gate itself was validated BEHAVIORALLY, not only by reading: the
repository was cloned to a throwaway temp directory and the REAL, UNMODIFIED
scripts/governance_gate.py @ e33b649 was executed against 17 constructed
scenarios (throwaway branches and commits created only inside the clone).
The real repository was only read. No gate, workflow, manifest, spec, or
production file was modified anywhere; no fix was implemented.

## R1/R2 — FORBIDDEN_SET vs WRITE_SET glob conflict: REPRODUCED; exact semantics

Conflict reproduced end-to-end with the unmodified gate (scenario S1b below):
a manifest transcribing the pilot FORBIDDEN_SET verbatim fails on its own
WRITE_SET deliverable. Exact semantics of the two pattern dialects:

| Pattern | Naive/shell reading (manifest intent) | Python fnmatch (what the gate uses) | git pathspec (ls-files, observed) | gitignore wildmatch |
|---|---|---|---|---|
| governance/*.md | direct children only | CROSSES "/" — matches governance/audits/*.md | CROSSES "/" — observed: `git ls-files 'governance/*.md'` listed governance/audits/orphan.md | does NOT cross "/" |
| governance/audits/*.md | audits direct children only | CROSSES "/" — matches governance/audits/sub/deep.md | crosses | does not cross |
| governance/** | everything under governance | matches, and also matches the directory itself ("governance") via the gate's `/**` special case | — | similar, plus-self |

Probe outputs (M1, executed against the gate's own code):
- fnmatch.fnmatchcase('governance/audits/AI3-GOV-PILOT-001.md', 'governance/*.md') = True
- matches('governance/audits/AI3-GOV-PILOT-001.md', 'governance/*.md') = True
- matches('governance', 'governance/**') = True (directory itself matches its own `/**`)
- matches('.github/workflows/governance-gate.yml', '.github/workflows/**') = True (dot-paths match fine at the pattern level)
- git ls-files 'governance/*.md' → 13 direct children PLUS governance/audits/orphan.md

Conclusion (R2): the "direct-child" reading exists in NO implementation
dialect actually in play — not in the gate's fnmatch, and not even in git
pathspecs. It is only an unstated convention. The gate resolves the ambiguity
in the way that contradicts every pilot manifest authored to date.

## R3 — precedence vs explicit exclusions: ANSWER

Current behavior (measured, S5b): a file listed in BOTH write_set and
forbidden_set FAILS — forbidden is a hard veto with no write_set precedence,
and the only exemption in the code is the manifest file itself, and only from
the WRITE_SET check, not the forbidden check.

Assessment: KEEP forbidden-over-write_set as a hard veto. GOVERNANCE-GATES-v2
defines the Scope Gate as two independent conditions ("all changed files are
within WRITE_SET **and** no forbidden file changed"); write_set precedence
would let a manifest silently whitelist a forbidden file by listing it in
both sets, defeating FORBIDDEN_SET's purpose as a hard boundary. Explicit
negation/exclusion syntax is also unnecessary complexity. The correct fix is
authoring-side validation, not precedence: the gate should reject at
manifest-load time any manifest whose write_set and forbidden_set intersect
under the gate's own matcher, with a manifest-error message — instead of the
current behavior where the author discovers the contradiction as a confusing
FORBIDDEN_SET violation on their own deliverable (S1b). Combined with a
pattern-semantics decision (below), this makes the documented manifests
representable and keeps the boundary hard.

## R4 — can the current gate safely validate each task class?

| Task class | As-is, via real CI (auto-selection) | As-is, via explicit --manifest | After minimal fixes |
|---|---|---|---|
| AI2 audit task (governance/audits/AI2-GOV-PILOT-001.md; FORBIDDEN_SET contains governance/*.md) | NO — fails "found 0" (D2) before scope logic | NO — FORBIDDEN_SET hits its own deliverable (S1b analog) | YES, once D2 is fixed and forbidden pattern semantics are decided (direct-child reading or disjoint authoring) |
| AI3 audit task (same shape) | NO — same D2 | NO — same as S1b (executed) | YES, same conditions |
| Future production workstream task (e.g. write src/astock_v2/new_module.py) | NO — same D2 | YES — S5 PASS, provided the manifest author excludes its own write area from forbidden_set (S5b shows nothing guards this) | YES — S5 semantics preserved; add load-time write∩forbidden disjointness check |

The gate's core scope logic is sound when it can be reached with a reachable
manifest (S10a: the shipped GOV-V21-MANIFEST-FIX-001.json PASSes against the
real commit pair 7624382→e33b649 with explicit --manifest). What is broken is
everything between "PR opened" and "scope logic runs".

## R5 — task-manifest requirement validation (all measured)

| Requirement | Enforced? | Evidence / notes |
|---|---|---|
| task_id | presence only | printed; no format check; no linkage to manifest filename (convention only) |
| agent | YES — must be in {AI1, AI2, AI3} | load_manifest; template default is "AI2" |
| base_commit | YES — non-empty, ≠ FREEZE_TO_REAL_COMMIT_SHA, MUST equal the gate's --base | S7a: mismatch → "CI base commit does not match manifest base_commit" (this cross-check WORKS — it corrects an assumption left open by AI3-GOV-PILOT-001); S7b: placeholder rejected |
| depends_on / blocks | presence only | no dependency-graph evaluation anywhere in the gate |
| read_set | presence only | never used by the gate |
| write_set | YES — non-empty list; out-of-scope detection | manifest file itself exempted from the WRITE_SET check |
| forbidden_set | YES — hard veto; list (may be empty) | no load-time write∩forbidden disjointness check |
| shared_interfaces | presence only | lock lifecycle is procedural (SHARED-INTERFACE-LOCK-v2), not enforced by the gate |
| acceptance.gates | YES — must contain scope, conflict, test | enforced in load_manifest |
| acceptance.tests | declarative only | never executed by the gate or workflow |
| exactly one PR-local .agent/tasks/*.json | YES in code, UNREACHABLE in practice | D2 below; "found 2" is dead code in CI (S6c found 0) |
| schema conformity (TASK-DEPENDENCY-SCHEMA-v2) | IMPOSSIBLE | S3: a manifest with exactly the schema-v2 key set FAILS "manifest missing keys: ['forbidden_set']" — the schema omits a field the gate requires |

## R6/R7 — worker-branch CI behavior and sufficiency

Facts (GitHub API, full 40-char SHAs):
- tests.yml triggers only on `push: [main]` and `pull_request: [main]`.
  Workflow runs for AI3 582085f, AI2 d47decf, AI2 fe8fca6, AI3 32674f5: 0 each.
- PR-time tests DO run (open governance-v2.2 drill PRs show tests conclusions),
  and run from the MERGE REF, i.e. they test the actual integration candidate.
- governance-gate.yml (PR-time only, exists only on main): all observed runs
  on drill PRs are conclusion=failure — now mechanistically explained by D1+D2
  below: the gate has never executed its scope logic in CI; it dies at
  "exactly one PR-local task manifest is required ... found 0" (or, with an
  explicit manifest path, would die at the empty-base cross-check, S0).

Answer (R7): PR-time CI is SUFFICIENT for acceptance, because it tests the
merge ref — the only artifact that can actually be promoted — and AI1's
INTEGRATION-AUDIT-v1 step 7 already requires independent regression runs at
integration. Branch-level CI is NOT required for docs-only workstreams (the
pilot tasks); for production workstreams it is operationally recommended
(one-line trigger addition: `push: branches: ['parallel/**']`) so workers get
test signal before declaring READY_FOR_AUDIT, since ZCODE-A2/A3 prompts
require running tests before completion and today that is local-only. The
urgent CI problem is not branch coverage; it is that the PR-time governance
gate is non-functional (D1/D2).

## R8 — BASE_COMMIT vs current main vs PR merge ref vs gate version

- Worker BASE_COMMIT = 29403bc (tag governance-v2.0). Current main = e33b649
  (tag governance-v2.1). Main moved during the pilot; worker branches do not
  contain the gate at all.
- At PR time: --head = GITHUB_SHA = the PR merge ref (main+branch merged);
  checkout = the same merge ref; git diff base...head = merge-base diff =
  exactly the PR's changed files. --base SHOULD be the PR's base SHA
  (github.event.pull_request.base.sha = current main HEAD at PR time) — but
  the workflow passes the undefined $GITHUB_BASE_SHA instead (D1).
- Gate VERSION that runs = main's version at PR time (workflows execute from
  the merge ref); whatever a worker branch carries is irrelevant. Gate
  verdicts can therefore flip when main moves between PR open and merge.
- base_commit semantics (S7a): the gate enforces manifest base_commit ==
  --base, i.e. base_commit means "PR base", NOT "historical task base". When
  main drifts during a long task, AI1 must re-issue the integration manifest
  with the new PR base; the historical task base stays in the task record.
  This is coherent but must be documented — it silently redefines the field
  the pilot manifests froze.

## R9 — minimal end-to-end validation scenario: DESIGNED AND EXECUTED

Suite: temp clone of the repo; throwaway branch per scenario off e33b649;
unmodified scripts/governance_gate.py invoked with --base/--head (and
--manifest where stated). Manifests carry base_commit=e33b649 unless noted.
Results are actual executions, not predictions:

| ID | Scenario | Result |
|---|---|---|
| S0 | CI invocation shape: --base "" (undefined $GITHUB_BASE_SHA) + explicit manifest | FAIL "CI base commit does not match manifest base_commit" |
| S0b | true CI shape: no --manifest, HEAD == --head | FAIL "found 0" (git diff ...HEAD = empty) |
| S1 | pilot FORBIDDEN_SET verbatim (governance/*.md), auto-selection path | FAIL "found 0" (auto-selection dead, D2) |
| S1b | same manifest via explicit --manifest (scope logic reached) | FAIL — FORBIDDEN_SET violation on governance/audits/AI3-GOV-PILOT-001.md (pilot finding 9 reproduced) |
| S2 | same task, forbidden_set enumerated as direct children (13 files) | PASS (workaround exists, impractical) |
| S3 | manifest strictly per TASK-DEPENDENCY-SCHEMA-v2 (no forbidden_set key) | FAIL "manifest missing keys: ['forbidden_set']" |
| S4 | changed file inside forbidden_set and outside write_set (src/evil.py) | FAIL — both FORBIDDEN_SET and WRITE_SET violations reported |
| S5 | production task, forbidden_set excludes own write area | PASS |
| S5b | same file in write_set AND forbidden_set (src/**) | FAIL — forbidden hard veto, no precedence |
| S6a | worker A2 claims src/shared.py (PR 1 in isolation) | PASS |
| S6b | worker A3 claims the SAME src/shared.py (PR 2 in isolation) | PASS — cross-PR overlap invisible to the gate |
| S6c | both manifests in one PR, auto path | FAIL "found 0" (even the intended "found 2" error is unreachable in CI) |
| S7a | manifest base_commit ≠ actual --base | FAIL — base cross-check fires |
| S7b | base_commit left as template placeholder | FAIL — "base_commit must be frozen" |
| S8a | docs/PROJECT_STATUS.md changed, declared forbidden | FAIL — forbidden + WRITE_SET violation |
| S8b | same file claimed by write_set, forbidden empty | PASS — the gate cannot protect main-adjacent files by itself |
| S9 | changed files only, no manifest, no --manifest | FAIL "found 0" (what every pilot integration PR hits first) |
| S10a | shipped GOV-V21-MANIFEST-FIX-001.json + real pair 7624382→e33b649, explicit --manifest | PASS |
| S10b | shipped manifest auto-selected from changed files (PR-realistic) | FAIL "found 0" |

Pure-function probes (gate code imported directly):
- select_manifest on RAW paths containing .agent/tasks/*.json → works (found 1 / found 2)
- the same list AFTER the gate's own normalize() (which is what
  changed_files() always produces) → "found 0" despite the manifest being
  present in the list.

Mapping to the required proofs: (a) legal WRITE_SET passes — S2/S5/S10a ✓;
(b) forbidden change fails — S1b/S4/S8a ✓; (c) overlapping WRITE_SET fails —
NOT ACHIEVABLE (S6a/S6b both pass; overlap enforcement is AI1's Conflict
Gate, procedural); (d) wrong BASE_COMMIT fails — S7a/S7b ✓; (e) main
modification is rejected — S8a ✓ when declared forbidden, but S8b shows the
gate is a manifest-coherence validator, not a main-protection mechanism:
main protection is the PR-only path + AI1-only merge, which is procedural
(the gate merely supports it at PR time); (f) AI1 integration remains the
only acceptance path — the automation contains no accept/merge/promote
authority whatsoever (the script only prints PASS/FAIL; the workflow only
runs the script on PRs), and PARALLEL-GOVERNANCE-v2 §7/§8 + AI1 controller
reserve the cycle to AI1 — verified by design review, not executable (and
that is the correct design: acceptance is procedural authority, not a script
exit code).

## Defects and classifications (R10)

Executable defects (reproduced with the unmodified gate @ e33b649):
- D1 workflow: `--base "$GITHUB_BASE_SHA"` references an env var that is not
  a GitHub Actions default and is defined nowhere in the workflow → CI
  always invokes the gate with an empty base. (S0/S0b.)
- D2 script: normalize() uses lstrip("./"), which strips the leading DOT of
  ".agent/..."; select_manifest then tests startswith(".agent/tasks/")
  against the already-normalized list → PR-local manifest auto-selection is
  structurally impossible; every PR fails "found 0" regardless of manifest
  presence (S1/S6c/S9/S10b; pure-function probe). This is the observed
  failure mode of all governance-gate CI runs to date.
- D3 script: pattern semantics (fnmatch "*" crosses "/") make
  FORBIDDEN_SET "governance/*.md" hit the audits/ deliverables (S1b) —
  the executable defect underlying AI3-GOV-PILOT-001 finding 9.
- D4 spec-vs-gate: TASK-DEPENDENCY-SCHEMA-v2 omits forbidden_set while the
  gate REQUIRES it (S3) — a schema-conformant manifest deterministically
  fails; one of the two must change.

Specification ambiguities (no implementation resolves them today):
- Pattern semantics of FORBIDDEN_SET (no dialect in play implements the
  intended direct-child reading) — needs one documented decision.
- Precedence policy is unstated in GOVERNANCE-GATES-v2 prose; the code's
  hard-veto choice is correct but undocumented.
- No load-time write_set∩forbidden_set disjointness validation; authors
  discover self-contradictions as scope failures.
- base_commit means "PR base", not "frozen task base" (S7a) — undocumented.
- Manifest filename↔task_id linkage and multi-task PR handling (the "found
  2" rule is unreachable via CI until D2 is fixed).
- depends_on/blocks/read_set/shared_interfaces are declared but enforced
  nowhere executable — acceptable for now, but should be labeled
  "procedural (AI1)" rather than implied executable.

Operational limitations (not defects):
- Worker-branch CI absence (0 runs on all audited HEADs); tests run only at
  PR (from the merge ref — which is the authoritative surface).
- Branch protection on main unverifiable without authenticated API access;
  all commits share one GitHub identity, so worker identities are procedural.
- Gate verdicts can flip when main moves between PR open and merge.
- Worktree layout deviations already reported in AI3-GOV-PILOT-001.

Acceptable design choices (validated as sound):
- Forbidden as a hard veto without write_set precedence (S4/S5b/S8a) — keep.
- base_commit cross-check (S7a) — keep; document its PR-base semantics.
- Exactly-one-PR-local-manifest rule — keep; becomes functional once D2 is
  fixed.
- The gate never executes acceptance.tests and holds no acceptance authority
  — correct separation; Test Gate execution stays with workers (local) and
  AI1 (integration).
- Gate logic itself: S10a proves the core scope validation is correct when
  reached with a reachable manifest.

## Conclusions

GATE VALIDATION: READY_FOR_AI1_DESIGN_REVIEW

EXECUTABLE CONFLICT: YES
(reproduced end-to-end: pilot FORBIDDEN_SET vs WRITE_SET — S1b; schema-v2
manifest rejected — S3; PR auto-selection impossible — S1/S9/S10b; CI
invocation broken — S0/S0b)

CI TRACEABILITY: WARN
(tests: obtainable at PR from the merge ref, absent on worker branches —
0 runs verified on all four audited HEADs; governance-gate at PR:
FAIL — mechanism dead on arrival via D1+D2, so no scope-gate evidence has
ever been produced by CI. Branch-level CI is not required for acceptance;
it is recommended for production workstreams only.)

PROPOSED NEXT ACTION: AI1 design review should adopt a minimal gate v2.2
bundle, in this order: (1) workflow — pass the real PR base explicitly
(e.g. env: BASE_SHA: ${{ github.event.pull_request.base.sha }}) and fail
fast on an empty value; (2) script — stop lstrip-ing leading dots in
normalize() (or select on raw paths), restoring manifest auto-selection;
(3) script+spec — one documented pattern-semantics decision: either
path-aware matching ("*" does not cross "/") aligning the gate with the
documented direct-child intent, or keep fnmatch and require disjoint
write_set/forbidden_set authoring — either way ADD a load-time
write∩forbidden disjointness check that fails as a manifest error;
(4) spec — add forbidden_set to TASK-DEPENDENCY-SCHEMA-v2 (S3 must flip);
(5) document base_commit = PR base semantics and the AI1 re-issue procedure
under base drift; (6) document cross-PR WRITE_SET overlap as AI1 Conflict
Gate responsibility (S6a/b show the scope gate cannot and should not do it);
(7) optionally add `push: branches: ['parallel/**']` to tests.yml for
production workstreams. Acceptance test for the fix: re-run this exact
scenario suite — S0b/S1/S3/S6c/S9/S10b must flip to their intended verdicts
while S4/S5/S5b/S7a/S7b/S8a/S8b/S10a hold their current ones. This task
implements none of the above.

## Scope / Change Audit

Everything above was produced read-only with respect to the real repository:
the scenario branches, commits, and manifests live in a throwaway temp clone;
the real repository's working tree was not modified beyond this task's
WRITE_SET file; no gate, workflow, manifest, or specification file was
changed; no fix was implemented; no authorization was created or inferred;
nothing was merged. The AI2 branch was not touched (its HEAD moved during
this task by AI2's own concurrent push, fe8fca6→d47decf, observed and
reported in AI3-GOV-PILOT-001).

## Task Completion

Audit performed against exact audited HEAD: e33b649189af17547c73a2e131f808c08baa62ed.

Final task status: validation complete — READY_FOR_AI1_DESIGN_REVIEW.
DONE is not acceptance; design decisions and any implementation remain
AI1-owned. No merge was performed; only this task branch was pushed.
