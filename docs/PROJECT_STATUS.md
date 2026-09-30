# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P14-C Contract Repair — EXPECTED_ABSENCE representation frozen — PASS / INDEPENDENTLY ACCEPTED** (Golden Re-freeze is the next gated stage)

P13-U has been independently accepted as PASS. P13-T remains a future data-condition gate and is **STOPPED / NOT EXECUTED** until a genuine virgin temporal holdout reaches the frozen execution threshold.

Current P13-U gate state at the last verified data run remains **ACCUMULATING**.

- `research_end = 2026-09-22`
- `virgin_start = 2026-09-23`
- last independently documented virgin trading days: **2** (2026-09-23, 2026-09-24)
- P13-T minimum execution condition: **20 trading days**
- P13-T recommended execution condition: **60 trading days**
- contamination detected in the last verified P13-U run: **False**

P14-A has been independently accepted as **PASS**.

P14 remains infrastructure/research-only. It must not consume the protected virgin zone or promote new information into production factors, policy, or calibration.

## Accepted Phases

| Phase | Status | Notes |
|---|---|---|
| P13-M | PASS | PIT-safe industry-relative factor study; no production promotion |
| P13-N | PASS | PIT factor hot-path optimization; golden outputs preserved |
| P13-O | PASS | Seven-factor stability analysis |
| P13-P | PASS | Independent factor validation; volatility remains research candidate only |
| P13-Q | PASS | Calibration research layer; research-only registry |
| P13-R | PASS | Recommendation/decision packet layer; research-only |
| P13-S | PASS | Deterministic research-report layer; LLM interface remains non-production |
| P13-T | STOPPED / NOT EXECUTED | No true evaluable virgin holdout was available |
| P13-U | PASS | Independently accepted virgin-holdout integrity gate; currently ACCUMULATING |
| P14-A | PASS | Information contract, provenance, PIT, freshness, revision, dedup/conflict infrastructure |
| P14-B | PASS | Independently accepted after durable ingestion-audit repair (P14-B-R1) |
| P14-C Contract Repair | PASS | EXPECTED_ABSENCE representation frozen; exact-head CI evidence independently verified; Golden Re-freeze is next |

**Important:** P13-U PASS does not mean P13-T PASS. P13-T remains pending until the frozen virgin zone reaches an executable holdout condition without contamination.

## Current Commit

`38bbf82340fd22fd196ea97639ce014e2bf15033`

Latest independently accepted implementation remains `84021d6c9039582cfa831e1e3a85f1141fb87efd` (P14-B baseline); `1961773d` is the current documentation-synchronized HEAD for the independently accepted P14-C Acceptance Harness Reset. The functional submission tree was independently verified at `3144a695`; `1961773d` adds only the acceptance-state documentation sync.

Independent review state: the latest independent verdict on the P14-C contract line is **Acceptance Harness Reset FAIL / REPAIR REQUIRED** (2026-10-01, `e881b09`, see its section at the end of this file); the CI/documentation repair it requires is delivered in this round and **awaits independent acceptance**.

Current accepted-head CI:
- workflow: `tests`
- run: `36650601210`
- HEAD: `84021d6c9039582cfa831e1e3a85f1141fb87efd`
- pytest job: success
- p13m job: success
- Full pytest: **all tests passed / 0 failed** (P14-B-R1 repair included)
- Full pytest step executed `python -m pytest -q -ra`
- P13-M regression step: success
- P14-A/P14-B tests are included in the full suite.

Current submission-head CI (P14-C Acceptance Harness + R4 repair, `3144a6951d33281af38e8663d394115148bb00d1`, awaiting independent acceptance):

- workflow: `tests`
- run: `36739506965` (event: push, completed / success, started 2026-09-30T15:48:16Z)
  - https://github.com/CGchenggang/a-stock-quantimental/actions/runs/36739506965
- pytest job (id `109969874122`): success — all steps green, including
  "Environment diagnostics" (`pytest --collect-only -q -ra`), "Full pytest suite"
  (`python -m pytest -q -ra`), and "P13-M pooled industry regression"
- p13m job (id `109969874447`): success — "P13-M pooled industry regression" step green
- Full pytest on the identical tree locally: **361 passed, 2 warnings, 0 failed**
  (includes the 14 harness meta-tests in `tests/contracts/p14c/`); the CI step's
  success conclusion is the machine-verifiable result for the same command on the
  same commit (job-log download requires admin rights and is not part of this record)
- Contract Harness executed via the pytest suite (characterization test
  `test_real_docs_characterization` runs `scripts/audit_p14c_contract.py::run_harness`
  against the real contract/matrix and asserts the counts below); direct script run
  on the same tree: `python scripts/audit_p14c_contract.py` → exit 0, status PASS
  - `contract_unique_ids = 61`, `matrix_unique_ids = 61`, `matrix_rows = 61`
  - `orphan_contract_invariants = 0`, `orphan_matrix_rows = 0`
  - `duplicate_contract_ids = 0`, `duplicate_matrix_ids = 0`, `undefined_matrix_ids = 0`
  - `hard_findings = 0`, `soft_findings = 0`

The immediately preceding documentation commit CI `36641360624` failed because a P14-A production-snapshot test incorrectly depended on a gitignored local calibration artifact. ZCODE fixed that test in the next commit; the current-head run `36642731938` is green. This failure/fix is retained as audit history rather than hidden.

## Current Research Boundary

### Consumed research zone

Last consumed decision date:

`2026-09-22`

P13-O/P13-Q/P13-R research consumed the OOS history through this date.

### Frozen virgin zone

`2026-09-23 onward`

No P13-Q/P13-R research pipeline may consume decision dates in this zone.

P13-U `assert_research_zone` is a fail-fast guard. Any decision date `>= 2026-09-23` entering the protected research entry points must raise an error.

P14 information-layer `select_asof` is also guarded by the same single-source boundary.

### P13-T execution rule

P13-T may only execute against a genuine virgin temporal holdout after the boundary is frozen and the minimum/recommended data condition is satisfied. Existing P13-R validation data must never be relabeled as holdout data.

## Data Boundary

- Validation universe: frozen 76-stock universe.
- Last documented P13-U data endpoint: **2026-09-24**.
- Virgin dates observed: 2026-09-23 and 2026-09-24.
- Missing symbols on both observed virgin dates: `000004`, `000016`.
- Missing data is reported; symbols are not silently dropped.
- P13-U checks date/symbol existence and integrity; it does not calculate performance metrics.
- Two stocks without SW1 membership remain subject to data-existence checking and are not silently removed.

P14-A used deterministic fixtures only. No production alpha factor or policy was changed.

**Reproducibility note:** `data/industry/` is intentionally ignored by `.gitignore`, so generated P13/P14 local data artifacts are not part of the GitHub commit. Acceptance therefore distinguishes source/CI verification from local data-state evidence.
## Frozen Parameters

- `RESEARCH_END = 2026-09-22`
- `VIRGIN_START = 2026-09-23`
- `MINIMUM_VIRGIN_TRADING_DAYS = 20`
- `RECOMMENDED_VIRGIN_TRADING_DAYS = 60`
- 76-stock validation universe
- P13-Q calibration registry
- P13-R policy registry
- P13-R cost/risk assumptions
- P13-S report schema
- P13-T determination
- P13-O consumed-date audit boundary
- P14-A information contract
- P14-A source category/freshness registry
- P14-A PIT semantics

## Known Limitations

1. P13-T has not produced final holdout metrics because the virgin zone is still too short.
2. P13-U cannot prove arbitrary runtime reads that leave no auditable artifact; its contamination check covers the defined consumed-date set and known research artifacts.
3. Trading-day identification uses actual universe data rather than an external exchange calendar; missing coverage is therefore reported explicitly.
4. The virgin zone currently contains only two documented trading days, so no model/policy performance conclusion may be drawn from it.
5. P13-U is an integrity gate, not a prediction or recommendation stage.
6. P13-U does not automatically execute P13-T when the threshold is reached; independent acceptance is still required.
7. Research-only calibration/policy discoveries remain non-production until independently validated.
8. P14-A uses fixture sources; real external source adapters have not yet been admitted.
9. P14-A freshness windows are explicit infrastructure defaults, not empirically validated alpha assumptions.
10. Conflict resolution/source precedence is intentionally not implemented; conflicting records remain preserved with provenance.
11. Local generated information artifacts are intentionally outside Git version control.

## P14 Roadmap

### P14-A — PASS

Information contract and PIT/provenance infrastructure:
- canonical information record;
- event_time vs available_time;
- PIT inclusive boundary;
- late-arriving information;
- revision visibility;
- provenance validation;
- explicit freshness policy;
- deterministic deduplication;
- conflict detection without arbitrary resolution;
- research-only records;
- P13-U virgin protection;
- deterministic audit.

### P14-B — PASS

**Source Adapters & Immutable Raw Information Store**

Build the controlled ingestion boundary:

`external source → raw immutable record → provenance → normalization → PIT-safe research layer`

Representative sources only; no broad source-count optimization.

### P14-C — IN PROGRESS / NEXT

Data quality/reconciliation and source health:
- completeness;
- missingness;
- timestamp anomalies;
- revision anomalies;
- duplicate/conflict monitoring;
- freshness monitoring;
- source health;
- deterministic quality reports.

### P14-D — planned

Research information query layer:
- as-of information retrieval;
- entity/time indexing;
- cross-market alignment;
- PIT-safe joins;
- research-only information snapshots.

### P14-E — planned

Representative multi-market source coverage:
- A-share market;
- company/public information;
- macro;
- overseas market.

Only after the P14-B/C contracts are stable.

### P14-F — planned

Information-to-research integration:
- candidate information features;
- research-only feature registry;
- no production promotion;
- no policy/calibration mutation.

### P14-G — planned
Agent-facing information interface:
- auditable retrieval;
- provenance citations;
- available-time semantics;
- freshness;
- deterministic research packets.

### P13-T — parallel future gate

P13-T remains independent of P14 development. Once the virgin zone reaches the agreed execution condition, stop new research consumption of that zone, freeze the manifest, and execute the pre-registered holdout evaluation.

## Acceptance Criteria

### General

A stage is accepted only after independent inspection of:
- implementation/code;
- tests;
- data and boundary semantics;
- PIT/future-data leakage controls;
- reproducibility;
- production diff;
- GitHub Actions CI;
- workflow jobs and steps;
- acceptance documentation.

ZCODE's acceptance report is evidence, not the final acceptance decision.

### P14-A

**Independent acceptance: PASS.**

Verified:
- canonical information record exists;
- event_time and available_time semantics are separated;
- PIT uses `available_time <= decision_time`;
- late-arriving information is handled by available_time;
- revision visibility cannot leak future revisions backward;
- provenance is explicit and unresolved/invalid records are rejected;
- freshness is separate from PIT and uses explicit source policy;
- deduplication is deterministic and order-independent;
- conflicting sources are preserved and marked, not silently resolved;
- normalization is deterministic;
- repeated outputs are byte-identical in the deterministic audit/tests;
- P13-U virgin boundary is shared as a single source of truth;
- P14 information selection fails fast on virgin decision dates;
- P13-Q/P13-R guards remain active;
- no new production factor/policy/calibration/recommendation logic was introduced;
- the current GitHub Actions run `36642731938` is green at current HEAD;
- full pytest is 281 passed / 2 warnings / 0 failed;
- P13-M regression is green;
- the transient preceding CI failure was corrected without weakening the invariant.

