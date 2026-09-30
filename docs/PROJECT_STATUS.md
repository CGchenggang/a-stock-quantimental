# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P14-C Contract Reset — FAIL / REPAIR REQUIRED; Contract not frozen**

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

**Important:** P13-U PASS does not mean P13-T PASS. P13-T remains pending until the frozen virgin zone reaches an executable holdout condition without contamination.

## Current Commit

`a3f22a894e7de3c7b8c520bd65de28cba5034b05`

Latest independently accepted implementation remains `84021d6c9039582cfa831e1e3a85f1141fb87efd`; `a3f22a8` is the current Contract Reset submission and is **not accepted**.

Current HEAD was independently checked on 2026-09-30.

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
