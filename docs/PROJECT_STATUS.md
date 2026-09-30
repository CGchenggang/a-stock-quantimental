# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P14-C — Data Quality / Reconciliation / Source Health — implementation complete; awaiting independent acceptance**

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

`84021d6c9039582cfa831e1e3a85f1141fb87efd`

Latest accepted commit message: `fix: persist every ingestion attempt in a durable audit log (P14-B-R1)`.

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