### P13-T future acceptance

P13-T may be accepted only if:
1. a true virgin temporal holdout exists;
2. the holdout boundary is frozen before evaluation;
3. no discovery/tuning/registry write-back uses holdout observations;
4. PIT and future-row immunity pass;
5. frozen manifest hashes are verified;
6. required metrics and risk/cost analysis are produced under the pre-registered protocol;
7. results are deterministic;
8. full pytest and required regression CI are green;
9. no unvalidated policy/factor/calibration changes are promoted to production.

### P14-B acceptance

P14-B may be accepted only after independent verification of:
1. raw source records are immutable after ingestion;
2. every raw record has source provenance and ingestion metadata;
3. adapter output maps deterministically into the P14-A contract;
4. adapter timestamps preserve source semantics and do not substitute ingestion time for available_time;
5. late-arriving and revised source records are preserved rather than overwritten;
6. raw storage is append-only/versioned;
7. duplicate ingestion is idempotent;
8. failed/partial ingestion cannot silently produce valid research records;
9. source failures/missing data are observable;
10. PIT-safe normalization still uses P14-A rules;
11. P13-U virgin protection remains intact;
12. no production factor/policy/calibration mutation occurs;
13. full pytest, P13-M regression, P13-U tests and all P14-B tests pass in GitHub Actions;
14. workflow job/step logs are independently inspected;
15. deterministic repeated ingestion produces byte-identical normalized results;
16. acceptance documents match actual code and CI.

## P14-B Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-C.**

Independently verified against HEAD `98bfe54bc76e0511e66feb57768b6456c9bf612a`:
- P14-B implementation, tests, research plan, raw-store audit and acceptance report inspected.
- GitHub Actions run `36647967677` is green: pytest and p13m jobs both succeeded; full pytest reported **302 passed / 2 warnings / 0 failed** and the P14-B 21-test block passed.
- Production diff from P14-A baseline `89349da` contains only P14-B information-ingestion infrastructure/tests/docs; no factor/policy/calibration/recommendation promotion was observed.
- P13-U virgin protection remains wired through the shared boundary and the dedicated P14-B virgin-zone test passes.

**Blocking finding:** P14-B documentation/research plan states that a same-key/different-payload mutation is recorded as a rejected ingestion attempt and that ingestion outcomes are auditable. In `RawStore.put()`, however, `DUPLICATE` and `RAW_MUTATION_DETECTED` outcomes are appended only to the in-memory `_outcomes` list; only accepted records are persisted to the JSONL file. After process restart/reload, the rejected mutation/duplicate attempt evidence is therefore not durable. This is inconsistent with the claimed immutable/auditable raw-ingestion boundary and is not merely a documentation issue.

**Required repair before re-acceptance:** persist ingestion-attempt audit events (including at minimum DUPLICATE and RAW_MUTATION_DETECTED, with source/source_id/revision, incoming payload hash, stored hash when applicable, ingestion_id, adapter_version, outcome, and deterministic audit metadata) in an append-only durable audit representation; reload must reconstruct the audit history; add restart/reload tests proving the evidence survives process boundaries; preserve byte-identical deterministic replay; keep accepted raw records immutable; keep P13-U/P14-A boundaries unchanged; rerun full CI and provide updated P14B docs. Do not start P14-C until this repair is independently accepted.

## P14-B Independent Re-acceptance — 2026-09-30

**Decision: PASS.**

Independently re-audited after P14-B-R1 against HEAD `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

Verified:
- `RawStore` now persists a separate append-only `raw_ingestion_audit.jsonl`; ACCEPTED canonical records remain in `raw_records.jsonl`.
- DUPLICATE and RAW_MUTATION_DETECTED events survive process restart; mutation events preserve incoming and stored hashes and never overwrite the canonical record.
- Adapter-level REJECTED / SOURCE_ERROR / AUTH_ERROR / TIMEOUT events are durably audited.
- Frozen `RawIngestRecord` availability semantics are derived at construction; no post-construction `__dict__` mutation remains in adapters.
- Restart, append-only, deterministic replay, no-duplicate-canonical-record, partial-failure and source-failure tests are present and passing.
- P14-A normalization/PIT semantics and P13-U virgin-zone protection remain intact.
- Production diff from P14-A baseline contains P14-B ingestion infrastructure/tests/docs only; no factor/policy/calibration/recommendation promotion was observed.
- GitHub Actions run `36650601210`: pytest and p13m jobs both SUCCESS; all workflow steps inspected and Full pytest SUCCESS.

P14-B is therefore accepted. P14-C is the next phase.

## Operating Rule

When a new ZCODE stage is reported complete:

1. Inspect the GitHub diff and current HEAD.
2. Inspect implementation and tests.
3. Inspect data/provenance/PIT boundaries.
4. Verify CI from workflow jobs/steps, not merely from status claims.
5. Compare production-zone changes against the frozen baseline.
6. Decide PASS / FAIL / STOPPED independently.
7. Update this file in the same repository when the project state changes materially.
8. If PASS, issue the next ZCODE task prompt.
9. If FAIL, issue focused repair tasks and do not advance the phase.
10. If STOPPED because a data condition is not met, build/maintain integrity infrastructure rather than fabricating evidence.

Last independently updated: 2026-09-30.
Independent P14-A acceptance recorded against HEAD `89349da30e656a571c7f97a4344a46502c3336ae`.


## P14-C Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Independently inspected against P14-B accepted baseline 84021d6c9039582cfa831e1e3a85f1141fb87efd and P14-C HEAD 7f31d1f3807109625b459403f040eb2a7d5eb8f8.

Blocking findings:
1. The claimed deterministic P14-C audit does not actually exercise all declared anomaly classes. In particular, the fixture/audit path does not create durable SOURCE_ERROR/PARSE_FAILURE evidence or a genuine missing-entity/date completeness case, despite the acceptance document claiming those anomalies are covered.
2. run_p14c_quality_audit.py computes source-health freshness with a hard-coded stale_n = 0 and passes stale: 0 to source_health. Therefore the audit artifact cannot detect/report stale-source health even though the implementation and plan claim STALE monitoring.
3. Completeness is reduced to every registered fixture source having at least one accepted row. It does not implement expected entities/dates versus actual entities/dates, missing entities, missing dates, or coverage ratio required by the P14-C contract.
4. The reconciliation output preserves values and provenance, but the integration audit does not demonstrate the required cross-source timestamp/provenance fields in its emitted reconciliation artifact beyond the minimal source records; this needs explicit end-to-end assertions.
5. P14-C CI evidence is not independently available from fetch_commit_workflow_runs for the current HEAD, so the claimed CI result cannot be treated as independently verified yet. A green local/test claim is insufficient for acceptance.

Required repair:
- implement real completeness/missingness accounting over explicit expected entity/date sets;
- add deterministic SOURCE_ERROR, PARSE_FAILURE, SOURCE_EMPTY, EXPECTED_ABSENCE and UNEXPECTED_MISSING evidence paths;
- derive fresh/stale/unresolved source-health metrics from actual audit evidence, never hard-code stale=0;
- make reconciliation end-to-end evidence explicit for values, differences, timestamps and provenance;
- add regression tests for each blocking invariant and deterministic double-run/manifest output;
- run and expose GitHub Actions CI for the repair HEAD, including full pytest, P13-M/P13-U protection and P14-C tests;
- preserve P13-U virgin boundary and do not introduce P13-T, factor, policy, calibration, recommendation, or production-alpha changes.

P14-D remains blocked until P14-C is independently re-accepted.


## P14-C Recheck — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Independently rechecked current HEAD `c5f2a86f17ce2978f7c50292af2e41915a5db8aa` against P14-B accepted baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

Blocking findings:
1. The current `completeness.json` design remains source-presence based rather than entity/date completeness. The audit documentation reports `expected_sources` versus `sources_with_accepted_rows`, but there is no independently evidenced expected-entity set, expected-date set, actual-entity/date set, missing entities, missing dates, or coverage ratio required by the P14-C repair gate.
2. The repository search and inspected audit material do not provide an independently verifiable durable evidence path for each required anomaly class: `SOURCE_ERROR`, `PARSE_FAILURE`, `SOURCE_EMPTY`, `EXPECTED_ABSENCE`, and `UNEXPECTED_MISSING`. The vocabulary and classifier exist, but declaring fixture coverage is not sufficient; the emitted audit artifacts must prove each path.
3. GitHub Actions evidence for current HEAD is not independently available through the current workflow-run lookup. The current-head run therefore cannot be accepted merely from documentation claims.
4. The claimed P14-C production diff is inaccurate: comparing `84021d6..c5f2a86` shows substantial additions outside the intended P14-C source/tests/docs boundary, including large `data/raw`, `data/clean`, and `workspace/` artifacts. The P14-C acceptance document's statement that the production diff is empty is therefore not an auditable description of the actual repository diff.
5. The current status document still records the earlier P14-C FAIL and does not record a valid independent re-acceptance. This is appropriate; no phase advancement is authorized.

Required next repair:
- implement explicit expected entity/date sets and actual entity/date coverage with deterministic missing-entity/missing-date accounting and coverage ratio;
- emit durable, inspectable evidence for all five required missingness/anomaly paths, including real source-error/parse-failure evidence rather than classifier-only tests;
- ensure source-health freshness is derived from actual P14-A freshness evidence and audit inputs, with no hard-coded stale count;
- make reconciliation integration artifacts explicitly preserve both source values, difference, event/available/ingested timestamps, provenance, and policy metadata;
- remove unrelated generated `data/` and `workspace/` artifacts from the P14-C repair diff (or justify and separately scope them); do not mix them into the acceptance boundary;
- provide a CI run on the final repair HEAD and make run/job/step evidence independently inspectable;
- preserve P13-U virgin protection and keep P13-T STOPPED;
- no factor, policy, calibration, recommendation, or production-alpha changes;
- after repair, stop and await independent acceptance. Do not mark PASS or start P14-D.


## P14-C-R2 Repair — 2026-09-30

R2 repair implemented: real completeness (expected/actual entities+dates with coverage_ratio), SOURCE_ERROR/PARSE_FAILURE/SOURCE_EMPTY evidence chain through audit_event→quality→health, freshness computed from P14-A policies (no hardcoded stale), reconciliation groups carry full provenance+timestamps, quality_report.json restructured into 9 dimensions with status/reasons/metrics/evidence.


## P14-C-R2 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Independently re-audited current HEAD `63487fdc3bcd014bd98a86eea0545cf8d7415e09` against P14-B accepted baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.
Blocking findings:
1. The R2 script declares `EXPECTED_CONTRACT`, but `_compute_completeness()` derives expected entities/dates from the actual fixture payloads instead of consuming an explicit expected contract. Therefore the expected set is not independent of the observed data and cannot detect a missing entity/date caused by ingestion failure. The `broken_source` entry also has no actual adapter path in `_payload_adapters()`; it is not exercised by the ingestion/evidence chain.
2. The required durable SOURCE_ERROR/PARSE_FAILURE evidence chain is not demonstrated by the inspected final audit path. The script comments claim a broken source and parse failure, but the adapter map only contains the four normal fixture adapters; the declared broken/empty fixture is not actually ingested through that map. This remains a fixture-coverage/evidence problem, not a vocabulary problem.
3. Reconciliation implementation `src/astock_v2/information/reconciliation.py` itself only emits source, source_id, value, available_time; event_time/ingested_at/ingestion_id/raw hash/provenance are appended later by the audit script. This can be acceptable architecturally, but there is no independently visible end-to-end test in the inspected P14-C test set that asserts all required final artifact fields. The acceptance claim therefore remains insufficiently locked by regression tests.
4. GitHub Actions evidence for the final R2 HEAD is absent from the workflow-run lookup (`workflow_runs: []`). Local/documentation claims cannot substitute for independently verifiable CI evidence.
5. The P14-C diff still adds generated test artifacts under `tests/_p13s_immunity_tmp/` and `tests/_p13u_store*_tmp/`. These are runtime/generated artifacts and should not be part of a clean phase implementation diff. The earlier generated-data cleanup therefore did not fully restore repository hygiene.
6. The repository status currently says “implementation complete; awaiting independent acceptance”, which is acceptable as a handoff state, but no PASS/phase advancement is authorized.

Required R3 repair:
- use an explicit immutable expected entity/date contract independent of actual payloads;
- exercise real deterministic SOURCE_ERROR and PARSE_FAILURE ingestion attempts through the audit path and persist their evidence;
- add end-to-end tests against the emitted reconciliation.json asserting source/value/difference/event_time/available_time/ingested_at/ingestion_id/raw hash/provenance/policy metadata;
- obtain a GitHub Actions run on the final repair HEAD and make pytest/P13-M/P14-C results independently inspectable;
- remove generated test artifacts from the repository and extend .gitignore as needed;
- preserve P13-U/P13-T boundaries and make no factor/policy/calibration/recommendation/production-alpha changes;
- stop after R3 and await independent acceptance. Do not start P14-D.


## P14-C-R3 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Independently audited the latest P14-C implementation HEAD `868b729ae862b750fb8c6a834b80596553be6fea` against accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Blocking findings

1. `run_p14c_quality_audit.py` is not executable as written: the `expected_absence` branch of `_compute_completeness()` does not initialize `expected_count` and `actual_count`, but both are emitted later. The declared `broken_source` case therefore cannot produce a valid completeness artifact.
2. `_compute_freshness_per_record()` references `FRESH` and `STALE` without importing those constants. This is a second direct execution blocker.
3. `parse_failure_source` is not included in `EXPECTED_CONTRACT`, so the parse-failure path lacks an independent expected entity/date contract.
4. SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY are not locked by an end-to-end regression test covering adapter failure → durable `raw_ingestion_audit.jsonl` → quality classification → source health → final `quality_report.json`.
5. `tests/test_p14c_reconciliation.py` only tests `reconcile()` directly; it does not execute `run_quality_audit(tmp_path)` and assert the final `reconciliation.json` fields required by the R3 contract.
6. GitHub Actions evidence is absent for latest HEAD: `fetch_commit_workflow_runs` returns `workflow_runs: []` and combined commit status is empty. Final CI therefore cannot be independently verified.
7. `docs/P14C_ACCEPTANCE.md` is stale relative to the latest implementation and lacks current-head CI evidence; its fixture/diff claims cannot be used as acceptance evidence.

### Positive findings

- An explicit `EXPECTED_CONTRACT` now exists and completeness consumes it rather than deriving expected sets from normal fixture payloads.
- Deterministic BrokenSourceAdapter and ParseFailureAdapter implementations now exist.
- Freshness is intended to reuse the P14-A freshness policy rather than a hard-coded stale count.
- No factor, calibration, recommendation, or P13-T promotion was observed; P13-T remains STOPPED and the documented virgin boundary remains `research_end=2026-09-22`, `virgin_start=2026-09-23`.

### Required R4 repair

- Make the audit script execute successfully from a clean directory and add direct smoke coverage for it.
- Fix expected-absence count/coverage semantics deterministically.
- Correctly import/use P14-A freshness constants; no second freshness policy and no hard-coded stale count.
- Add parse-failure source to the independent contract where required and prove SOURCE_ERROR/PARSE_FAILURE/SOURCE_EMPTY through the durable evidence chain and final artifacts.
- Add end-to-end audit regression tests, including reload of durable audit evidence.
- Add `reconciliation.json` end-to-end assertions for source, source_id, value, difference, relative_difference, event_time, available_time, ingested_at, ingestion_id, raw_payload_hash, provenance, policy_id, policy_version and status.
- Run clean double-run determinism checks.
- Keep the P14-C diff bounded to relevant source/tests/scripts/docs/.gitignore; remove generated artifacts.
- Push the repair and obtain independently inspectable GitHub Actions evidence for pytest, P13-M and full pytest; inspect run/job/step results.
- Preserve P13-U/P13-T boundaries and do not modify factor/policy/calibration/recommendation/production-alpha logic.
- Stop after repair and await independent acceptance. Do not start P14-D.

P14-D remains blocked.


## P14-C-R4 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Latest HEAD: `0ecfdac372ddfca2d8ab59a301c74af1b9fa1f2a`.
Accepted P14-B baseline: `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings

- The two R3 runtime errors were addressed: expected-absence counts are initialized and freshness constants are imported from the P14-A layer.
- An explicit module-level EXPECTED_CONTRACT is now used by completeness.
- R4 adds an end-to-end audit test that reads final JSON artifacts from disk and checks reconciliation provenance/timestamps, durable SOURCE_ERROR/REJECTED/ACCEPTED outcomes, stale evidence, deterministic manifest, and P13-U/P13-Q/P13-R guards.
- No P13-T/factor/calibration/recommendation promotion was observed.

### Blocking findings

1. **No independently verifiable CI run for the final HEAD.** GitHub Actions lookup for `0ecfdac372ddfca2d8ab59a301c74af1b9fa1f2a` returns `workflow_runs: []`. Therefore the required final pytest/P13-M/full-suite evidence is absent. This alone blocks acceptance.
2. **SOURCE_EMPTY is not actually locked end-to-end by the new R4 test.** The durable-audit test asserts SOURCE_ERROR, REJECTED and ACCEPTED, but does not assert a SOURCE_EMPTY outcome/artifact. The `broken_source` fixture is simultaneously wired to BrokenSourceAdapter (which raises SOURCE_ERROR) while EXPECTED_CONTRACT marks it expected_absence=True; this conflates failure/empty/expected-absence semantics rather than independently proving all required paths.
3. **EXPECTED_ABSENCE / SOURCE_EMPTY / SOURCE_ERROR are not cleanly separated in the completeness contract.** The expected_absence branch unconditionally emits EXPECTED_ABSENCE, even when the same source's actual adapter path is a fetch error. A single source should not be used to stand in for multiple distinct anomaly classes in the final evidence contract.
4. **The R4 test for independent expected contract does not actually simulate a missing payload and assert the resulting missing date/coverage.** It only checks that the constant contains two dates. The key invariant should be exercised by removing one actual payload or injecting an adapter failure against an expected entity/date while leaving EXPECTED_CONTRACT unchanged, then asserting missing_dates and coverage_ratio < 1.
5. **The R4 acceptance document remains stale/inaccurate.** It still says `git diff 84021d6..HEAD -- src/astock_v2 = 空`, but the actual compare shows src/astock_v2/information/__init__.py and raw_store.py modifications. The latter includes P14-C freshness-policy propagation, which may be legitimate, but the documentation must accurately state and justify the boundary rather than claim an empty diff.

### Required R5 repair

- Keep R5 narrowly focused; do not add new P14-C functionality.
- Obtain an actual GitHub Actions run for the final HEAD and independently inspect workflow → job → step evidence for pytest, P13-M and full pytest.
- Separate deterministic fixtures/contracts for SOURCE_ERROR, PARSE_FAILURE, SOURCE_EMPTY, EXPECTED_ABSENCE and UNEXPECTED_MISSING. Do not make one source simultaneously represent incompatible anomaly classes.
- Add a real missing entity/date regression: mutate/remove actual fixture ingestion while leaving EXPECTED_CONTRACT unchanged, then assert missing entity/date and coverage ratio < 1.
- Add final-artifact assertions for SOURCE_EMPTY and the distinct missingness classes, including durable evidence where applicable.
- Update docs/P14C_ACCEPTANCE.md to exactly match the current implementation and actual 84021d6..HEAD diff; explicitly justify any P14-B source change required by P14-C.
- Run clean-directory audit twice and compare deterministic artifacts byte-for-byte; run python -m pytest -q -ra locally.
- Keep P13-U boundary research_end=2026-09-22, virgin_start=2026-09-23; keep P13-T STOPPED/NOT EXECUTED; no factor/policy/calibration/recommendation/production-alpha changes.
- Stop after repair and await independent acceptance. Do not start P14-D.

P14-D remains blocked.

## P14-C-R5 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-D.**

Independently audited the latest P14-C-R5 implementation HEAD `f7bd995129721d5547dcd4e63b0377dc0d3bb012` against the accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings

- R5 does introduce dedicated fixture paths for SOURCE_ERROR, PARSE_FAILURE, SOURCE_EMPTY and an explicit expected entity/date contract.
- A real missing-date regression now asserts that the fixed contract remains unchanged, `2026-03-04` is reported as missing, and coverage is below 1.0.
- Final-artifact tests cover reconciliation provenance/timestamps, stale evidence and deterministic manifests.
- P13-U boundary remains `research_end=2026-09-22`, `virgin_start=2026-09-23`; no P13-T execution or factor/policy/calibration/recommendation promotion was observed.

### Blocking findings

1. **No independently verifiable GitHub Actions result for the final R5 HEAD.** `fetch_commit_workflow_runs` returns `workflow_runs: []`, and combined commit status is empty for `f7bd995...`. Therefore the required final CI evidence cannot be accepted. The workflow definition does contain full pytest and P13-M jobs, but there is no run/job/step evidence for this commit.
2. **EXPECTED_ABSENCE is still conflated with SOURCE_ERROR on the same fixture/source.** `broken_source` is a BrokenSourceAdapter that raises SOURCE_ERROR, while its EXPECTED_CONTRACT entry also sets `expected_absence=True`. The R5 test explicitly asserts both properties. This violates the R5 requirement that incompatible anomaly semantics be represented by separate deterministic fixtures/contracts. The classifier priority merely hides the semantic collision; it does not make the evidence contract clean.
3. **SOURCE_EMPTY is not represented by a durable ingestion evidence event.** The R5 test accepts the absence of any raw audit event for `source_empty_source` and infers SOURCE_EMPTY from the adapter report/completeness artifact. That can be a valid source-level observation, but it does not satisfy the stronger end-to-end evidence-chain standard previously required for failure/empty anomalies unless the adapter-level EMPTY_SUCCESS observation itself is explicitly persisted/audited. At minimum, the final contract should state and test whether SOURCE_EMPTY is an adapter observation or a durable ingestion event, rather than silently treating “no audit events” as proof.
4. **Acceptance documentation is still stale relative to the final implementation.** `docs/P14C_ACCEPTANCE.md` describes “10 deterministic fixtures” and still states `git diff 84021d6..HEAD -- src/astock_v2 = 空`, while the actual compare from the accepted P14-B baseline contains `src/astock_v2/information/__init__.py` and `raw_store.py` changes in addition to the new P14-C modules/tests. The raw-store freshness-policy propagation may be legitimate, but the acceptance document must describe and justify it accurately.

### Required R6 repair

- Do not add P14-D or new P14-C functionality.
- Push a final commit and obtain a real GitHub Actions run for that exact HEAD; independently inspect workflow → job → step evidence for the pytest job, P13-M regression and Full pytest suite.
- Split EXPECTED_ABSENCE onto its own dedicated deterministic source/fixture. `broken_source` must represent SOURCE_ERROR only; no source may carry both SOURCE_ERROR and EXPECTED_ABSENCE semantics.
- Decide and document the SOURCE_EMPTY evidence contract. Prefer an explicit durable adapter/source-observation event (for example EMPTY_SUCCESS) in the audit artifact, and add an E2E assertion for that event; do not use “no raw events exist” as the sole proof of SOURCE_EMPTY.
- Update `docs/P14C_ACCEPTANCE.md` to match the exact R5/R6 implementation and actual `84021d6..HEAD` diff, including justification for any `raw_store.py` change.
- Run `python -m pytest -q -ra`, clean-directory double-run determinism, and remove generated artifacts.
- Preserve P13-U/P13-T boundaries and make no factor/policy/calibration/recommendation/production-alpha changes.
- Stop after repair and await independent acceptance. Do not start P14-D.

P14-D remains blocked.

## P14-C Contract Repair R2 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Contract is NOT frozen. Do not start Golden Tests.**

Independently reviewed R2 HEAD `ea2e72846551fb48d6452f8064f9062e1ff418ae` against accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings

- EXPECTED_ABSENCE semantics are now internally consistent: `EXPECTED_CONTRACT` contains only `expected_entities` / `expected_dates`; stale `expected_absence=True` references were removed.
- Contract invariant identifiers were canonicalized to the `P14C-*` namespace.
- The R2 delta from `9a5d399` to `ea2e728` is documentation-only (`docs/PROJECT_STATUS.md` and `docs/contracts/P14-C-DESIGN-CONTRACT.md`).
- P13-U/P13-T boundaries remain unchanged.

### Blocking finding

**Contract ID ↔ Acceptance Matrix traceability is still not bidirectionally closed.**

Independent extraction of the current documents found:

- Design Contract IDs: **46 unique**
- Acceptance Matrix IDs: **41 unique**
- Contract IDs without a Matrix row: **18**
  - `P14C-EVID-004/005`
  - `P14C-COMP-005`
  - `P14C-TS-001..004`
  - `P14C-DUP-001..004`
  - `P14C-FRESH-004`
  - `P14C-PROV-A-001`
  - `P14C-PROV-B-001`
  - `P14C-DET-003`
  - `P14C-RR-001..003`
- Matrix IDs without a Design Contract invariant: **13**
  - `P14C-MISS-005/006`
  - `P14C-REV-001..003`
  - `P14C-RECON-006`
  - `P14C-SH-004..006`
  - `P14C-BND-001..004`

Therefore the claimed bidirectional closure remains false. The R2 commit canonicalized existing IDs but did not complete the required one-to-one Contract ↔ Matrix registry.

### CI evidence

No GitHub Actions workflow run or combined status is independently available for R2 HEAD `ea2e728`. Because this is a documentation-only contract stage, the missing CI evidence is secondary to the direct contract traceability failure, but it must still be obtained before final acceptance if the repository workflow requires CI evidence for the frozen contract.

### Required R3 repair

- Keep the repair documentation-only.
- Build one canonical invariant registry: every Design Contract invariant gets exactly one `P14C-*` ID.
- Add Matrix rows for all currently orphaned Contract IDs.
- Either define every currently orphaned Matrix ID as a formal Contract invariant, or remove the Matrix row if it is not a contract requirement. Preferred: retain requirements only when explicitly defined in the Design Contract.
- Perform a mechanical bidirectional audit and record:
  - `orphan_contract_invariants = 0`
  - `orphan_matrix_rows = 0`
  - `duplicate_contract_ids = 0`
  - `undefined_matrix_ids = 0`
- Verify invariant wording is aligned between Contract and Matrix.
- Keep EXPECTED_ABSENCE semantics as currently repaired; do not reintroduce fixture-specific fields.
- Do not modify `src/`, `tests/`, `data/`, `scripts/`, P13-T/U, factors, policy, calibration, recommendation logic, or production-alpha logic.
- Do not create Golden Tests yet.
- Obtain inspectable CI evidence for the final R3 HEAD if required by the repository workflow.
- Stop and await independent acceptance.

P14-D remains blocked.

## P14-C Contract Reset Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Contract is NOT frozen. Do not start Golden Tests and do not advance to implementation or P14-D.**

Independently reviewed current HEAD `a3f22a894e7de3c7b8c520bd65de28cba5034b05` and the four Contract Reset documents against the accepted P14-B boundary `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings
- The reset correctly identifies the major R1-R5 root causes and explicitly separates Design Contract, semantic, E2E, CI, documentation and hygiene problems.
- The expected entity/date contract is explicitly intended to be independent of actual payloads.
- The missingness taxonomy explicitly distinguishes SOURCE_ERROR, PARSE_FAILURE, SOURCE_EMPTY, EXPECTED_ABSENCE and UNEXPECTED_MISSING.
- P14-A is retained as the sole PIT/freshness authority, and the P13-U/P13-T research boundary is preserved.
- The Acceptance Matrix correctly postpones Golden Test implementation until after independent Contract review.

### Blocking findings
1. **Evidence Contract is internally contradictory.** INV-EVID-001 says every ingestion attempt must have a durable event in the durable audit file, while SOURCE_EMPTY is defined as only an `IngestionReport(status=EMPTY_SUCCESS)`. INV-EVID-003 also requires SOURCE_EMPTY evidence not to exist only in memory, but the contract never defines the durable persistence location and restart semantics for that report.
2. **`expected_empty` is a fixture/test concern incorrectly embedded in EXPECTED_CONTRACT.** The expected contract is supposed to be the production authority for what should exist; `expected_empty=True = deliberate SOURCE_EMPTY fixture` mixes test construction with domain expectation and risks recreating the semantic conflation that R4/R5 exposed.
3. **Revision integrity is missing as a formal Design Contract section.** Scope mentions revision gap / duplicate revision / payload mutation / available_time regression, and the Acceptance Matrix invents P14C-REV-001..003, but the Design Contract contains no corresponding revision invariants.
4. **The nine quality dimensions are not frozen.** The Acceptance Matrix requires a `nine_dimensions` fixture, while the Design Contract never enumerates the nine dimensions, their names, status domain, metrics/evidence schema, or required output structure.
5. **Provenance Contract is over-broad and conflicts with non-record anomaly cases.** It says every final quality judgment must trace to raw_payload/raw_payload_hash/ingestion_id/available_time/ingested_at, but EXPECTED_ABSENCE, SOURCE_EMPTY and UNEXPECTED_MISSING can legitimately have no canonical record/raw payload. The contract needs an explicit distinction between record provenance and source-observation/completeness provenance.
6. **Completeness semantics for EXPECTED_ABSENCE are underspecified.** The contract simultaneously defines `expected_pairs` from entity×date and says `expected_absence=True` means expected=0/coverage=1.0, but does not define how a source containing both required pairs and explicitly absent pairs is represented or excluded from the denominator.
7. **Acceptance Matrix contains mappings without corresponding frozen Contract IDs.** Missingness and revision rows use P14C-MISS-* and P14C-REV-* IDs, but those IDs are not defined as invariants in the Design Contract. This is a contract-to-test traceability gap.

### Required Contract Reset repair
- Repair the Design Contract only; do not modify `src/`, implementation tests, production logic, P13-T, P13-U, factors, policy, calibration or recommendation logic.
- Define one authoritative durable evidence model for SOURCE_EMPTY, including the exact persisted event/observation type, storage location, reload semantics and E2E evidence chain.
- Remove fixture-specific `expected_empty` from the domain expected contract, or explicitly prove a domain-level meaning independent of testing; preferred design is to keep expected contract about expected coverage and source observation about what actually happened.
- Add a formal Revision Integrity Contract with invariant IDs matching the Acceptance Matrix and define payload mutation versus P14-B immutable raw-store mutation semantics.
- Freeze the nine quality dimensions and their exact schema/allowed statuses/reasons/metrics/evidence fields, or remove the nine-dimension requirement from the matrix until the schema is explicitly frozen.
- Split record provenance from source-observation/completeness provenance so anomaly cases without records remain fully auditable.
- Define how EXPECTED_ABSENCE interacts with expected_pairs, expected_count, actual_pairs and coverage when a source has a mixture of required and intentionally absent entity/date pairs.
- Ensure every Acceptance Matrix Contract ID maps to an explicit invariant in the Design Contract, and every Design Contract invariant has at least one matrix row.
- Keep the research boundary `research_end=2026-09-22`, `virgin_start=2026-09-23`; keep P13-T STOPPED / NOT EXECUTED.
- Stop after the documentation-only repair and await independent Contract review. Do not write Golden Tests yet.

P14-D remains blocked.
## P14-C Contract Repair Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Contract is NOT frozen. Do not start Golden Tests.**

Independently reviewed Repair HEAD `9a5d399750eba4fbbd472f55e6a5f9a15fc43e7e` against accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings
- SOURCE_EMPTY now has an explicit durable evidence model in `raw_ingestion_audit.jsonl`, including restart/replay semantics and separation from canonical raw records.
- Fixture-only `expected_empty` was removed from the EXPECTED_CONTRACT structure.
- Revision Integrity, nine quality dimensions, and separate record-vs-observation provenance are now formally documented.
- Completeness defines entity/date/pair sets and an explicit denominator rule.
- Repair diff is documentation-only: the compare from `a3f22a8` to `9a5d399` changes only `docs/PROJECT_STATUS.md`, `docs/contracts/P14-C-DESIGN-CONTRACT.md`, and `docs/contracts/P14-C-ACCEPTANCE-MATRIX.md`.
- P13-U/P13-T boundaries remain explicitly protected.

### Remaining blocking findings

1. **EXPECTED_ABSENCE remains internally contradictory.** Section 8.2 correctly removes `expected_absence` from EXPECTED_CONTRACT, but §9.3 still says EXPECTED_CONTRACT may declare `expected_absence = True`, and §9.4/INV-COMP-005 still refer to such declarations. The repaired contract therefore still has two incompatible schemas for the same authoritative object. Freeze one model only; the preferred model is to keep EXPECTED_CONTRACT as expected_entities/expected_dates and represent intentional absence through a separate explicit expected-absence pair/set, with exact denominator semantics.

2. **Contract ID ↔ Acceptance Matrix traceability is still not bidirectionally closed.** The Matrix uses IDs such as `P14C-REV-001`, while the Design Contract defines revision invariants as `REV-001` through `REV-005`, not the same Contract IDs. More broadly, the Design Contract contains explicit invariants such as `INV-EVID-004/005`, `INV-COMP-005`, `INV-TS-001..004`, `INV-REV-004/005`, `INV-DUP-001..004`, and `INV-PROV-A/B-001` without corresponding Matrix rows. Conversely, every Matrix row must map to an explicitly named invariant in the Design Contract. The stated bidirectional traceability invariant is therefore not yet satisfied.

### Required Contract Repair R2
- Resolve EXPECTED_ABSENCE into one authoritative, internally consistent representation; remove every stale reference to `expected_absence` as a field of EXPECTED_CONTRACT unless that field is deliberately reinstated with a precise mixed-required/mixed-absent pair schema.
- Assign one canonical Contract ID to every Design Contract invariant and use exactly the same ID in the Acceptance Matrix. No aliases such as `REV-001` vs `P14C-REV-001`.
- Add a Matrix row for every explicit Design Contract invariant, including the currently unmapped Evidence, Timestamp, Completeness, Revision, Duplicate/Conflict and Provenance invariants; ensure every Matrix row points to a defined invariant.
- Keep this repair documentation-only. Do not create Golden Tests, modify `src/`, `tests/`, data, P13-T/U, factors, policy, calibration, or recommendation logic.
- After repair, stop and await independent acceptance again.

P14-D remains blocked.

## P14-C Contract Repair R3 Independent Acceptance — 2026-09-30

**Decision: FAIL / REPAIR REQUIRED. Contract is NOT frozen. Do not start Golden Tests or advance to P14-D.**

Independently reviewed R3 implementation HEAD `1a6178a3e090b7509eeacfcb99161d2498ff815d` against the accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings

- R3 is the actual latest implementation commit and its delta from the R3 repair base is documentation-only: `docs/PROJECT_STATUS.md`, `docs/contracts/P14-C-DESIGN-CONTRACT.md`, and `docs/contracts/P14-C-ACCEPTANCE-MATRIX.md`.
- EXPECTED_CONTRACT remains limited to `expected_entities` / `expected_dates`; fixture-specific `expected_empty`, `broken_source`, `force_source_error`, and `fixture_mode` are not reintroduced.
- SOURCE_EMPTY is explicitly defined as a durable `raw_ingestion_audit.jsonl` observation and is separated from canonical raw records.
- The Design Contract and Acceptance Matrix contain the same 61 unique canonical `P14C-*` IDs; there are no contract-only or matrix-only IDs.
- P13-U/P13-T boundaries remain unchanged; no Golden Tests or production implementation changes were introduced by R3.

### Blocking findings

1. **Acceptance Matrix contains duplicate Contract IDs.** Mechanical extraction found 61 unique IDs in the Design Contract and 61 unique IDs in the Matrix, but the Matrix contains 64 ID occurrences because `P14C-SH-004`, `P14C-SH-005`, and `P14C-SH-006` each appear twice. R3 explicitly requires `duplicate_matrix_ids = 0`; therefore the bidirectional registry is not closed.
2. **R3 self-reported count is incorrect.** The commit message claims 57 unique Contract IDs, while the independent extraction finds 61 unique IDs in each document. This must be corrected so the acceptance evidence is auditable and mechanically reproducible.
3. **The Matrix/Contract wording has at least one redundant normative requirement:** `P14C-RECON-001` and `P14C-RECON-006` both prohibit automatic source-winner selection. This is not by itself the primary mechanical blocker, but the final repair should verify that each canonical ID represents one distinct invariant and that duplicate semantics are not hidden behind different IDs.
4. **No GitHub Actions run/status is independently available for R3 HEAD.** `fetch_commit_workflow_runs` and combined status both return empty for `1a6178a...`. This is secondary to the direct registry failure, but current-head CI evidence must be obtained before final acceptance if the repository workflow requires it.

### Required R4 repair

- Keep the repair documentation-only.
- Remove the duplicate Matrix rows for `P14C-SH-004/005/006`; retain exactly one row for each canonical ID.
- Re-run a mechanical audit and require exactly:
  - `contract_unique_ids = matrix_unique_ids`
  - `orphan_contract_invariants = 0`
  - `orphan_matrix_rows = 0`
  - `duplicate_contract_ids = 0`
  - `duplicate_matrix_ids = 0`
  - `undefined_matrix_ids = 0`
- Reconcile the reported ID count with the actual extracted count; do not claim 57 if the registry contains 61.
- Review whether `P14C-RECON-001` and `P14C-RECON-006` should be merged or otherwise made semantically distinct; do not delete a normative requirement merely to make counts match.
- Preserve the current EXPECTED_ABSENCE model and all P14-A/P14-B authority boundaries.
- Do not create Golden Tests, modify `src/`, `tests/`, `data/`, `scripts/`, P13-T/U, factors, policy, calibration, recommendation logic, or production alpha logic.
- Obtain inspectable CI evidence for the final repair HEAD if the workflow is available.
- Stop after the documentation-only repair and await independent acceptance.

P14-D remains blocked.

## P14-C Contract Repair R4 — 2026-09-30

Documentation-only repair per the R3 independent acceptance verdict (`54d6b6e`). All changes confined to `docs/contracts/P14-C-DESIGN-CONTRACT.md` and `docs/contracts/P14-C-ACCEPTANCE-MATRIX.md`; verified by the mechanical audit `scripts/audit_p14c_contract.py` (delivered `b358670`/`18e44f3`): **PASS, 0 hard + 0 soft findings**.

### Design Contract changes

- Numbered the Boundary section into the section sequence (`## P14C-BND:` → `## 12. Boundary Contract`); resequenced Duplicate / Conflict to §13 and fixed the off-by-one subsection numbering in Freshness (13.x→14.x), Reconciliation (14.x→15.x), and Provenance (15.x→16.x). Section numbers now run §1..§23 with no gaps.
- Canonicalized `P14C-SH-001..003` from bare bold text to the `- **P14C-SH-00N**:` list form, making their Acceptance Matrix rows traceable.
- Reworded `P14C-RECON-001..004` to reconciliation semantics (CONSISTENT/CONFLICT tolerance classification; contributing-source value and provenance preservation) per §15.1's field requirements. The "不得自动选择 winner / 不得自动平均 / 不得静默 resolution" prohibitions remain normative under `P14C-DUP-001..004`; RECON-006 restated as an output-schema prohibition (no `resolved_value`). No normative requirement deleted.
- Disambiguated the identical pair FRESH-002/SH-002 ("不得硬编码 stale 计数"): FRESH-002 now scopes to record-level P14-A policy evaluation; SH-002 scopes to aggregation of per-record freshness results into the STALE health state.

### Acceptance Matrix changes

- Removed the trailing duplicate Source Health block; `P14C-SH-004/005/006` each appear exactly once (61 rows = 61 unique IDs).
- Aligned drifted rows to their Design Contract invariants: REV-003/REV-004 (mutation/regression were swapped), COMP-002..004, DET-002/003 (swapped), EVID-003 (was testing quality_reasons instead of durable failure evidence), SH-001..003 (now trace to the deterministic/no-hardcode/no-ML invariants; the OK/DEGRADED/STALE state behaviors remain the expected results and are normative in Contract §17's state table).
- Closure header now states the mechanically verified counts.

### Mechanical audit result (repair HEAD)

- `contract_unique_ids = matrix_unique_ids = 61`
- `orphan_contract_invariants = 0`, `orphan_matrix_rows = 0`
- `duplicate_contract_ids = 0`, `duplicate_matrix_ids = 0`, `undefined_matrix_ids = 0`
- Cross-domain duplicate invariant text (W001) and near-duplicates (W003): 0.

### Notes

- The nine-dimension report structure and per-dimension `reasons` checks remain normative via Contract §18/§19 schema enforcement; they no longer occupy matrix rows (previously mis-filed under COMP-004/EVID-003).
- `tests/contracts/p14c/test_p14c_contract_harness.py`'s characterization snapshot was consciously updated to the repaired clean state, exactly as the test's own docstring prescribes ("contract edits require independent review, and the snapshot must be consciously updated alongside them"). No assertion was weakened: the test now pins the strictest state (zero findings, 61/61/61 counts). No other `tests/`, `src/`, `data/`, or `scripts/` changes.
- EXPECTED_ABSENCE model and all P14-A/P14-B authority boundaries unchanged. P13-T STOPPED, P13-U ACCUMULATING. No Golden Tests created.

Stopping here; awaiting independent acceptance.

P14-D remains blocked.


## P14-C Acceptance Harness Reset — Independent Acceptance — 2026-10-01

**Decision: FAIL / REPAIR REQUIRED. Contract is NOT frozen. Do not start Golden Tests or advance to P14-D.**

Independently inspected current HEAD `3144a6951d33281af38e8663d394115148bb00d1` against accepted P14-B baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Positive findings

- The Acceptance Harness is now present at `scripts/audit_p14c_contract.py`.
- Meta-tests are present at `tests/contracts/p14c/test_p14c_contract_harness.py`.
- The harness checks canonical ID closure, duplicate rows, aliases, section numbering, EXPECTED_CONTRACT fixture-field bans, nine dimensions, frozen boundaries, DRAFT governance status, stale traceability claims, and semantic-drift suspects.
- R4 removed the three duplicate Source Health Matrix rows found in the R3 independent review. The current R4 report states 61 unique IDs / 61 Matrix rows / zero orphan and duplicate findings.
- The current workflow definition `.github/workflows/tests.yml` includes a Full pytest suite and P13-M regression, so the new harness meta-test would be exercised by Full pytest.
- No new P13-T execution or production alpha/policy/calibration/recommendation promotion was introduced by the R4 documentation repair itself.

### Blocking findings

1. **No independently verifiable GitHub Actions run exists for current HEAD.** Both the commit workflow-run lookup and combined commit status for `3144a695` return no run/status. The repository acceptance rule explicitly requires GitHub Actions evidence, including workflow → job → step inspection. Therefore the claimed harness PASS cannot yet be independently accepted.

2. **The current `PROJECT_STATUS.md` was stale at HEAD.** Its Current Phase and Current Commit still pointed to the earlier Contract Reset submission `a3f22a8`, not the actual R4/harness HEAD. This is now recorded as a documentation-consistency defect and must be corrected before final acceptance.

3. **The characterization snapshot is intentionally pinned to the clean current documents.** This is acceptable as a regression mechanism only if the clean state has first been independently verified. Because current-head CI is unavailable, the snapshot cannot by itself substitute for the required independent execution evidence.

4. **Local direct execution could not be independently reproduced in this environment** because external GitHub network access is unavailable. Therefore the reported `PASS, 0 hard + 0 soft` result is treated as ZCODE evidence, not as an independently executed result.

### Required repair

- Obtain a real GitHub Actions run for exact HEAD `3144a6951d33281af38e8663d394115148bb00d1` and expose the workflow/job/step evidence.
- Ensure the run executes `tests/contracts/p14c/test_p14c_contract_harness.py` and the Full pytest suite; retain P13-M regression evidence.
- Correct `docs/PROJECT_STATUS.md` so Current Phase / Current Commit reflect the actual submission and the independent acceptance state.
- Do not weaken or rewrite the clean-state characterization snapshot merely to obtain PASS.
- Keep P13-T STOPPED / NOT EXECUTED, preserve P13-U virgin protection, and do not add P14-D or production factor/policy/calibration/recommendation logic.
- Stop after the CI/documentation repair and await independent acceptance.

P14-D remains blocked.

## P14-C Acceptance Harness CI Gate Repair — 2026-10-01

Response to the Acceptance Harness Reset verdict (`e881b09`). Documentation-only; no code, tests, contract, workflow, or data changes.

### Blocking finding 1 — CI run for `3144a695` (addressed: run exists and is now recorded)

A real GitHub Actions run for exact HEAD `3144a6951d33281af38e8663d394115148bb00d1` **exists** and is recorded in the Current Commit section above:

- workflow `tests`, run `36739506965` (event: push, completed / **success**, started 2026-09-30T15:48:16Z)
- pytest job `109969874122`: every step success, including "Environment diagnostics" (`pytest --collect-only -q -ra`), "Full pytest suite" (`python -m pytest -q -ra`), "P13-M pooled industry regression"
- p13m job `109969874447`: "P13-M pooled industry regression" success
- Note for re-verification: the Actions run appears under **check-runs** (`/commits/{sha}/check-runs`) and workflow-run lookup (`/actions/runs?head_sha={sha}`), not under the legacy combined-status endpoint; the original lookup may also have hit the 2026-09-30 GitHub connectivity outage window.

### Blocking finding 2 — stale PROJECT_STATUS (addressed in this commit)

Current Phase and Current Commit now reflect the actual submission (`3144a695`) and the latest independent verdict (`e881b09`).

### Blocking finding 3 — snapshot vs independent execution (unchanged by design)

The clean-state characterization snapshot is not weakened or rewritten. The CI "Full pytest suite" step on `3144a695` exited success; on the identical tree the suite is 361 passed / 0 failed, including the 14 harness meta-tests, one of which executes `run_harness` against the real documents and asserts `contract_unique_ids = matrix_unique_ids = 61`, `matrix_rows = 61`, zero orphans/duplicates, zero hard/soft findings.

### Blocking finding 4 — local numbers as ZCODE evidence (CI conclusions now primary)

The run/job/step conclusions above are the machine-verifiable result; local direct runs (`python scripts/audit_p14c_contract.py` → exit 0, PASS, 0 hard + 0 soft) are corroborating ZCODE evidence only.

P13 boundaries unchanged: `research_end = 2026-09-22`, `virgin_start = 2026-09-23`, P13-T STOPPED / NOT EXECUTED, P13-U protection intact. No Golden Tests, no P14-D, no production factor/policy/calibration/recommendation changes.

Stopping here; awaiting independent acceptance.

P14-D remains blocked.


## P14-C Acceptance Harness Reset — Independent Acceptance — 2026-10-01

**Decision: PASS. P14-C Acceptance Harness Reset is independently accepted.**

Independent verification was performed against the functional submission `3144a6951d33281af38e8663d394115148bb00d1` and the final documentation-sync HEAD `1961773d6af4e742d2c05a662a34d1d91b9ccf29`.

### Acceptance evidence

- GitHub Actions workflow: `tests`
- Exact functional submission SHA: `3144a6951d33281af38e8663d394115148bb00d1`
- Run: `36739506965`
- Workflow result: **success**
- `pytest` job `109969874122`: **success**
- `p13m` job `109969874447`: **success**
- `pytest` job steps independently inspected; Environment diagnostics, core tests, agent/backtest/ledger tests, P8 regression, P13-M regression, and Full pytest all succeeded.
- Full pytest log: **361 passed, 2 warnings, 0 failed**.
- Full pytest command: `python -m pytest -q -ra`.
- P13-M regression: **3 passed** in the dedicated job.
- Harness characterization is included in the Full pytest suite and pins the clean real-document state:
  - `contract_unique_ids = 61`
  - `matrix_unique_ids = 61`
  - `matrix_rows = 61`
  - `contract_only = []`
  - `matrix_only = []`
  - `duplicate_contract_ids = 0`
  - `duplicate_matrix_ids = 0`
  - `hard_findings = 0`
  - `soft_findings = 0`
- The current HEAD delta after the verified functional submission contains only `docs/PROJECT_STATUS.md`; no Contract, Harness, test, source, data, or workflow changes were introduced by the synchronization commit.
- EXPECTED_CONTRACT remains restricted to `expected_entities` / `expected_dates`; the forbidden fixture-control fields remain absent.
- P13-T remains **STOPPED / NOT EXECUTED**; P13-U virgin protection remains intact.
- No Golden Tests were created in this stage.
- No production factor/policy/calibration/recommendation changes were introduced.

### Acceptance boundary

The Acceptance Harness is now the mechanical gate for the next P14-C stage. The Contract is treated as frozen for the purpose of proceeding to Golden Tests/Fixtures. P14-C production implementation is still **not accepted** merely by this harness acceptance.

**Next allowed stage: P14-C Golden Tests / Fixtures Design & Freeze.**

P14-D remains blocked until P14-C Golden Tests, implementation, CI, and independent acceptance are complete.

## P14-C Golden Tests / Fixtures Design & Freeze — 2026-10-01

**P14-C Golden Tests / Fixtures Design & Freeze
implementation complete — awaiting independent acceptance**

Deliverables (scope per mandate: only `tests/contracts/p14c/**`, the golden coverage doc, and this status file):

- `tests/contracts/p14c/fixtures/` — **64 frozen golden fixtures** (`P14C-GOLD-001..064`), one scenario per file, every expected value a hand-written literal (standard answer, never an implementation snapshot).
- `tests/contracts/p14c/golden/core.py` — validation engine: schema checks, contract-arithmetic self-consistency (§9 completeness, §10.1 timestamp checks, §15 tolerance, §17 health priority), frozen-authority cross-checks (P14-A `is_admissible`/`visible_revisions`/`freshness_status`/`FRESHNESS_POLICIES`, P14-B `RawStore` durable replay, P13-U boundary guard), anti-cheat scans (mandate §31 A–E), Matrix coverage closure, deterministic canonical report.
- `tests/contracts/p14c/test_p14c_golden.py` — 76 pytest cases (64 per-fixture + 12 global gates).
- `docs/contracts/P14-C-GOLDEN-TESTS.md` — frozen coverage matrix (64 rows) + interpretation notes.

Coverage: **all 61 canonical Contract IDs** in the frozen Acceptance Matrix are covered (closure mechanically asserted); PIT-GOOD/PIT-BAD additionally exercise P14-A PIT authority; G-TS-005 extends TS-001.

Anti-cheat: no fixture-control fields (`expected_empty`/`expected_absence`/`broken_source`/`force_source_error`/`fixture_mode` — scanned); golden layer never imports the P14-C production implementation (import-scan); expected sets proven a-priori by fixtures where actual ≠ expected; contract/matrix bytes hash-pinned so silent contract edits fail the golden layer.

RECON-001 vs RECON-006 (mandate §26): distinct semantics demonstrated (tolerance classification vs output-schema prohibition). **CONTRACT_BLOCKER: NO.** Intentional absence is declared positively as `intentional_absence_pairs` (a-priori pair declaration; the contract's §8.2 structure has no absence field — documented in the golden doc, contract itself untouched).

Determinism: full suite run #1 = run #2 = **437 passed, 2 warnings, 0 failed**; canonical golden report byte-identical across rebuilds (sha256 `1c7a0b4b36564fa92c258f4e1ba65499e2806f826decf676997e6f47d3ebe13f`); engine total 338 checks, 0 failures.

Boundaries: `research_end = 2026-09-22`, `virgin_start = 2026-09-23` unchanged; P13-T STOPPED / NOT EXECUTED; P13-U protection intact; all fixture dates are synthetic, deterministic, pre-virgin (the single sanctioned virgin date, BND-003's `violating_decision_date=2026-09-24`, exists only to prove the guard rejects it). No production alpha/policy/calibration/recommendation changes. FACTOR_REGISTRY hash-pinned (`689d7463…8601b`, 8 factors).

No P14-C production implementation was started. Awaiting independent acceptance.

P14-D remains blocked.


## P14-C Golden Tests / Fixtures Design & Freeze — Independent Acceptance — 2026-10-01

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-C Production Implementation.**

Independently inspected against exact HEAD `06f3294c8c76dae031510f9c308722678ac08092`, with P14-C Acceptance Harness Reset accepted baseline `a8104e755cbaf6fa6909b26cae343b66877c0ab3` / functional harness tree `3144a6951d33281af38e8663d394115148bb00d1`.

### Positive acceptance evidence

- GitHub Actions exact-HEAD run: `36748661777`, workflow `tests`, push event, completed / **success**.
- `pytest` job `110001285110`: all workflow steps succeeded; Full pytest reported **437 passed, 2 warnings, 0 failed**.
- `p13m` job `110001285269`: dedicated P13-M regression succeeded (**3 passed**).
- HEAD diff from `3144a695` contains only Golden fixtures/tests/docs plus `PROJECT_STATUS.md`; no `src/**`, `data/**`, Acceptance Harness, Contract, workflow, P13-U/T or production factor/policy/calibration/recommendation changes.
- 64 Golden fixtures cover all 61 canonical Contract IDs; fixture IDs are dense and unique.
- RECON-001 and RECON-006 are demonstrably distinct in the submitted Golden layer.
- Contract/Matrix bytes are hash-pinned; banned fixture-control tokens are mechanically scanned; expected sets are tested with actual data different from expected sets.
- P13-T remains STOPPED / NOT EXECUTED and the protected research boundary is not used for research/holdout evaluation.

### Blocking findings

1. **CONTRACT_BLOCKER — EXPECTED_ABSENCE has no legal frozen contract representation.**

   The frozen Design Contract §8.2 defines `EXPECTED_CONTRACT[source_id]` with only `expected_entities` and `expected_dates`. Yet MISS-004 and COMP-005 require domain-declared EXPECTED_ABSENCE and require those pairs to be excluded from the completeness denominator. The Golden implementation invents a new field `intentional_absence_pairs` inside the fixture's expected-contract entry to make this executable. That field is not part of the frozen Contract schema. Therefore the Golden layer has silently extended the Contract instead of freezing a standard answer derived from it. This is a genuine contract/schema gap, not a test-only issue.

   Required resolution: **do not modify the Golden tests to bless this invented field and do not start production implementation.** Return to Contract Repair and explicitly define the legal representation/authority for EXPECTED_ABSENCE, then re-run the Acceptance Harness before re-freezing Golden fixtures. Preserve the existing MISS-002 distinction between SOURCE_EMPTY and EXPECTED_ABSENCE.

2. **Virgin-zone fixture violation — G-061 uses an actual protected virgin date.**

   `tests/contracts/p14c/fixtures/G-061_bnd.json` uses `violating_decision_date = 2026-09-24`, which is inside the protected P13-U virgin zone beginning `2026-09-23`. Although the test uses the date only to prove that the guard rejects it, the Golden task explicitly required synthetic, deterministic, non-holdout fixtures and preservation of the virgin boundary. The guard can be tested with an arbitrary synthetic date after the boundary (for example a far-future synthetic date) without referring to an observed virgin date. The fixture must therefore be changed to a synthetic post-boundary date that is not an actual holdout observation/date.

### Determination

The 437-test green CI result is valid evidence of internal consistency, but it cannot override the frozen-contract and virgin-zone violations above. **P14-C Golden Tests / Fixtures Design & Freeze is not accepted.** Do not proceed to P14-C Production Implementation.

Repair sequence:
1. Contract Repair: explicitly freeze EXPECTED_ABSENCE representation and authority; do not edit Golden fixtures merely to make them pass.
2. Re-run the Acceptance Harness and obtain independent PASS.
3. Re-freeze the Golden fixtures against the repaired contract.
4. Replace G-061's actual virgin date with a synthetic post-boundary date.
5. Re-run exact-HEAD CI, Golden tests, full pytest, P13-M regression and deterministic double-run.

P14-D remains blocked.

## P14-C Contract Repair — EXPECTED_ABSENCE Freeze — 2026-10-01

Response to the Golden Tests Freeze verdict (`6489fad`). Contract-only repair; no production code, no Golden/Harness test edits, no data changes.

### Root cause addressed (verdict blocking finding 1)

The frozen Contract defined the EXPECTED_ABSENCE semantics (MISS-004, COMP-005) but no legal field to declare it, forcing the Golden layer to invent `intentional_absence_pairs`. This repair freezes the missing semantics in `docs/contracts/P14-C-DESIGN-CONTRACT.md` (v4):

- **Representation (§8.2 + new §8.3)**: `expected_absence_pairs` inside each `EXPECTED_CONTRACT[source]` entry (optional, default `[]`) is the **sole authoritative declaration channel** for EXPECTED_ABSENCE. Boolean switches (`expected_absence=True`), `expected_empty`, `broken_source`, `force_source_error`, `fixture_mode`, and any actual-derived representation are explicitly declared invalid.
- **Five-class mutual-exclusion chain (§7.2)**: `EXPECTED_ABSENCE ≠ SOURCE_EMPTY ≠ SOURCE_ERROR ≠ PARSE_FAILURE`, `EXPECTED_ABSENCE ≠ UNEXPECTED_MISSING`, each with a one-line definition.
- **MISS-004 strengthened (same ID)**: EXPECTED_ABSENCE cannot be derived from actual-missing data, SOURCE_EMPTY, SOURCE_ERROR, or PARSE_FAILURE — only declared via §8.3. No new invariant IDs were introduced (existing MISS-004 / EXP-001 / EXP-002 / COMP-001 / COMP-005 / EVID-004 naturally carry the semantics, per the repair mandate's preference against ID inflation).
- **Completeness arithmetic (§9.1/§9.2)**: `X = declared absence pairs (X ⊆ P, out-of-scope declaration fails fast)`, `R = P − X`, `expected_count = |R|`, `actual_count = |A_pair ∩ R|`, coverage unchanged otherwise; X never increases actual_count, never counts as missing, is never silently dropped, and is reported separately as EXPECTED_ABSENCE evidence.
- **Provenance (new §16.4, Type C Contract Declaration Provenance)**: absence declarations are contract facts, not ingestion observations. Required: `source_id`, `expected_contract_id`, `entity_date_pair_scope`, `declaration_reference`. Forbidden (forgery = violation): `observation_type`, `observed_at`, `adapter_version`, `ingestion_id`, `available_time`, `ingested_at`, `raw_payload_hash`.

### Verification results

- Acceptance Harness (`python scripts/audit_p14c_contract.py`): **PASS, 0 hard + 0 soft**; closure preserved — `contract_unique_ids = matrix_unique_ids = 61`, `matrix_rows = 61`, orphans/duplicates 0 (Matrix file unchanged: sha256 `fc99637a…636`).
- `tests/contracts/p14c/` pytest: 88 passed, 2 failed — both failures are the Golden layer's **contract-bytes hash pin** (`test_anticheat_contract_pinned` + aggregator `test_all_checks_green`) refusing the edited contract. This is the Check-D anti-cheat gate working as designed: the golden layer may not silently track a moving contract. Golden files were NOT touched this round.
- Full pytest: 435 passed, 2 failed (same two pin tests), 0 other failures. P13-M regression: 3 passed.
- New pinned hashes for the Golden re-freeze: `P14-C-DESIGN-CONTRACT.md` sha256 `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b`.

### GOLDEN_REFREEZE_REQUIRED (next gated stage, after this repair is independently accepted)

1. Re-pin `PINNED_CONTRACT_SHA` in `tests/contracts/p14c/golden/core.py` to `c217f6b9…167b` (Matrix pin unchanged).
2. Rename the declared-absence field in fixtures G-007, G-009, G-020 from `intentional_absence_pairs` to the canonical `expected_absence_pairs`; update `golden/core.py` completeness arithmetic to read `X` from the canonical field (formulas already match §9.1/§9.2).
3. Update `BANNED_FIXTURE_TOKENS` to ban the boolean/control styles (`expected_absence=True`, bare `expected_absence` key, `expected_empty`, `broken_source`, `force_source_error`, `fixture_mode`) while permitting the canonical `expected_absence_pairs` declaration field; keep the import-scan as is.
4. Regenerate `docs/contracts/P14-C-GOLDEN-TESTS.md` interpretation notes (absence representation is now canonical, not an interpretation).
5. Deterministic double-run + exact-HEAD CI.

### GOLDEN_FIX_REQUIRED (verdict blocking finding 2)

Replace G-061's `violating_decision_date = 2026-09-24` (an actual protected virgin date) with a synthetic post-boundary date (e.g. `2027-01-01T09:00:00+08:00`); the guard-raises assertion is unchanged. During the same re-freeze.

### Boundaries

`research_end = 2026-09-22`, `virgin_start = 2026-09-23` unchanged; P13-T STOPPED / NOT EXECUTED; P13-U intact. No factor/calibration/policy/recommendation changes; no P14-C production implementation started.

Stopping here; awaiting independent acceptance.

P14-D remains blocked.


## P14-C Contract Repair — Independent Acceptance — 2026-10-01

**Decision: FAIL / CI GATE REPAIR REQUIRED. Do not advance to Golden Re-freeze yet.**

Independently inspected exact Contract Repair HEAD `38bbf82340fd22fd196ea97639ce014e2bf15033` against the Golden Freeze failure `6489fad` and P14-B accepted baseline `84021d6c9039582cfa831e1e3a85f1141fb87efd`.

### Contract semantic findings

**PASS at the Contract layer:**

- `expected_absence_pairs` is now explicitly defined in `EXPECTED_CONTRACT[source]` as the sole authoritative declaration channel.
- Boolean/test-control alternatives remain prohibited.
- EXPECTED_ABSENCE is explicitly separated from SOURCE_EMPTY, SOURCE_ERROR, PARSE_FAILURE and UNEXPECTED_MISSING.
- MISS-004 now prohibits deriving EXPECTED_ABSENCE from actual missingness or source anomalies.
- Completeness arithmetic is frozen as `X = declared absence pairs`, `R = P - X`, with denominator based on required pairs.
- EXPECTED_ABSENCE pairs are separately reported and excluded from the completeness denominator.
- Type-C Contract Declaration Provenance is explicitly distinguished from record/observation provenance.
- No new Contract IDs were introduced; Contract/Matrix closure remains structurally 61/61, with the Matrix unchanged.
- Diff from the Golden Freeze HEAD contains only `docs/PROJECT_STATUS.md` and `docs/contracts/P14-C-DESIGN-CONTRACT.md`; no `src/**`, `data/**`, Golden, Harness, P13-U/T or production factor/policy/calibration/recommendation changes.

### Blocking finding

**CI_GATE_BLOCKER — no independently verifiable GitHub Actions run exists for exact HEAD `38bbf82340fd22fd196ea97639ce014e2bf15033`.**

- `fetch_commit_workflow_runs` for exact HEAD returned no workflow runs.
- Combined commit status for exact HEAD returned no statuses.
- The repository workflow is configured to run on every push to `main`, so the absence of an exact-HEAD run cannot be treated as equivalent to PASS.
- The reported local result (`435 passed, 2 failed`) is not sufficient for final acceptance. The two failures are the expected Golden contract-hash pin failures caused by this intentional Contract change, but exact-HEAD CI evidence is still required by the project workflow.

### Important non-blocking observation

The Golden layer is intentionally expected to fail its pinned-contract checks until the next gated Golden Re-freeze. This is correct anti-drift behavior and is **not** a reason to modify Golden/Harness during Contract Repair.

### Determination

**P14-C Contract Repair is NOT independently accepted yet.**

The Contract semantic repair itself is accepted as correctly scoped and internally coherent, but the phase fails the mandatory exact-HEAD CI gate.

Required next step:

1. Obtain a verifiable GitHub Actions run for exact Contract Repair HEAD.
2. Inspect run → job → step, including Harness and regression/full-test evidence.
3. If CI is green, independently accept this Contract Repair.
4. Then proceed to the already-defined **Golden Re-freeze** task:
   - re-pin the Contract hash;
   - rename `intentional_absence_pairs` → `expected_absence_pairs`;
   - update Golden completeness reads and anti-cheat token rules;
   - replace G-061's actual virgin date with a synthetic post-boundary date;
   - rerun exact-HEAD CI, Golden, full pytest, P13-M and deterministic double-run.

P14-C Production Implementation remains blocked. P14-D remains blocked.

## P14-C Contract Repair — CI Gate Repair — 2026-10-01

Response to the Contract Repair verdict (`9c8c106`): contract semantics PASS, scope PASS, closure PASS; sole blocker = exact-HEAD CI evidence (CI_GATE_BLOCKER). This round is CI/status-synchronization only.

### Exact-HEAD CI evidence for `38bbf82340fd22fd196ea97639ce014e2bf15033`

A real GitHub Actions run for the exact Contract Repair HEAD **exists**:

- workflow `tests`, run `36752429513` (event: push, completed)
  - https://github.com/CGchenggang/a-stock-quantimental/actions/runs/36752429513
- pytest job `110014139560`: completed / failure — the ONLY failing step is
  "Full pytest suite"; locally reproduced on the identical tree as
  `435 passed, 2 failed`, the 2 failures being exactly the Golden
  contract-hash pin pair (`test_anticheat_contract_pinned` +
  `test_all_checks_green`), i.e. the documented expected anti-drift
  behavior until the sanctioned Golden Re-freeze (per the verdict's own
  non-blocking observation). No unexpected failures.
- p13m job `110014139754`: completed / **success** ("P13-M pooled industry regression")
- Re-verification endpoints that return this run:
  - `GET /repos/CGchenggang/a-stock-quantimental/actions/runs?head_sha=38bbf82340fd22fd196ea97639ce014e2bf15033`
  - `GET /repos/CGchenggang/a-stock-quantimental/commits/38bbf82340fd22fd196ea97639ce014e2bf15033/check-runs`
  - Note: the legacy combined-status endpoint does not include Actions
    check runs; a transient GitHub connectivity outage window also
    coincided with the original query (pushes from this workspace failed
    during the same window).

### CI-only repair commit (this round)

- `7d00b1c` (parent `9c8c106`, tree-descendant of `38bbf823`): adds one
  explicit workflow step "Contract Harness audit (P14-C)" running
  `python scripts/audit_p14c_contract.py` (exit-code gated, JSON in job
  log), so every run exposes an individually inspectable harness result
  instead of an implicit one inside the full suite. No test was removed,
  deselected, weakened, or replaced by print-only.
- Its run: workflow `tests`, run `36782824995`
  (https://github.com/CGchenggang/a-stock-quantimental/actions/runs/36782824995)
  - pytest job `110117027438`: "Contract Harness audit (P14-C)" →
    **success** (harness PASS 0 hard / 0 soft, 61/61/61 closure);
    "P13-M pooled industry regression" step → success;
    "Full pytest suite" → failure (same two expected Golden pin tests, nothing else)
  - p13m job `110117027669`: success

### Local verification on this HEAD (corroborating only)

- `python scripts/audit_p14c_contract.py` → exit 0, PASS, 0 hard + 0 soft, 61/61/61
- `python -m pytest -q -ra tests/contracts/p14c/` → 88 passed, 2 failed (the pin pair only)
- `python -m pytest -q -ra` → 435 passed, 2 failed (same pair), 2 warnings
- `python -m pytest -q -ra tests/test_industry_relative.py` → 3 passed
- `python -m pytest -q -ra tests/test_industry.py tests/test_import_cninfo_industry_membership.py` → 11 passed

### Gates

Diff `38bbf823..HEAD`: only `.github/workflows/tests.yml` + `docs/PROJECT_STATUS.md`. Contract (`c217f6b9…167b`), Matrix (`fc99637a…636`), Golden, Harness script/tests, src, data all unchanged. P13-T STOPPED / NOT EXECUTED; P13-U intact; `research_end = 2026-09-22`, `virgin_start = 2026-09-23` unchanged. Golden Re-freeze NOT started (next gated stage after independent acceptance).

Stopping here; awaiting independent acceptance.

P14-D remains blocked.


## P14-C Contract Repair — Independent Acceptance — 2026-10-01

**Decision: PASS. Contract Repair is independently accepted. Do not treat this as P14-C production acceptance; proceed only to the gated Golden Re-freeze stage.**

Independent acceptance target:
- Contract Repair implementation HEAD: `38bbf82340fd22fd196ea97639ce014e2bf15033`
- P14-B accepted baseline: `84021d6c9039582cfa831e1e3a85f1141fb87efd`
- Current repository HEAD after CI-only/documentation evidence commits: `06f3294c8c76dae031510f9c308722678ac08092`

### Acceptance evidence

1. **Exact-head CI evidence exists and is genuine.**
   - GitHub Actions run: `36752429513`
   - pytest job: `110014139560`
   - p13m job: `110014139754`
   - The pytest job checkout log explicitly fetched and checked out `38bbf82340fd22fd196ea97639ce014e2bf15033`; `git log -1 --format=%H` returned the same SHA.
   - P13-M regression step succeeded.
   - All pre-full-suite pytest groups succeeded.
   - Full pytest reported **435 passed, 2 failed, 2 warnings**; both failures are exactly the sanctioned Golden contract-hash pin checks:
     - `test_anticheat_contract_pinned`
     - `test_all_checks_green`
     Both report the newly repaired Contract SHA-256 `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b` as the mismatch. This is the expected anti-drift behavior until the separately gated Golden Re-freeze. It is not a Contract Repair defect.

2. **CI gate repair added an explicit inspectable Contract Harness step without changing the Contract or production implementation.**
   - CI-only commit: `7d00b1cf2a1cbde3ca61b5da63ffd386f8fc196a`
   - Its workflow run: `36782824995`
   - Dedicated `Contract Harness audit (P14-C)` step: SUCCESS.
   - P13-M job: SUCCESS.
   - Full pytest again fails only the same two expected Golden contract-pin checks.
   - Diff from Contract Repair HEAD to the CI-only commit contains only `.github/workflows/tests.yml` and `docs/PROJECT_STATUS.md`; no Contract, Matrix, Golden, Harness script, `src/`, data, factor, policy, calibration, recommendation, or P13-T/U changes.

3. **Final documentation evidence commit is status-only.**
   - Commit: `06f3294c8c76dae031510f9c308722678ac08092`
   - Diff from `7d00b1cf2a1cbde3ca61b5da63ffd386f8fc196a` contains only `docs/PROJECT_STATUS.md`.
   - No semantic or production changes were introduced after the CI-only repair.

4. **Contract semantics remain consistent with the independently reviewed repair.**
   - `expected_absence_pairs` is the sole authoritative EXPECTED_ABSENCE declaration inside `EXPECTED_CONTRACT[source]`.
   - EXPECTED_ABSENCE is distinct from SOURCE_EMPTY, SOURCE_ERROR, PARSE_FAILURE, and UNEXPECTED_MISSING.
   - Completeness uses required set `R = P - X`.
   - Contract Declaration Provenance is separated from observation provenance.
   - Acceptance Matrix closure remains 61/61 with no orphan/duplicate/undefined IDs according to the repaired harness evidence.
   - P13-T remains STOPPED / NOT EXECUTED; P13-U remains protected.
   - No production factor, policy, calibration, recommendation, or alpha logic was changed.

### Independent determination

**P14-C Contract Repair — PASS / ACCEPTED.**

The CI gate repair requirement is satisfied because there is machine-verifiable GitHub Actions evidence for the exact Contract Repair HEAD, and the later CI-only commit adds an independently inspectable Contract Harness step without modifying the Contract semantics.

The two Golden hash-pin failures are intentionally preserved as the anti-drift gate. They must be resolved only by the next **P14-C Golden Re-freeze** task, not by weakening or bypassing the pin.

### Next gate

**P14-C Golden Re-freeze** is now the only authorized next implementation stage.

It must:
- re-pin the repaired Contract hash;
- replace `intentional_absence_pairs` with canonical `expected_absence_pairs`;
- update Golden anti-cheat/interpretation rules consistently;
- replace G-061's actual virgin date `2026-09-24` with a synthetic post-boundary date;
- run deterministic double-run, exact-head CI, full pytest, and P13-M regression;
- remain Golden/test/fixture scope only.

P14-C Production Implementation and P14-D remain blocked until Golden Re-freeze is independently accepted.

## P14-C Golden Re-freeze — 2026-10-01

Golden Re-freeze against the independently accepted Contract Repair (`38bbf823`, accepted by `441e3fa8`). Scope: only `tests/contracts/p14c/fixtures/**` + `tests/contracts/p14c/golden/core.py` + this status file.

### Changes

1. **Absence declaration canonicalized**: fixture field `intentional_absence_pairs` → the contract-canonical `expected_absence_pairs` in G-007 (MISS-002) and G-020 (COMP-005); `golden/core.py` completeness arithmetic and MISS classification now read `X` from the canonical field (formulas already matched §9.1/§9.2: R = P − X, expected_count = |R|).
2. **G-007 contract-conformance fix**: its declared pair referenced entity `SW801040` outside `expected_entities`, violating frozen Contract §8.3 rule 3 (every declared pair must lie in E × D). `expected_entities` extended to `["SW801010", "SW801040"]` so the declaration is in-scope; SOURCE_EMPTY (SW801010, required, fetch returned []) vs EXPECTED_ABSENCE (SW801040, declared) semantics unchanged.
3. **New golden check `absence_scope.*`**: mechanically enforces §8.3 rule 3 (X ⊆ P) on every fixture's expected_contract.
4. **Anti-cheat retuned without weakening**: textual scan keeps banning `expected_empty` / `broken_source` / `force_source_error` / `fixture_mode`; the bare boolean/control key `expected_absence` (e.g. `"expected_absence": true`) is banned as an exact JSON key via a new structural scan — while the canonical `expected_absence_pairs` list is the sanctioned declaration channel. Import-scan against the P14-C production implementation unchanged.
5. **Contract hash re-pinned** (computed from the actual files, not guessed): `P14-C-DESIGN-CONTRACT.md` → `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b`; Matrix pin unchanged `fc99637a…636` (file untouched).
6. **G-061 boundary fixture repaired**: `violating_decision_date` real virgin date `2026-09-24` → purely synthetic far-future `2099-01-01T09:00:00+08:00` (+ explicit `synthetic_marker` note). The fixture still proves `assert_research_zone` raises on post-boundary decision dates; no real virgin-zone data is consumed anywhere. Structural scan confirms no fixture input contains any date ≥ `2026-09-23` other than this exempted synthetic guard date.

### Validation (all commands actually executed)

- `python scripts/audit_p14c_contract.py` → exit 0, PASS, 0 hard + 0 soft, closure 61/61/61, 0 duplicates/orphans/undefined
- `python -m pytest -q -ra tests/contracts/p14c/test_p14c_golden.py` → **76 passed** (both formerly-failing pin tests now green), run #2 → 76 passed
- `python -m pytest -q -ra tests/contracts/p14c/` → 90 passed (harness meta-tests unbroken)
- `python -m pytest -q -ra` → **437 passed, 0 failed**, 2 warnings
- `python -m pytest -q -ra tests/test_industry_relative.py` → 3 passed
- Deterministic canonical report double-run: byte-identical, sha256 `09cca5b0985265deddb42672b770efd88f82152a46b473acec7d1bb8970438f4` (64 fixtures, 0 failed validations)

### Boundaries

`research_end = 2026-09-22`, `virgin_start = 2026-09-23` unchanged; P13-T STOPPED / NOT EXECUTED; P13-U protected; no real virgin data consumed. No src/, data/, Contract, Matrix, Harness, factor/policy/calibration/recommendation changes. P14-C Production Implementation NOT started.

Note for the next documentation pass (outside this round's allowed scope): `docs/contracts/P14-C-GOLDEN-TESTS.md` interpretation notes still mention the pre-refreeze field name; no test consumes that prose.

Stopping here; awaiting independent acceptance.

P14-D remains blocked.
