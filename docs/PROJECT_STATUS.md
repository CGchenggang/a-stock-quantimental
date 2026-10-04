# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P14-D → P14-E Selection State Integration Contract — PASS / INDEPENDENTLY ACCEPTED (51a769f0a50632c5b8d71f4247d5a60ee2847012)**; **Human Authorization GRANTED for the separately scoped integration implementation**; **P14-E Production Implementation — PASS / INDEPENDENTLY ACCEPTED** (implementation `69cfe2a86d23352e9f74cf7454aad6cf59135e7b`; acceptance decision by the project owner on 2026-10-04, recorded on owner instruction — see the acceptance record below); **R3-A (Local Historical Store → P14-B real source adapter) STARTED under owner authorization — reuse of the accepted P14-B/C/D/E authority chain, no semantic change**; P14-F NOT AUTHORIZED.

P13-T remains STOPPED / NOT EXECUTED. P13-U remains PROTECTED.

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
| P14-C Contract Repair | PASS | EXPECTED_ABSENCE representation frozen; exact-head CI evidence independently verified |
| P14-C Golden Re-freeze | PASS | Independently accepted; 64 deterministic Golden fixtures; 61/61/61 closure; Production Implementation remains separately gated |
| P14-C Production Implementation | PASS | Independently accepted at `06250722e5660975733695c1ffd956cde9a8c118`; completeness required-universe repair |
| P14-D | PASS | Independently accepted after P14-D-REPAIR-001; PIT-safe information query layer; P14-E remains not authorized |
| P14-E-004 | PASS | Production Implementation Contract accepted (Design Gate, `144b38f`); reverse-trace FOUR-CLASS frozen; Production Implementation remains separately gated |
| P14-E-005 | PASS | Independently accepted Contract Draft at `70634cbe`; P14-D authority-aligned `create_bundle(query_result, authoritative_evidence_records)`; production implementation remains NOT AUTHORIZED |
| P14-E-006 Golden/Harness | PASS | Independently accepted Golden/Harness design and implementation gate at `17afd2d`; production implementation remains NOT AUTHORIZED |
| P14-D → P14-E Selection State Integration Contract v2 | PASS | Independently accepted at `51a769f`; separate Human Authorization required before implementation; P14-E production implementation remains NOT AUTHORIZED |
| P14-E Production Impl | PASS / INDEPENDENTLY ACCEPTED | REPAIR-003 BLOCKED (independently confirmed) resolved via the authorized Integration Contract v2 (`51a769f`): Human Authorization granted → REPAIR-002 verified delta restored verbatim (`69cfe2a`) — P14-D emits the resolved selection state and P14-E is a pure verbatim consumer (all label re-derivation machinery deleted); Test E adversarial regression retained; mandatory P14-B reload authority unchanged. Implementation acceptance recorded 2026-10-04 per project-owner decision (see the acceptance record below) | Golden/Harness independently accepted at `17afd2d` |

**Important:** P13-U PASS does not mean P13-T PASS. P13-T remains pending until the frozen virgin zone reaches an executable holdout condition without contamination.

## Current Commit

`51a769f0a50632c5b8d71f4247d5a60ee2847012` — independently accepted P14-D → P14-E Selection State Integration Contract v2 (docs-only). Exact-head CI run `37185144953` is green and matches this SHA. **Human Authorization for the separately scoped integration implementation was granted on 2026-10-04 by the project owner; implementation remains subject to the exact scope in Contract v2 and subsequent Independent Acceptance.

`69cfe2a86d23352e9f74cf7454aad6cf59135e7b` — P14-D → P14-E Integration Contract v2 implementation (Human Authorization of contract `51a769f0a50632c5b8d71f4247d5a60ee2847012`; REPAIR-002 verified delta restored verbatim + REPAIR-003 Test E regression retained). Status-sync convention: this file's Current Commit records the newest content commit at authoring time; docs-only bookkeeping commits on top of it are finalized by the acceptance record, which is the authoritative setter of the actual final HEAD (sha fixed-point is physically impossible inside a commit's own tree).**

P14-E-005 Contract Draft remains independently accepted at `70634cbe9e8086d325c2cff7efd377461d3d746a`.

Exact-head CI evidence for `17afd2d71675df86d443fc6093f822cf437970cb`:
- Workflow Run: `37079891815` (push, completed / **success**)
- https://github.com/CGchenggang/a-stock-quantimental/actions/runs/37079891815
- Pytest Job `110837393583`: success (P14-C audit + P14-D audit + P14-E audit + P13-M + Full pytest suite all success)
- P13-M Job `110837394102`: success
- head_sha == `17afd2d71675df86d443fc6093f822cf437970cb` (exact-head match **YES**)
- Retrieval: `GET /actions/runs?head_sha=17afd2d71675df86d443fc6093f822cf437970cb`

Latest independently accepted implementation gate: P14-E-004 Production Implementation Contract at `a72502f98a1da6aaa39ce8e048b180a0e074b466` (acceptance record commit `144b38f6f5ab11e4000ecabf2512aa0a1e422bb2`). Latest independently accepted production implementation remains P14-C at `06250722e5660975733695c1ffd956cde9a8c118` (P14-D/P14-E-004 are design/query-infrastructure gates; no production alpha runtime exists).

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

### P14-C — PASS (independently accepted)

Data quality/reconciliation and source health:
- completeness;
- missingness;
- timestamp anomalies;
- revision anomalies;
- duplicate/conflict monitoring;
- freshness monitoring;
- source health;
- deterministic quality reports.

### P14-D — PASS (independently accepted)

PIT-safe research information query layer:
- as-of information retrieval (`available_time <= as_of`, inclusive);
- exclusion accounting (NOT_YET_AVAILABLE / OUTSIDE_AS_OF / UNRESOLVED_AVAILABILITY);
- deterministic per-lineage version selection (restatement-safe);
- provenance records + `result_id`;
- virgin-zone entry guard.

### P14-E — GOLDEN/HARNESS ACCEPTED / PRODUCTION IMPLEMENTATION NOT AUTHORIZED

Research information evidence / provenance layer:
- evidence identity (content-addressed via P14-B raw_payload_hash / ingestion_id);
- evidence bundle per query (result linkage, candidate trace, exclusions);
- deterministic bundle_id + durable JSONL persistence;
- reverse traceability bundle → evidence → raw record.

`docs/contracts/P14-E-DESIGN-CONTRACT.md` is STATUS: DRAFT (v1.1, REPAIR-001). Implementation, Golden, and Harness are not authorized until independent Contract acceptance.

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

## P14-D → P14-E Selection State Integration Contract — Independent Acceptance — 2026-10-04

**Decision: PASS / INDEPENDENTLY ACCEPTED. This is Contract Acceptance only; it is NOT Human Implementation Authorization.**

Independent verification performed against exact current `main` HEAD `51a769f0a50632c5b8d71f4247d5a60ee2847012`.

### Acceptance evidence

- Actual `main` HEAD: `51a769f0a50632c5b8d71f4247d5a60ee2847012`.
- Compare from REPAIR-003 BLOCKED HEAD `91836f74a1e8895c85b354e2fe27429a87aa92e9`: exactly one commit, one changed file.
- Changed file: `docs/contracts/P14-E-P14D-SELECTION-STATE-INTEGRATION-CONTRACT.md`, +60/-9.
- No production code, tests, P14-D implementation, P14-C/P14-B, P13-T/P13-U, data, alpha/factor/policy/recommendation/trading files were changed by this commit.
- Contract v2 closes the prior authorization-scope gap: the package re-export is enumerated, the P14-E restoration surface is limited to `evidence.py` and its regression tests, and the implementation gate is separated into Contract Acceptance → Human Authorization → Implementation → Independent Acceptance.
- Authority ownership is explicit: P14-A/P14-D remain the sole selection/version authority; P14-E is a consumer; P14-B remains raw-evidence authority; P14-C remains source-reconciliation authority.
- The six P14-E selection/rejection labels are frozen verbatim; PIT visibility, version-selection semantics, existing result keys and ordering are declared unchanged.
- P14-E re-selection is explicitly forbidden; the proposed implementation consumes resolved labels verbatim.
- Exact-head GitHub Actions run `37185144953`: completed / success; `head_sha == 51a769f0a50632c5b8d71f4247d5a60ee2847012`.
- Pytest job `111385410514`: all steps successful, including P14-C/D/E audits, P13-M pooled regression and full pytest.
- P13-M job `111385410613`: successful.
- ZCODE-reported full pytest: 581 passed / 2 warnings / 0 failed; CI workflow completed successfully.
- P13-T remains STOPPED / NOT EXECUTED; P13-U remains PROTECTED; P14-F remains NOT AUTHORIZED.

### Acceptance boundary

This PASS accepts only the integration contract. It does **not** authorize implementation of `resolve_selection`, `research_query.py`, `information/__init__.py`, P14-D contract/harness changes, or P14-E `evidence.py` / regression-test restoration. Those changes require separate explicit Human Authorization.


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

Last independently updated: 2026-10-03.
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

## P14-C Golden Re-freeze — Independent Acceptance — 2026-10-01

**Decision: PASS. Golden Re-freeze is independently accepted. Do not treat this as P14-C Production Implementation acceptance.**

Independent acceptance target:
- Golden Re-freeze HEAD: `349c6b274b6b72f89bc4db35e5b1961f719011ed`
- Parent / independently accepted Contract Repair state: `441e3fa8e8ab5c7a5b2451e1f2ff5ca385a60e99`
- Accepted Contract SHA-256: `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b`
- Matrix SHA-256 remains pinned and unchanged: `fc99637a74b6fb08fea977a6edcb6245c3bce1c2636d9736380da4b5599a3636`

### Independent verification

1. **Scope is clean.** Compare `441e3fa8..349c6b2` contains only `docs/PROJECT_STATUS.md`, the allowed Golden fixtures `G-007_miss.json`, `G-020_comp.json`, `G-061_bnd.json`, and `tests/contracts/p14c/golden/core.py`. No `src/**`, `data/**`, Contract, Matrix, Harness, P13-T/U, factor/policy/calibration/recommendation or alpha changes were introduced.
2. **Contract was not modified.** Golden pin matches the independently accepted repaired Contract hash above; Matrix pin remains unchanged.
3. **EXPECTED_ABSENCE is canonicalized.** G-007/G-020 use `expected_absence_pairs`; completeness uses `R = P - X); anti-cheat rejects the forbidden control forms while allowing the canonical declaration channel. G-007's declared pair is now in `E × D` and the new absence-scope check enforces that invariant mechanically.
4. **Virgin-zone integrity is preserved.** G-061 uses synthetic `2099-01-01T09:00:00+08:00`; no real `2026-09-23+` fixture input is consumed. `research_end = 2026-09-22`, `virgin_start = 2026-09-23`; P13-T remains STOPPED / NOT EXECUTED and P13-U remains protected.
5. **Golden closure and determinism are complete.** 64 fixtures, dense unique IDs; Contract/Matrix/Golden coverage is 61/61/61; no orphan/duplicate/undefined IDs. Golden tests pass twice at 76/76; P14-C tests 90/90; full pytest 437 passed, 0 failed, 2 warnings; P13-M regression 3 passed. Canonical report is byte-identical on double-run with SHA-256 `09cca5b0985265deddb42672b770efd88f82152a46b473acec7d1bb8970438f4`.
6. **Exact-head CI is independently verified.** GitHub Actions workflow `tests`, run `36784963333`, has HEAD `349c6b274b6b72f89bc4db35e5b1961f719011ed`. Pytest job `110124063122` and P13-M job `110124063357` both succeeded. The checkout log explicitly fetched `349c6b274b6b72f89bc4db35e5b1961f719011ed` and `git log -1 --format=%H` returned the same SHA. Harness audit, all test groups, P13-M regression and full pytest steps are green; full pytest reports 437 passed, 0 failed.

### Determination

**P14-C Golden Re-freeze — PASS / ACCEPTED.**

The Golden standard is now frozen against the accepted Contract Repair. P14-C Production Implementation is the next gated stage; P14-D remains blocked until the implementation stage and its independent acceptance are complete.

### Next gate

Only **P14-C Production Implementation** may proceed next. The implementation must be graded against the frozen Golden fixtures and must not modify the Contract, Matrix, Golden standard answers, P13-T/U boundary, or production factor/policy/calibration/recommendation semantics without a separately authorized contract change.

Last independently updated: 2026-10-01.

## P14-C Production Implementation — 2026-10-01

Production implementation of the independently accepted P14-C Contract (`c217f6b9…167b`) + Harness + Golden layer (`349c6b2`, accepted `bb7c8c2`). Every change traces directly to frozen Contract/Matrix/Golden requirements.

### Production architecture

New canonical module `src/astock_v2/information/expected_contract.py` (exported via the information package):

- `ExpectedContract` — validated view of one `EXPECTED_CONTRACT[source]` entry per Contract §8.2: `expected_entities` / `expected_dates` / `expected_absence_pairs` (sole authoritative EXPECTED_ABSENCE channel, §8.3).
- Fail-fast structural rejection (anti-cheat as production code): the fixture-control fields (`expected_empty` / `broken_source` / `force_source_error` / `fixture_mode`) and the banned boolean key (`expected_absence`) raise on construction; declared pairs outside E × D raise (§8.3 rule 3). Production never interprets control fields.
- §9.2 completeness on the required set: `R = P − X`, `expected_count = |R|`, `actual_count = |A_pair ∩ R|`, coverage = actual/expected (1.0 when R empty); entity/date/pair granularities all reported (COMP-004); canonical sorted ordering, JSON-friendly lists.
- §7.1 classification: `classify_pairs` (OBSERVED / EXPECTED_ABSENCE / UNEXPECTED_MISSING) and `source_missingness_class` driven by the pair-level required set (a granularity gap consisting solely of declared-absent pairs is EXPECTED_ABSENCE evidence, never UNEXPECTED_MISSING).
- §16.4 Type C Contract Declaration Provenance: `declaration_provenance()` emits exactly `source_id / expected_contract_id / entity_date_pair_scope / declaration_reference`; observation-only fields structurally absent.

Audit runner `scripts/run_p14c_quality_audit.py` migrated onto the canonical module: `EXPECTED_CONTRACT` control fields removed; `_compute_completeness` rebuilt on `ExpectedContract` with the frozen classification priority (observation evidence SOURCE_EMPTY / SOURCE_ERROR / PARSE_FAILURE takes precedence; then UNEXPECTED_MISSING on missing required pairs; then EXPECTED_ABSENCE on unobserved declared pairs; NONE when nothing is missing — EXPECTED_ABSENCE is never a label for "all fine"). `us_index_daily` now declares `(SPX, 2026-03-03)` via `expected_absence_pairs`, exercising the full production absence path (pair classification, denominator exclusion, Type C evidence).

### Tests

- `tests/test_p14c_production.py` (22 cases): mandate Cases A–F through the production path; D/E/F proven not reinterpreted as EXPECTED_ABSENCE; structural control-field rejection; Type C provenance shape; determinism; and the frozen Golden fixtures (G-006/007/009/010/012/015..020) consumed as read-only oracles through the production implementation — golden layer untouched.
- `tests/test_p14cr4_audit_e2e.py`: three pins updated to the canonical semantics (boolean flag assertions → `expected_absence_pairs`/coverage per §9.2; complete-source class NONE; us_index_daily EXPECTED_ABSENCE), each traceable to Contract §8.3/§7.1/§9.2.

### Validation (all executed)

- Contract audit: PASS, 0 hard + 0 soft, 61/61/61; Contract/Matrix SHAs unchanged (`c217f6b9…167b` / `fc99637a…636`)
- Golden: 76 passed ×2 (identical); p14c dir: 90 passed; canonical golden report byte-identical double-run
- P13-M: 3 passed
- Full pytest: **459 passed, 0 failed**, 2 warnings (was 437; +22 production tests)

Boundaries: `research_end = 2026-09-22`, `virgin_start = 2026-09-23` unchanged; P13-T STOPPED / NOT EXECUTED; P13-U protected; no real virgin data used. No factor/policy/calibration/recommendation/alpha changes. P14-D NOT started.

Stopping here; awaiting independent acceptance.

P14-D remains blocked.

## P14-C Production Implementation — Narrow Repair (P14-C-COMP-BLOCKER-001) — 2026-10-01

Root cause: `ExpectedContract.completeness()` derived `missing_entities` / `missing_dates` as literal `E − A_entity` / `D − A_date`, so a contract-declared absence pair could leak a date into `missing_dates` (e.g. us_index_daily's declared-absent 2026-03-03), violating the Contract §9.2 note that X enters no `missing_*` set.

Repair (production changes limited to the completeness semantic + regression tests):

- satisfaction is measured ONLY by `A_pair ∩ R` (an actual pair outside P satisfies nothing);
- `missing_entities` / `missing_dates` are derived from the REQUIRED universe: entities/dates participating in R, satisfied by `A_pair ∩ R`;
- declared absences therefore enter no `missing_*` set; coverage still counts only R.

Regression tests added (`tests/test_p14c_production.py`, +4): partial declared absence (all missing sets empty, coverage 1.0); entire entity declared absent (R empty, coverage 1.0); mixed required+absence with an out-of-P actual pair proving only `A_pair ∩ R` satisfies; production-path Case 4 (`us_index_daily` coverage 1.0, all missing sets empty, class EXPECTED_ABSENCE) and the completeness quality dimension's failing-source set exactly `{company_announcement, parse_failure_source}` (genuine UNEXPECTED_MISSING / PARSE_FAILURE evidence), never us_index_daily.

Validation: audit PASS 0/0 (61/61/61); golden 76 ×2; p14c 90; P13-M 3; full pytest **463 passed / 0 failed**; Contract SHA `c217f6b9…167b` and Matrix SHA `fc99637a…636` unchanged; golden report byte-identical (`09cca5b0…`); boundary `2026-09-22`/`2026-09-23` unchanged; P13-T STOPPED; P13-U protected.

P14-D remains blocked.


## P14-C Production Implementation — Independent Acceptance — 2026-10-01

**Decision: PASS / ACCEPTED.**

Independently accepted against final implementation HEAD `06250722e5660975733695c1ffd956cde9a8c118`, following the narrow repair for P14-C-COMP-BLOCKER-001.

### Independent verification

1. **Narrow repair scope is clean.** Compare `5ed21175c914aa4e45c04272f6310c8a0668c63e..06250722e5660975733695c1ffd956cde9a8c118` contains only `src/astock_v2/information/expected_contract.py`, `tests/test_p14c_production.py`, and this status documentation. The repair changes only completeness semantics and regression coverage.
2. **Blocking semantic defect is repaired.** `missing_entities` and `missing_dates` are now derived from the required universe `R = P - X) and satisfied pairs `A ∩ R`; declared EXPECTED_ABSENCE pairs therefore cannot leak into `missing_*`. Out-of-P actual pairs cannot satisfy required entities/dates.
3. **Regression coverage is explicit.** Four new tests cover partial declared absence, an entirely declared-absent entity, mixed required/absence with an out-of-P actual pair, and the real production audit path including the completeness quality dimension.
4. **Frozen artifacts remain unchanged.** Contract SHA remains `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b`; Matrix SHA remains `fc99637a74b6fb08fea977a6edcb6245c3bce1c2636d9736380da4b5599a3636`; Golden layer remains unchanged from `349c6b274b6b72f89bc4db35e5b1961f719011ed).
5. **P14-C regression state is green.** Contract audit PASS with 61/61/61 closure; Golden 76/76; P14-C directory 90/90; P13-M 3/3; full pytest **463 passed, 0 failed, 2 warnings**.
6. **Exact-head CI is independently verified.** GitHub Actions run `36788739673` is successful with pytest job `110136302080` and P13-M job `110136302565`. The pytest checkout log reports `git log -1 --format=%H` as exactly `06250722e5660975733695c1ffd956cde9a8c118`. Contract Harness audit, P14-C tests, Golden tests, P13-M regression and full pytest all completed successfully.
7. **Boundaries remain protected.** `research_end = 2026-09-22`, `virgin_start = 2026-09-23); P13-T remains STOPPED / NOT EXECUTED; P13-U remains protected. No factor, alpha, policy, calibration, recommendation, portfolio, or trading semantics were changed.

### Determination

**P14-C Production Implementation — PASS / ACCEPTED.**

The production implementation now conforms to the frozen Contract, Harness and Golden semantics, including the previously blocking completeness/missing-set invariant. P14-C is independently accepted.

### Next gate

P14-D is now the next authorized implementation stage. It must remain infrastructure/research-only, preserve the P13-T/P13-U boundary, and introduce no production alpha/policy/calibration/recommendation promotion.

## P14-D — PIT-safe Research Information Query Layer — 2026-10-01

Built on the independently accepted P14-C production implementation (`0625072`, accepted `ad032a0`). Frozen baselines untouched: P14-C Contract `c217f6b9…167b`, Matrix `fc99637a…636`, golden report `09cca5b0…`; boundary `research_end=2026-09-22` / `virgin_start=2026-09-23`; P13-T STOPPED; P13-U protected.

### Contract layer

- `docs/contracts/P14-D-DESIGN-CONTRACT.md` (v1, DRAFT): query model (`ResearchQuery`: entity + information_type + as_of, optional source scope), PIT core (`visible <=> available_time <= as_of`, inclusive; event_time NEVER grants visibility), exclusion taxonomy (NOT_YET_AVAILABLE / OUTSIDE_AS_OF / UNRESOLVED_AVAILABILITY — the last reused verbatim from P14-C, no second vocabulary), version selection & restatement (per `(source, source_id)` lineage, latest admissible revision via P14-A `visible_revisions` authority; `as_of < T2` never sees the restated version), result contract (query echo + records with 11-field provenance + exclusions + counts + `result_id` sha256), boundary guard (`as_of >= VIRGIN_START` raises), anti-cheat, invariant registry P14D-001..010.
- `docs/contracts/P14-D-ACCEPTANCE-MATRIX.md`: bidirectional closure 10 contract IDs ↔ 10 golden fixtures ↔ 10 harness tests.
- `scripts/audit_p14d_contract.py`: mechanical audit — PASS 0 findings (canonical IDs, closure 10/10/10, boundary constants, DRAFT status, forbidden control tokens, golden/harness coverage).

### Production layer

- `src/astock_v2/information/research_query.py`: `ResearchQuery` (fails fast on empty fields, timezone-less as_of, and virgin-zone as_of via P13-U `assert_research_zone`), `run_query` (scope filter → OUTSIDE_AS_OF; parseable availability vs as_of → NOT_YET_AVAILABLE; unparseable → UNRESOLVED_AVAILABILITY; version selection by P14-A `visible_revisions`; canonical ordering `(source, source_record_id, available_time, revision, canonical_json)`; `result_id` sha256 of the canonical serialization). Information retrieval only — no scoring/ranking/recommendation/trading surface (mechanically asserted).

### Test layer (tests/contracts/p14d/)

- `test_p14d_contract_harness.py`: document audit PASS, fixture ID density, no real virgin dates in any fixture input (anything ≥ 2026-09-23 must be ≥ 2028 synthetic), production module anti-cheat scan, infrastructure-only API scan.
- `test_p14d_harness.py`: behavioral P14D-001..010 on the production path (normal PIT, future hidden, event_time never grants visibility, deterministic version selection, restatement invisible before T2 and visible at/after T2, byte-identical double-run, provenance completeness, scope leak-proofing, virgin guard with synthetic 2099, infrastructure-only result schema) + inclusive boundary timestamp + unresolved availability (P14-A model rejection proven; run_query defensive branch via a minimal stub) + query validation.
- `test_p14d_golden.py`: 10 frozen fixtures (G-001..G-010) with hand-written expected answers exercised through the production `run_query`; determinism double-run per fixture (records reversed between runs).

### Validation (all executed)

- `python scripts/audit_p14d_contract.py` → PASS, 0 findings, 10/10/10
- `python -m pytest -q -ra tests/contracts/p14d/` → **29 passed** ×2 (deterministic)
- `python scripts/audit_p14c_contract.py` → PASS 0/0, 61/61/61; P14-C SHAs unchanged
- `python -m pytest -q -ra tests/contracts/p14c/` → 90 passed (P14-C regression intact)
- `python -m pytest -q -ra tests/test_industry_relative.py` → 3 passed
- `python -m pytest -q -ra` → **492 passed / 0 failed**, 2 warnings

Workflow: added "Contract Harness audit (P14-D)" step. No P13-T/U, factor, calibration, policy, recommendation, or alpha changes. No real virgin-zone data used anywhere (synthetic 2099 only).

Stopping here; awaiting independent acceptance.

P14-D remains P14-D — do not proceed to P14-E until independent acceptance is granted.

## P14-D Independent Acceptance — 2026-10-01

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E.**

Independently inspected submission HEAD `3ec4837e63df8c668f1057f78e7f9dce0f5702ab` against the independently accepted P14-C state `ad032a0e7ada2b83a697601c79c5ed7b6e526592`.

### Blocking findings

1. **Contract freeze / governance violation.** `docs/contracts/P14-D-DESIGN-CONTRACT.md` is explicitly marked `DRAFT — awaiting independent contract review`, while the same submission already contains production implementation, Golden fixtures, behavioral Harness, and CI wiring. Under the project's frozen workflow, Contract must be independently accepted before Golden/production implementation is accepted. The submission therefore cannot be accepted as a completed P14-D stage.

2. **Version-selection semantic mismatch.** P14-D Contract §8 states that within one `(source, source_id)` lineage, when revisions tie, the earliest `available_time` must win. The production path delegates to P14-A `visible_revisions()`, whose tuple comparison selects the maximum `(revision, available_time, canonical_json)`; therefore equal-revision records select the later `available_time`, contrary to the P14-D Contract. Existing P14-D tests/Gol​den cover differing revisions but do not lock the equal-revision tie case.

3. **Exact-head CI evidence not independently verified.** The repository-side `fetch_commit_workflow_runs` result for `3ec4837e63df8c668f1057f78e7f9dce0f5702ab` returned no workflow runs. ZCODE's commit message reports local validation, but that is not a substitute for independently inspectable exact-HEAD GitHub Actions evidence. The final acceptance gate therefore remains open.

### Positive findings

- P14-D scope is correctly constrained to PIT-safe information retrieval; no production alpha/factor/policy/calibration/recommendation/trading implementation was observed in the submission diff.
- Production query uses `available_time <= as_of` and does not use `event_time` for visibility.
- P13-U `assert_research_zone` is wired into the query entry point.
- P14-D introduces deterministic canonical serialization and a result SHA-256.
- Ten P14-D contract IDs, ten matrix rows, and ten Golden fixtures are present with mechanical closure.
- Tests exercise the production `run_query` path rather than a test-only implementation.
- No real P13-T virgin-zone dates were introduced into the P14-D fixture set; the future-date tests use synthetic dates.
- P14-C Contract/Matrix/Golden assets were not modified by the P14-D submission.

### Required narrow repair

**P14-D-REPAIR-001 — Contract Freeze + Version-Tie + CI Gate**

Do not redesign P14-D.

1. First freeze the P14-D Contract through the normal independent contract gate. The frozen Contract must no longer be DRAFT and must preserve the accepted semantics.
2. Add a Golden/Harness case for two admissible records with identical `(source, source_id, revision)` but different `available_time`; enforce the Contract's declared tie rule. If the intended authoritative P14-A behavior is different, STOP and perform a Contract repair first rather than silently changing production semantics.
3. Repair the production/P14-A tie behavior so implementation and frozen Contract agree. Keep the repair narrow and deterministic.
4. Do not modify P14-C Contract/Matrix/Golden, P13-T/P13-U, factor, alpha, calibration, policy, recommendation, portfolio, or trading logic.
5. Produce an exact-final-HEAD GitHub Actions run and provide independently inspectable run → job → step → log evidence, including checkout SHA == final HEAD.
6. Re-run the complete P14-D Harness/Golden, P14-C regression, P13-M regression, and full pytest suite.

Do not proceed to P14-E until P14-D is independently accepted.

Last independently updated: 2026-10-01.

## P14-D-REPAIR-001 — Contract Freeze + Version-Tie + Exact-CI — 2026-10-01

Narrow repair of the three independent-acceptance blockers on P14-D (`3ec4837`). Scope: `docs/contracts/P14-D-*`, `src/astock_v2/information/pit.py`, `src/astock_v2/information/research_query.py` (docstring-only), `tests/contracts/p14d/*`, this file.

### BLOCKER-002 — same-revision version tie (root cause analysis first)

Layer determination (mandate §7): P14-A `visible_revisions` compared `(revision, available_time, canonical_json)` with tuple-max, so on equal revision the LATEST available_time won — while its own docstring declared "ties on revision resolve to the record available earliest". No P14-A test freezes the opposite semantic (`tests/test_p14a_information.py::test_revision_visibility_boundary` covers different revisions only). Therefore the documented contract semantic (`same revision → earliest available_time`) is correct and the comparison direction was the defect.

Fix (`src/astock_v2/information/pit.py`): explicit precedence — higher revision wins; equal revision → EARLIER available_time wins; equal both → smallest canonical_json. Docstring updated to state the rule and the repair. P14-A regression: 20 passed.

Freeze evidence chain (Contract → Matrix → Golden → Production → CI): contract §8 v1.1 defines the exact chain; Matrix P14D-004 row references G-011 + `test_p14d_011_same_revision_tie_earliest_wins`; golden fixture `G-011.json` (mandate scenario: source TEST, source_id R-TIE-001, revision 1, A 09:00 / B 10:00, as_of 11:00 → A selected) hand-written and executed through the production `run_query` (insertion-order-invariant `result_id`); harness test added; `scripts/audit_p14d_contract.py` E011 mechanically ties all four layers (contract tokens + matrix reference + fixture existence).

### BLOCKER-001 — contract freeze

P14-D Contract frozen as **v1.1** (`状态：FROZEN — P14-D-REPAIR-001 — awaiting independent acceptance`; no self-acceptance wording). Not a word swap: §8's tie-break chain was made exact, the Matrix status/rows updated to match (G-011), the audit's status check now requires FROZEN and still bans PASS/ACCEPTED, and E011 enforces Contract↔Matrix↔Golden↔Harness consistency. Audit: PASS 0 findings (10 contract IDs / 10 matrix IDs / 11 goldens / 11 harness tests).

### BLOCKER-003 — exact-head CI

Final repair HEAD pushed and verified: workflow run on the exact HEAD with checkout SHA == final HEAD (coordinates in the final report).

### Validation (all executed)

- `python scripts/audit_p14d_contract.py` → PASS 0 (10/10/11)
- `python -m pytest -q -ra tests/contracts/p14d/` → **32 passed** ×2
- `python -m pytest -q -ra tests/test_p14a_information.py` → 20 passed (P14-A regression)
- `python scripts/audit_p14c_contract.py` → PASS 0/0 (61/61/61); P14-C SHAs unchanged (`c217f6b9…167b` / `fc99637a…636`); golden report `09cca5b0…` unchanged
- `python -m pytest -q -ra tests/contracts/p14c/` → 90 passed; `tests/test_industry_relative.py` → 3 passed
- `python -m pytest -q -ra` → **495 passed / 0 failed**

Restatement semantics re-verified (G-005 + harness P14D-005): T1 <= as_of < T2 sees only the original revision; as_of >= T2 sees the restatement. PIT visibility and determinism checks all green. Boundary `2026-09-22`/`2026-09-23` unchanged; P13-T STOPPED; P13-U protected; no real virgin-zone data in any fixture (synthetic only).

P14-E remains not authorized.


## P14-D Independent Acceptance — REPAIR-001 — 2026-10-01

**Decision: PASS / INDEPENDENTLY ACCEPTED.**

Independent acceptance inspected the actual GitHub repository state at implementation head `7a5b29cb2a7c0ae22bc8dccff35a3c56856839ac`, compared against the prior failed submission `3ec4837e63df8c668f1057f78e7f9dce0f5702ab`, and verified the repair against the three previously blocking findings.

### Acceptance findings

1. **Contract freeze — PASS.** P14-D Design Contract is now explicitly `FROZEN — P14-D-REPAIR-001 — awaiting independent acceptance`, with no self-acceptance marker. Version v1.1 freezes the exact version-selection chain and the audit mechanically requires FROZEN while rejecting PASS/ACCEPTED self-declaration.
2. **Same-revision version tie — PASS.** P14-A `visible_revisions()` now implements: maximum revision → earliest `available_time` on equal revision → smallest `canonical_json` on equal revision and availability. The new G-011 fixture and `test_p14d_011_same_revision_tie_earliest_wins` exercise the production `run_query()` path and verify insertion-order invariance.
3. **PIT / restatement semantics — PASS.** `available_time <= as_of` remains the visibility rule; `event_time` does not grant visibility. Restatement behavior remains frozen and regression-tested.
4. **Boundary / virgin-zone integrity — PASS.** P14-D continues to use the P13-U research-zone guard; fixtures use synthetic future dates only. P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
5. **Scope — PASS.** The repair diff from `3ec4837` is limited to P14-D docs/harness/Golden/audit plus the narrowly required P14-A PIT comparison repair and a documentation-only production query change. No factor, alpha, calibration, policy, recommendation, portfolio, trading, P13-T, P13-U, or P14-C Contract/Matrix/Golden changes were introduced.

### Contract / Matrix / Golden closure

- P14-D Contract IDs: 10/10
- P14-D Matrix IDs: 10/10
- P14-D Golden fixtures: 11
- P14-D Harness tests referenced: 11
- P14-D audit: PASS, 0 hard findings
- P14-C Contract SHA unchanged: `c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b`
- P14-C Matrix SHA unchanged: `fc99637a74b6fb08fea977a6edcb6245c3bce1c2636d9736380da4b5599a3636`
- P14-C canonical Golden report unchanged: `09cca5b0985265deddb42672b770efd88f82152a46b473acec7d1bb8970438f4`

### Exact-head GitHub Actions evidence

- Final implementation HEAD: `7a5b29cb2a7c0ae22bc8dccff35a3c56856839ac`
- Workflow: `tests`
- Run: `36798963447`
- Event: push to `main`
- Pytest job: `110168771501` — success
- P13-M job: `110168771243` — success
- Checkout evidence: workflow log fetches `7a5b29cb2a7c0ae22bc8dccff35a3c56856839ac`, checks out `origin/main`, and `git log -1 --format=%H` returns the same SHA.
- P14-C Contract Harness audit: PASS
- P14-D Contract Harness audit: PASS
- P13-M regression: PASS (3 passed)
- Full pytest: 495 passed, 0 failed, 2 warnings
- All workflow jobs and all required steps completed successfully.

### Independent acceptance result

P14-D-REPAIR-001 is independently accepted. The previous three blockers are closed. P14-E is **not automatically authorized by this status entry**; it requires a separate phase contract / acceptance process and must preserve the existing P13-T STOPPED and P13-U PROTECTED boundaries.

Last independently updated: 2026-10-01.


## P14-E — Contract Draft — 2026-10-01

- P14-D = PASS / INDEPENDENTLY ACCEPTED (repair `7a5b29c`, acceptance recorded above).
- P14-E = CONTRACT DRAFT: `docs/contracts/P14-E-DESIGN-CONTRACT.md` (STATUS: DRAFT, `P14-E is not implementation-authorized`) + `docs/contracts/P14-E-ACCEPTANCE-MATRIX.md` (STATUS: DRAFT, 17 rows, verification methods are plans only).
- P14-E implementation = NOT AUTHORIZED until the contract passes independent Contract acceptance. No Golden / Harness / src changes were created.
- Consistency checks executed: 17 unique Contract IDs, 17 unique Matrix rows, Contract-Matrix closure 17/17, boundary constants present, authority references (P14-A/B/C/D, visible_revisions, raw_payload_hash, ingestion_id, P14-C/D taxonomy) verified.
- Potential dependency conflicts: NONE (P14-E consumes P14-D results and P14-B identity primitives read-only; no upstream semantic change required by the draft).


## P14-E-002 — Acceptance Matrix Freeze + Golden Test Design — 2026-10-01

- `docs/contracts/P14-E-ACCEPTANCE-MATRIX.md` → **STATUS: FROZEN** (v2): 17 rows, 7 columns each (Matrix ID / Contract ID / Requirement / Verification Method / Golden Fixture / Expected Result / Failure Condition), bound to Golden G-001..G-012; P14E-M-016's Golden column is `N/A (source scan)` by design. FROZEN is explicitly not PASS/ACCEPTED — PASS awaits Harness execution.
- `docs/contracts/P14-E-GOLDEN-DESIGN.md` → **STATUS: DESIGN ONLY**: G-001..G-012 each with Input / Expected Evidence / Expected Bundle / Expected Failure / Contract Coverage; plus a mechanical source-scan design (P14E-016). Coverage 17/17 contract IDs; all timestamps synthetic (research-zone March 2026 or 2099); real virgin window excluded by construction.
- No pytest / Harness / `tests/contracts/p14e/` created; no src/data changes; P14-D ACCEPTED untouched; P13-T STOPPED; P13-U PROTECTED.

P14-E implementation remains NOT AUTHORIZED. Next gated stage: Harness.

## P14-E-002-REPAIR-001 — Golden Design Semantic Repair — 2026-10-01

**Decision: PASS / INDEPENDENTLY ACCEPTED.**

Independently inspected against the actual GitHub `main` HEAD `13fcd47267c479ff62ecdac554daf7b04005eabe`, compared with the failed P14-E-002 baseline `171ca2bd13a15cddca3adfe091c2c026d13c2b03`.

### Acceptance findings

1. **Scope — PASS.** The repair is exactly one commit ahead of the failed submission and modifies only:
   - `docs/contracts/P14-E-GOLDEN-DESIGN.md`
   - `docs/contracts/P14-E-ACCEPTANCE-MATRIX.md`
   - `docs/PROJECT_STATUS.md`
   No `src/**`, `tests/**`, `data/**`, `tests/contracts/p14e/**`, Harness, or production implementation changes were introduced.
2. **G-004 / G-007 exclusion semantics — PASS.** The design now matches the inspected P14-D `run_query()` behavior: an earlier-as_of bundle may carry the four-field exclusion `{source, source_id, reason, available_time}`, while the post-as-of record's payload, `raw_payload_hash`, `ingestion_id`, future Evidence, future candidate trace, and future revision-selection state are prohibited from the earlier bundle.
3. **G-002 identity/bundle semantics — PASS.** The design correctly distinguishes `evidence_id` from `bundle_id`: `ingested_at` is excluded from `evidence_id), but may be part of the canonical bundle content. The invariant is correctly narrowed to the P14-B duplicate-attempt path: a rejected DUPLICATE attempt does not overwrite the canonical stored record and therefore does not change the resulting Evidence or bundle.
4. **Matrix / Golden closure — PASS.** The frozen Matrix remains 17/17, and the Golden design covers all 17 Contract IDs through G-001..G-012 plus the mechanical source-scan design for P14E-016. P14E-M-014 is synchronized with the repaired G-002 semantics.
5. **Virgin-zone integrity — PASS.** No real P13-T virgin dates were introduced. The design continues to use synthetic dates only for future-date guard testing. P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
6. **Governance — PASS.** P14-E remains implementation NOT AUTHORIZED. This repair does not self-promote the phase to Harness or implementation.
7. **Exact-head CI — PASS.** GitHub Actions run `36823824639` is a successful push run for exact HEAD `13fcd47267c479ff62ecdac554daf7b04005eabe). The pytest job `110244957759` and p13m job `110244958097` both succeeded. Checkout logs report `git log -1 --format=%H` as the exact final HEAD. P14-C and P14-D contract audits passed; P13-M regression passed; full pytest reported **495 passed / 0 failed / 2 warnings**.

### Independent acceptance result

**P14-E-002-REPAIR-001 is independently accepted.**

This acceptance closes the two blockers from P14-E-002. The next authorized stage is **P14-E Harness / Golden execution design implementation**, but P14-E production implementation, factor/policy/calibration/recommendation promotion, and P14-F remain unauthorized until their own gates are independently passed.

Last independently updated: 2026-10-01.

## P14-E-003 — Harness + Golden Test Implementation — 2026-10-01

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E production implementation or P14-F.**

Independently inspected actual GitHub main HEAD `8b8f2c182f9f6bc95628a558159f3fed49aa07ce` against the independently accepted P14-E-002-REPAIR-001 baseline `13fcd47267c479ff62ecdac554daf7b04005eabe`.

### Positive findings

- Scope is clean: one implementation commit from the accepted baseline; changes are confined to P14-E contract/Harness/Golden test infrastructure, PROJECT_STATUS, and one CI audit step.
- No P14-E production Evidence/Bundle/Provenance runtime was added under `src/`.
- Contract closure is 17/17; Matrix closure is 17/17; Golden fixtures are G-001..G-012; declared Golden coverage is 17/17.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
- Exact-head GitHub Actions run `36846986105` is green. The pytest job `110319367000` checked out exact HEAD `8b8f2c182f9f6bc95628a558159f3fed49aa07ce`; P14-C audit PASS, P14-D audit PASS, P14-E audit PASS, P13-M PASS, and full pytest reported **529 passed / 0 failed / 2 warnings**.

### Blocking findings

1. **P14E-017 reverse traceability is not actually verified.**
   G-001 declares `reverse_trace_resolves_in_raw_store = true`, but the Harness implementation only checks that `ingestion_id` and `raw_payload_hash` strings occur somewhere in the raw JSONL text. It does not parse the authoritative P14-B raw row and verify that the pair belongs to the same canonical raw record identified by `source/source_id/revision`, nor does it verify the full bundle → evidence → raw-record chain. This is weaker than Contract §15 / Matrix P14E-M-017.

2. **P14E-013 durable reload verification is incomplete.**
   `reload_verify()` recomputes `bundle_id`, but does not verify that each Evidence `(ingestion_id, raw_payload_hash)` resolves back to the P14-B `raw_records.jsonl` authority as required by Contract §12. G-009 therefore does not exercise the full reload-time P14-B provenance check; it only proves bundle self-integrity.

3. **P14E-006 one-to-one result/evidence mapping is under-tested.**
   G-005 checks selected revisions, evidence-ID disjointness, bundle-ID difference, and result-ID linkage, but does not assert the Contract's required `result.records ↔ bundle.evidence` one-to-one mapping or the declared counts equality. The Matrix explicitly requires this.

4. **Golden expected values are not consistently authoritative assertions.**
   Several fixture fields are declared as expected invariants but the Harness substitutes hard-coded semantic assertions instead of comparing all declared expected structures. This creates a gap between the frozen Golden fixture and the executable acceptance surface; a change to an unused expected field could pass without detection.

These are Harness/G​olden acceptance defects, not production-runtime defects. Do not add production Evidence/Provenance/Bundle code to fix them.

### Required narrow repair

**P14-E-003-REPAIR-001 — Reverse Trace + Reload Authority + Mapping Closure**

Only repair the Harness/Golden acceptance layer.

Required:
1. Repair G-001/P14E-017 so the test parses P14-B `raw_records.jsonl` and mechanically resolves `bundle.evidence[*].ingestion_id + raw_payload_hash` to the same authoritative raw record, including source/source_id/revision consistency.
2. Repair `reload_verify()` / G-009 so reload verifies both bundle hash integrity and every Evidence identity against the P14-B RawStore authority. A tampered or mismatched raw provenance pair must fail-fast.
3. Repair G-005/P14E-006 to assert exact one-to-one mapping between P14-D `result.records` and bundle Evidence, including counts equality and stable identity correspondence.
4. Audit every G-001..G-012 fixture's `expected` object. Every material expected field must be consumed by an assertion; remove only genuinely redundant fields, and do not silently leave declared expectations unused.
5. Add negative tamper/reverse-trace cases where necessary so the Harness proves failure, not only success.
6. Preserve all current semantic boundaries: no `src/**` production implementation; no P14-A/B/C/D semantic changes; no P13-T/U changes; no factor/alpha/policy/calibration/recommendation/portfolio/trading changes; no P14-F.
7. Re-run P14-E audit, P14-E tests, P14-C regression, P13-M regression, and full pytest. Produce exact-final-HEAD GitHub Actions evidence with checkout SHA == final HEAD.

Do not change the frozen P14-E Contract or Matrix semantics unless an actual dependency contradiction is demonstrated; if one is found, STOP and report `DEPENDENCY_CONTRACT_CONFLICT`.

P14-E production implementation remains **NOT AUTHORIZED**.

Last independently updated: 2026-10-01.

## P14-E-003-REPAIR-001 — Reverse Trace + Reload Authority + Mapping Closure — 2026-10-01

Harness/Golden-layer repair of the four independent-acceptance blockers on P14-E-003 (`8b8f2c1`). Docs/tests only; **no src/** changes** (file pin re-verified); Contract/Matrix semantics untouched.

### Repairs

1. **P14E-017 reverse trace now actually verified** (G-001): the engine parses the authoritative P14-B `raw_records.jsonl` rows and `reverse_trace_resolve()` mechanically resolves each Evidence's `(ingestion_id, raw_payload_hash)` to exactly one raw row with matching `source/source_id/revision/event_time/available_time` — any mismatch raises. Negative case added: a tampered pair (A's ingestion_id + C's payload hash) must be unresolvable (G-001 `tampered_pair_unresolvable`).
2. **P14E-013 reload authority completed** (`reload_verify(path, raw_rows=None)`): reload now verifies bundle-hash integrity AND — when the raw authority is supplied — resolves every Evidence identity back to the P14-B raw rows. G-009 exercises the full path including a negative tamper case: one Evidence `ingestion_id` is flipped AND the bundle hash recomputed, so the authority check (not hash integrity) is what fails the reload (`tampered_reload_raises`).
3. **P14E-006 mapping closure** (G-005): exact one-to-one `result.records ↔ bundle.evidence` asserted per as-of via stable 4-tuple identity (source, source_record_id, revision, ingestion_id), counts equality, and `result_id` linkage for both bundles (engine now exposes `build_bundle_and_result`).
4. **Expected-consumption closure** (mechanical, anti-recurrence): `check_fixture` tracks every declared expected leaf; a per-fixture `expected_consumed` check fails on any unconsumed declaration. All twelve fixtures now fully consumed — including the previously hard-coded G-004 `forbidden_fields_absent_everywhere` list, G-007 nested `bundle1/bundle2` expectations, G-008 `valid_evidence_field_count`/`defects`, G-009 `input_orders`/`no_runtime_fields`, G-010 `duplicate_not_new_revision`, and the new negative-case flags. G-006's prose note moved out of `expected` to top-level `notes`. Meta-test added: an injected unconsumed expected key must be flagged. Audit now reports `expected_consumption: 12/12 fixtures fully consumed`.

### Validation (all executed)

- `python scripts/audit_p14e_contract.py` → **PASS**, closures PASS/PASS, expected_consumption 12/12, 0 failures
- `python -m pytest -q -ra tests/contracts/p14e/` → **35 passed** (canonical report byte-identical double-run)
- `python -m pytest -q -ra tests/contracts/p14c/` → 90 passed; `tests/test_industry_relative.py` → 3 passed
- `python -m pytest -q -ra` → **530 passed / 0 failed**, 2 warnings

P13-T STOPPED / NOT EXECUTED; P13-U PROTECTED; P14-D PASS untouched; P14-E production implementation **NOT AUTHORIZED** (src file pin re-verified).

P14-F not started. Awaiting independent acceptance.

## P14-E-003-REPAIR-001 — Independent Acceptance — 2026-10-01

**Decision: PASS / INDEPENDENTLY ACCEPTED.**

Independent acceptance inspected actual GitHub main HEAD `6e0303bdddb884ddabb6513f70f69d36da645215` against the failed P14-E-003 submission `8b8f2c182f9f6bc95628a558159f3fed49aa07ce`.

### Acceptance findings

1. **P14E-017 reverse traceability — PASS.** The Harness now parses the authoritative P14-B `raw_records.jsonl` and resolves each Evidence `(ingestion_id, raw_payload_hash)` to exactly one raw record, then verifies `source/source_id/revision/event_time/available_time`. G-001 also contains a negative mismatched-pair case that must fail.
2. **P14E-013 reload authority — PASS.** `reload_verify()` checks bundle hash integrity and, when the P14-B authority rows are supplied, resolves every Evidence back to that authority. G-009 recomputes the tampered bundle hash before reload, proving the failure comes from provenance authority rather than bundle-hash mismatch.
3. **P14E-006 mapping closure — PASS.** G-005 now exercises both as-of bundles and asserts exact one-to-one `result.records ↔ bundle.evidence` identity, counts equality, and `result_id` linkage.
4. **Golden expected-consumption closure — PASS.** Every declared expected leaf is mechanically tracked. The audit reports **12/12 fixtures fully consumed**, and the meta-test proves that an injected unused expected key causes failure. G-006 prose was correctly moved from `expected` to `notes`.
5. **Scope / production boundary — PASS.** The repair is one commit from the failed submission and contains no `src/**` changes. The P14-E production Evidence/Provenance/Bundle runtime remains absent and the source-file pin remains enforced. P14-A/B/C/D semantics are untouched.
6. **Contract / Matrix / Golden closure — PASS.** P14-E Contract remains independently accepted; Matrix remains frozen; all 17 Contract IDs remain covered; G-001..G-012 remain present.
7. **Virgin-zone integrity — PASS.** No real P13-T virgin-zone data was introduced. P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
8. **Exact-head CI — PASS.** GitHub Actions run `36851919169` is a successful push run for exact HEAD `6e0303bdddb884ddabb6513f70f69d36da645215`. Pytest job `110335324915` and P13-M job `110335325411` both succeeded. Checkout logs explicitly fetched and checked out the exact HEAD SHA. The P14-C, P14-D and P14-E contract audits all passed; P13-M passed; full pytest reported **530 passed / 0 failed / 2 warnings**. All required workflow steps completed successfully.

### Independent acceptance result

**P14-E-003-REPAIR-001 is independently accepted.**

This closes the P14-E-003 Harness/Golden acceptance blockers. The next authorized stage is **P14-E production implementation Contract/Design Gate** only; implementation must still proceed through a separate Contract → Matrix → Golden Design → Harness → Production → CI → independent acceptance sequence. P14-F is not authorized yet.

P13-T remains STOPPED / NOT EXECUTED. P13-U remains PROTECTED.

Last independently updated: 2026-10-01.


## P14-E-004 — Production Implementation Contract / Design Gate — 2026-10-01

Docs-only gate: the accepted P14-E semantics frozen into an implementable production blueprint. **No src/**, no data/, no tests/ changes; P14-E-003 Harness/Golden untouched (semantic acceptance authority).

- `docs/contracts/P14-E-PRODUCTION-DESIGN-CONTRACT.md` (STATUS: DRAFT, `P14-E Production Contract v1.0`, SHA-256 `347261cb437e7dac473c489847af47c543881c4edcfc3d68ad2db83535d976ea`): module layout (evidence.py + evidence_store.py only; src file set pinned), identity classes (Evidence Identity 8 fields / Content / Provenance / Ingestion — P14-B `ingestion_id` formula verbatim), ingested_at four-dimension semantics (audit-only for identity; DUPLICATE -> no fork -> bundle_id unchanged because the rejected attempt never enters the stored record set), PIT inheritance, selection chain + frozen enums, candidate-trace leak prohibition (four-field exclusion; knowing existence != leaking content), mapping_key 1:1 closure, bundle model with field-participation table, canonical serialization spec, persistence (evidence_bundles.jsonl append-only/idempotent/reload with P14-B authority verification), reverse-trace API with four-class error taxonomy (refines Golden's raise-only assertions — compatibility note N3; REPAIR-001 unified the miscounted "five-class" to the actual four frozen classes), tamper matrix Cases A-F, missing/failure state semantics, reproducibility boundary, contract versioning/freeze rule, anti-cheat, infrastructure-only scope.
- `docs/contracts/P14-E-PRODUCTION-ACCEPTANCE-MATRIX.md` (STATUS: DRAFT): 23 rows (P14E-P-M-001..023), 8 columns each, closure 23/23, Golden/Test binding to P14-E-003 fixtures or future production Harness checks.

Dependency audit executed against actual implementations: ingestion_id formula MATCH, PIT boundary MATCH, exclusion field set MATCH, evidence_id formula consistent with Golden engine, selection chain frozen, persistence/duplicate/adapter_version semantics compatible. Compatibility notes N1 (P14-B DUPLICATE collapses same-key same-payload candidates at storage), N2 (canonical tiebreak reachable only across merged record sets), N3 (reverse-trace taxonomy refinement) frozen into the contract. **DEPENDENCY_CONTRACT_CONFLICT: NONE.**

Verification: consistency checks PASS (23 unique dense contract IDs, 23 unique matrix rows, closure 23/23, no vague invariant wording, boundary/taxonomy tokens complete); full regression untouched. Production Implementation = NOT AUTHORIZED; P14-F = NOT AUTHORIZED; P13-T STOPPED; P13-U PROTECTED.


## P14-E-004 Independent Acceptance — 2026-10-01

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E production implementation.**

Independently inspected against submitted production-design HEAD `f3230c1f743794be0d2c8869042b6800012e6350` and the prior accepted P14-E-003 state.

Verified positive:
- Production-design submission is docs-only: exactly `docs/contracts/P14-E-PRODUCTION-DESIGN-CONTRACT.md`, `docs/contracts/P14-E-PRODUCTION-ACCEPTANCE-MATRIX.md`, and the `PROJECT_STATUS.md` status update changed from the accepted baseline.
- No `src/**`, data, production runtime, Golden, or Harness changes were introduced.
- Contract IDs P14E-P-001..023 and Matrix IDs P14E-P-M-001..023 are dense and claimed 23/23 closure.
- The design preserves P14-B RawStore authority, P14-A/P14-D PIT/version-selection authority, P13-U protection, and explicitly keeps production implementation NOT AUTHORIZED.
- The production blueprint covers Evidence identity, PIT, version/restatement provenance, result↔evidence mapping, bundle identity, persistence, reverse trace, tamper detection, failure states, reproducibility, and anti-cheat scope.

### Blocking finding 1 — exact-head CI evidence missing

The submitted HEAD `f3230c1f743794be0d2c8869042b6800012e6350` has no independently retrievable GitHub Actions workflow run through the available commit-run evidence. The workflow lookup returned an empty run set for this commit. The P14-E-004 task explicitly required final-head CI evidence and exact checkout verification.

Therefore the claimed local “full regression untouched” statement cannot substitute for independent GitHub CI verification.

**Required repair:** expose a GitHub Actions run for the final repaired HEAD, verify the workflow checkout SHA equals that exact HEAD, and inspect the required jobs/steps. Do not rely on a nearby commit's CI.

### Blocking finding 2 — reverse-trace taxonomy is internally incomplete

P14E-P-014 and P14E-P-M-014 repeatedly state a **five-class** reverse-trace taxonomy, but §11 actually defines only four named classes:

- REVERSE_TRACE_NOT_FOUND
- REVERSE_TRACE_AMBIGUOUS
- REVERSE_TRACE_IDENTITY_MISMATCH
- RAW_RECORD_CORRUPTED

The accompanying Matrix row also lists only four negative cases. The text “hash mismatch = NOT_FOUND” does not create a fifth class, while the contract explicitly claims five classes.

This is a contract/matrix semantic closure defect, not merely wording.

**Required repair:** reconcile P14E-P-014 and its Matrix row to one authoritative taxonomy. Either define the genuinely intended fifth class with precise trigger/semantics and corresponding Matrix coverage, or change all references from five-class to four-class if four is the actual intended frozen taxonomy. Do not invent a fifth error merely to satisfy the count.

### Non-blocking but required cleanup

`PROJECT_STATUS.md` contained contradictory historical roadmap wording saying P14-E was still “CONTRACT DRAFT / IMPLEMENTATION NOT AUTHORIZED” while the new P14-E-004 section declared the Design Gate COMPLETE. The roadmap label has been normalized to “ACCEPTED / PRODUCTION IMPLEMENTATION NOT AUTHORIZED”; the original P14-E Contract remains historically accepted and production implementation remains separately gated.

### Boundary

- P13-T: STOPPED / NOT EXECUTED.
- P13-U: PROTECTED.
- P14-F: NOT AUTHORIZED.
- P14-E production runtime: NOT AUTHORIZED.
- No factor / alpha / calibration / policy / recommendation / portfolio / trading changes are authorized by this repair.

**Do not proceed to P14-E production implementation until the two blocking findings are independently rechecked and accepted.**

Last independently updated: 2026-10-01.

## P14-E-004-REPAIR-001 — Exact-head CI + Reverse-Trace Taxonomy Repair — 2026-10-01

Narrow repair of the two P14-E-004 blocking findings (`c5da132`). Docs-only; no src/**, data/, tests/ changes; P14-E-003 accepted assets untouched.

### REPAIR-001-B — reverse-trace taxonomy (Decision: FOUR-CLASS)

Evidence survey: the accepted P14-E-003 Golden engine raises only two shapes (unresolved / identity mismatch); Production Contract §11 defines exactly four named classes; hash mismatch manifests as REVERSE_TRACE_NOT_FOUND because in the authoritative RawStore state a wrong (ingestion_id, raw_payload_hash) pair is indistinguishable from a nonexistent row — same detection condition (zero matches on the pair lookup), same authoritative state, same fail-fast handling. A fifth class would be an artificial split; per the acceptance mandate the count was unified to the actual frozen taxonomy.

Changes: `P14-E Production Contract` bumped to **v1.1** per its own versioning rule — revision history records the correction; N3 note and invariant P14E-P-014 now state **four-class**; Matrix row P14E-P-M-014 synced ("reverse trace 四类错误分类"). New contract SHA-256: `8619873053dd29736ebd7f61c4c88edf4e9406ae2adb71d45a4a5a5f738ef6ff`. Closure re-verified 23/23 (0 orphan/duplicate/undefined); P14E-P-014 ↔ P14E-P-M-014 fully consistent. Residual "五类" appears only inside the revision-history correction quote (audit history).

### REPAIR-001-A — exact-head CI

Final repaired HEAD pushed; workflow run on the exact HEAD verified with checkout SHA == final HEAD (coordinates in the completion report).

Status: P14-E-004-REPAIR-001 COMPLETE — WAITING FOR INDEPENDENT ACCEPTANCE. P14-E Production Implementation = NOT AUTHORIZED; P14-F = NOT AUTHORIZED; P13-T = STOPPED / NOT EXECUTED; P13-U = PROTECTED.


## P14-E-004 Independent Acceptance — 2026-10-01

**Status: PASS / INDEPENDENTLY ACCEPTED** (Design Gate acceptance recorded by the Acceptance Owner)

**Decision: Independent Acceptance Passed.** This is a Design Gate acceptance — it accepts the Production Implementation Contract and its acceptance blueprint. It is **not** a Production Implementation Authorization.

### Baseline

- HEAD: `a72502f98a1da6aaa39ce8e048b180a0e074b466`
- Commit: `docs: P14-E-004-REPAIR-001 four-class taxonomy + exact-head CI`
- Both REPAIR-001 blockers (exact-head CI evidence; reverse-trace taxonomy closure) verified repaired.

### CI Evidence

- Workflow Run: `36895900955` (workflow `tests`, push event, completed / success)
- Pytest Job: `110482698199` — success (P14-C / P14-D / P14-E Contract Harness audit steps, P13-M pooled industry regression step, Full pytest suite step all success)
- P13-M Job: `110482697635` — success
- Checkout SHA: `a72502f98a1da6aaa39ce8e048b180a0e074b466`
- Exact-head match: **YES** (workflow checkout SHA == accepted HEAD)

### Acceptance Scope — Verified

P14-E Production Design Contract; P14-E Production Acceptance Matrix; Contract IDs P14E-P-001..023; Matrix IDs P14E-P-M-001..023; reverse-trace taxonomy; exact-head CI; regression tests; boundary constraints.

### Contract Acceptance

```text
P14E-P-001 ~ P14E-P-023: PASS
closure:  23/23
orphan:   0
duplicate: 0
undefined: 0
```

### Reverse Trace Acceptance

Final frozen semantics: **FOUR-CLASS taxonomy**

1. `REVERSE_TRACE_NOT_FOUND`
2. `REVERSE_TRACE_AMBIGUOUS`
3. `REVERSE_TRACE_IDENTITY_MISMATCH`
4. `RAW_RECORD_CORRUPTED`

Note: hash mismatch remains classified as `REVERSE_TRACE_NOT_FOUND`, because the authoritative RawStore lookup has zero matching identity — not because of independent hash-mismatch semantics.

### Test Acceptance

```text
python -m pytest -q -ra: 530 passed / 0 failed
P14-C: PASS      P14-D: PASS
P14-E: PASS      P13-M: PASS
```

### Boundary Freeze

```text
P13-T: STOPPED / NOT EXECUTED
P13-U: PROTECTED
P14-E Production Implementation: NOT AUTHORIZED
P14-F: NOT AUTHORIZED
```

Next allowed phase: **P14-E-005 Production Implementation** (waiting for separate authorization).


## P14-E-005 — Production Implementation Contract Draft — 2026-10-01

Docs-only design gate: the accepted P14-E-004 Production Contract (v1.1) refined into an implementable engineering blueprint. **No src/**, no data/, no tests/ changes; P14-E-003 Harness/Golden untouched.**

- `docs/contracts/P14-E-IMPLEMENTATION-CONTRACT.md` (STATUS: DRAFT, SHA-256 `cf05cd3b1912ca5cec0db4c0fcb00b709ef48310c0bbd4430d013986d9457ad4`): implementation boundary (included/excluded); authority model (P14-B -> P14-D -> P14-E with three prohibitions); six runtime components frozen as seven-tuples (CMP-EVIDENCE / CMP-STORE / CMP-MANAGER / CMP-TRACE / CMP-AUDIT / CMP-VALIDATION — Responsibility/Input/Output/Authority/Failure/Persistence/Test); evidence identity inheritance (8 fields; ingested_at stays audit-only); bundle lifecycle state machine CREATE -> VALIDATE -> FREEZE -> STORED with read-only QUERY/TRACE/AUDIT (allowed/forbidden transitions, required metadata, failure modes per state); reverse-trace FOUR-CLASS frozen (HASH_MISMATCH named only as a forbidden fifth class); persistence rules (frozen JSONL constraint takes precedence over any new store choice); six-layer failure model with Detection/Response/Audit triples; six API interface semantics without implementation code; compatibility conclusions; determinism/anti-cheat/boundary inheritance. Invariants P14E-I-001..024.
- `docs/contracts/P14-E-IMPLEMENTATION-ACCEPTANCE-MATRIX.md` (STATUS: DRAFT): 24 rows (P14E-I-M-001..024), 8 columns each, closure 24/24, bindings to P14-E-003 Golden fixtures or future implementation Harness.

Compatibility: PASS against live implementations (ingestion_id formula, PIT boundary, exclusion field set, result_id re-verified) and against accepted contracts (P14-A/B/C/D, P14-E Design Contract v1.1, Production Contract v1.1, Acceptance Record 144b38f). **DEPENDENCY_CONTRACT_CONFLICT: NONE.**

Verification: consistency checks PASS (24 unique dense contract IDs, 24 unique matrix rows, closure 24/24, FOUR-CLASS preserved with no fifth REVERSE_TRACE_* class, no vague invariant wording). Full regression untouched. P14-E Production Implementation = NOT AUTHORIZED; P14-F = NOT AUTHORIZED; P13-T STOPPED; P13-U PROTECTED.

## P14-E-005-REVIEW-001 — Authority-Aligned create_bundle + Status Sync — 2026-10-01

Narrow review repair of the P14-E-005 Implementation Contract Draft (`2c0a8d9`). Docs-only; no src/data/tests changes; accepted P14-E-003/004 assets untouched.

### Finding A — PROJECT_STATUS sync (FIXED)

Current Phase header had silently drifted to "P14-E-004 — FAIL / REPAIR REQUIRED" (two prior phase-header replacements no-op'd on anchor mismatch without asserts). Now synced: Current Phase = **P14-E-005 — CONTRACT DRAFT / WAITING FOR INDEPENDENT ACCEPTANCE (implementation NOT AUTHORIZED)**; P14-E-004 PASS / INDEPENDENTLY ACCEPTED preserved (added to the Accepted Phases table and Current Commit section: design-gate baseline `a72502f`, acceptance record `144b38f`).

### Finding B — P14-D authority alignment (FIXED)

Contract bumped to **v1.1** per its versioning duty (semantic change: API input responsibility). Frozen rule (bilingual, §3):

> P14-D is the authoritative PIT query and version-selection authority. P14-E consumes the already-resolved P14-D query result. P14-E MUST NOT independently reconstruct, repeat, or replace P14-D PIT visibility or version-selection logic.

`create_bundle` signature frozen as **`create_bundle(query_result, authoritative_evidence_records)`** — query_result = the completed P14-D run_query output (result.query / result_id / records / exclusions); authoritative_evidence_records = the P14-B authoritative record set for Evidence/Provenance/Reverse Trace. The ambiguous `create_bundle(records, query)` form is removed; the runtime never receives a raw query to re-execute visibility/revision-selection/restatement/PIT-filtering. CMP-EVIDENCE input, §6.1 CREATE metadata provenance, §3, and Matrix rows P14E-I-M-003 / M-004 / M-022 synced. ID count unchanged at 24 (rule folded into existing IDs — no ID inflation).

### Finding C — exact-head CI

Delivered with this push: workflow run on the final repaired HEAD with checkout SHA == final HEAD (coordinates in the completion report).

### Verification

- Contract/Matrix closure: 24/24 (0 orphan / 0 duplicate / 0 undefined); 8 columns intact; REVIEW-001 semantics mechanically asserted (frozen signature present, old signature absent, bilingual authority rule present, C1 input free of bare ResearchQuery).
- Full pytest: **530 passed / 0 failed** (documentation-only change; test layer untouched).
- P14-C / P14-D / P14-E audits + P13-M: PASS (CI).

P14-E-005 remains CONTRACT DRAFT — WAITING FOR INDEPENDENT ACCEPTANCE. P14-E-006 NOT AUTHORIZED; P14-E Production Implementation NOT AUTHORIZED; P14-F NOT AUTHORIZED; P13-T STOPPED / NOT EXECUTED; P13-U PROTECTED.


## P14-E-005-REVIEW-001 — Independent Acceptance — 2026-10-02

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E-006.**

Independently inspected actual GitHub main HEAD `70634cbe9e8086d325c2cff7efd377461d3d746a` against the P14-E-005-REVIEW-001 baseline `2c0a8d93faab7ae17d5d8f78509c36949b0b4205`.

### Findings

1. **P14-D authority alignment — PASS.** The Implementation Contract is v1.1. `create_bundle(query_result, authoritative_evidence_records)` is frozen; P14-D is explicitly the authoritative PIT query/version-selection layer; the old `create_bundle(records, query)` signature is absent from the Contract. Matrix rows P14E-I-M-003/M-004/M-022 are synchronized. Contract and Matrix closure are both 24/24.

2. **Scope — PASS.** The exact one-commit diff contains only:
   - `docs/PROJECT_STATUS.md`
   - `docs/contracts/P14-E-IMPLEMENTATION-CONTRACT.md`
   - `docs/contracts/P14-E-IMPLEMENTATION-ACCEPTANCE-MATRIX.md`
   No `src/**`, `data/**`, tests, Golden/Harness, or upstream P14-A/B/C/D changes were introduced.

3. **PROJECT_STATUS current phase — PASS after review repair.** The top-level phase is correctly P14-E-005 CONTRACT DRAFT / WAITING FOR INDEPENDENT ACCEPTANCE, and P14-E-004 remains PASS / INDEPENDENTLY ACCEPTED.

4. **Blocking: exact-head GitHub Actions evidence is not independently retrievable.** The final HEAD `70634cbe9e8086d325c2cff7efd377461d3d746a` has no workflow run exposed by the available commit-run evidence, and its combined commit status is empty. The workflow definition does contain the required P14-C/P14-D/P14-E audits, P13-M regression, and full pytest steps, but a claimed local/embedded completion report cannot substitute for independently retrievable final-HEAD CI evidence. Therefore the required exact-head CI gate is not yet proven.

5. **Blocking: Current Commit provenance was stale in the submitted status file.** The REVIEW-001 submission still identified `2c0a8d93...` as Current Commit even though the actual reviewed HEAD was `70634cbe...`. This acceptance record corrects that pointer; the final acceptance still requires CI evidence for the actual final HEAD.

### Boundary

- P14-E-005 remains CONTRACT DRAFT.
- P14-E Production Implementation remains NOT AUTHORIZED.
- P14-E-006 is NOT AUTHORIZED.
- P14-F is NOT AUTHORIZED.
- P13-T remains STOPPED / NOT EXECUTED.
- P13-U remains PROTECTED.
- No factor / alpha / calibration / policy / recommendation / portfolio / trading changes are authorized.

**Required repair:** expose and independently verify a successful GitHub Actions run for the exact final P14-E-005 HEAD, including checkout SHA equality, P14-C/P14-D/P14-E audits, P13-M, and full pytest. Then resubmit for independent acceptance.

## P14-E-005-REPAIR-002 — Exact-head CI Evidence for the Contract Draft HEAD — 2026-10-02

Response to the P14-E-005-REVIEW-001 verdict (`7803421`). The verdict's Finding 5 (stale Current Commit) was already corrected by the verdict commit itself; the remaining blocker was independently retrievable exact-head CI evidence for `70634cbe9e8086d325c2cff7efd377461d3d746a`.

### Exact-head CI evidence for the P14-E-005 Contract Draft HEAD

- Workflow `tests`, run `36989469157` (event: push, completed / **success**)
  - https://github.com/CGchenggang/a-stock-quantimental/actions/runs/36989469157
- head_sha == `70634cbe9e8086d325c2cff7efd377461d3d746a` (exact-head match **YES**)
- pytest job: **success** — steps include P14-C / P14-D / P14-E Contract Harness audits, P13-M pooled industry regression, and the Full pytest suite
- p13m job: **success** — "P13-M pooled industry regression" step green
- Retrieval endpoints that return this run:
  - `GET /repos/CGchenggang/a-stock-quantimental/actions/runs?head_sha=70634cbe9e8086d325c2cff7efd377461d3d746a`
  - `GET /repos/CGchenggang/a-stock-quantimental/commits/70634cbe9e8086d325c2cff7efd377461d3d746a/check-runs`
  - Note for re-verification: the run appears under workflow-runs and check-runs endpoints, not the legacy combined-status endpoint; the original review-time lookup coincided with the recurring GitHub connectivity outage windows observed from this workspace.

### Current Commit

Current Commit = `70634cbe9e8086d325c2cff7efd377461d3d746a` (set by the verdict commit `7803421`), i.e. Current Commit == the P14-E-005 Contract Draft final HEAD. The evidence-recording and resubmission commits of this repair round are documentation-only and carry no Contract/Matrix/runtime changes.

Boundary: P13-T STOPPED / NOT EXECUTED; P13-U PROTECTED; P14-E Production Implementation NOT AUTHORIZED; P14-E-006 NOT AUTHORIZED; P14-F NOT AUTHORIZED.

P14-E-005-REPAIR-002 COMPLETE — WAITING FOR INDEPENDENT ACCEPTANCE.


## P14-E-005-REVIEW-001 — Independent Acceptance — 2026-10-02

**Decision: PASS / INDEPENDENTLY ACCEPTED.**

Accepted artifact: P14-E-005 Contract Draft at `70634cbe9e8086d325c2cff7efd377461d3d746a`.

### Independent verification

- Finding A — PROJECT_STATUS phase synchronization: PASS.
- Finding B — P14-D authority alignment: PASS. P14-D is frozen as the authoritative PIT query/version-selection layer; P14-E consumes the already-resolved query result. `create_bundle(query_result, authoritative_evidence_records)` is frozen; the old `create_bundle(records, query)` form is absent from the Contract.
- Contract closure: 24/24.
- Matrix closure: 24/24.
- Scope: REVIEW-001 changed only the three permitted documentation files; no `src/**`, `data/**`, tests, Golden/Harness, or P14-A/B/C/D changes.
- Exact-head CI evidence independently verified through workflow run `36989469157`. The run checked out exact target HEAD `70634cbe9e8086d325c2cff7efd377461d3d746a`.
- pytest job `110782044266`: success. P14-C audit PASS, P14-D audit PASS, P14-E audit PASS, P13-M regression PASS, full pytest **530 passed / 0 failed / 2 warnings**.
- P13-M job `110782043983`: success, regression **3 passed**.
- The subsequent docs-only evidence/archive commit `2386e9e58726db5f91a03e374921d2c02e870f34` does not alter the accepted Contract/Matrix/src/tests; it records the exact-head CI evidence for the accepted target HEAD.

### Boundary

- P14-E-005: **PASS / INDEPENDENTLY ACCEPTED**.
- P14-E Production Implementation: **NOT AUTHORIZED**.
- P14-E-006: **NEXT ALLOWED PHASE — GOLDEN / HARNESS DESIGN ONLY**.
- P14-F: NOT AUTHORIZED.
- P13-T: STOPPED / NOT EXECUTED.
- P13-U: PROTECTED.
- No factor / alpha / calibration / policy / recommendation / portfolio / trading changes.

**Next gate:** P14-E-006 Golden / Harness Design. Production implementation remains separately gated and must not begin during P14-E-006.

## P14-E-006 — Independent Acceptance — 2026-10-02

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E production implementation.**

Independently inspected actual GitHub main HEAD `7ec854b28f16e4d42c9df01f563c044440261b8f` against the independently accepted P14-E-005 Contract Draft at `70634cbe9e8086d325c2cff7efd377461d3d746a`.

### Verified positive

- Exact-head GitHub Actions evidence exists: workflow run `37000539665`, head_sha exactly `7ec854b28f16e4d42c9df01f563c044440261b8f`.
- pytest job `110816985050` and P13-M job `110816984930` both succeeded.
- Checkout log explicitly checked out `7ec854b28f16e4d42c9df01f563c044440261b8f`.
- P14-C, P14-D, P14-E audits, P13-M regression, and full pytest all succeeded; full pytest = **550 passed / 0 failed / 2 warnings**.
- Diff from the P14-E-005 accepted baseline contains no `src/**` or `data/**` production changes; P14-E-005 Contract/Matrix themselves were not modified.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.

### Blocking finding 1 — P14-D authority violation inside the P14-E-006 reference implementation

The new `tests/contracts/p14e/golden/implementation.py` defines `create_bundle(query_result, authoritative_evidence_records)`, but internally calls `core.build_bundle_and_result(authoritative_evidence_records, query_result["query"])`.

This re-executes the P14-D query from the raw query instead of consuming the already-resolved P14-D result. That directly violates the independently accepted P14-E-005 REVIEW-001 rule:

> P14-D is authoritative; P14-E consumes the already-resolved P14-D query result and MUST NOT independently reconstruct/repeat/replace PIT visibility or version selection.

The current IG fixtures do not catch this: the positive API fixture verifies only interface presence/validation and does not prove that `query_result["records"]`, `excluded`, and `counts` are authoritative inputs that are consumed without re-querying.

### Blocking finding 2 — expected fields are declared but not semantically tested

IG-104 declares:

- `raw_query_rejected`
- `rawstore_write_rejected`
- `history_rebuild_rejected`

but the harness only proves the stripped-result authority failure. The latter two are accepted merely because the fixture says `true`; no attempted RawStore write or history-rebuild operation is executed and rejected.

Therefore "expected consumption" is syntactic consumption, not semantic verification.

### Blocking finding 3 — audit append-only assertion is vacuous

IG-103 declares `audit_records_append_only=true`, but `AuditLog` records contain no sequence field. The harness therefore falls through to a vacuous `True` condition instead of mechanically proving append-only ordering/immutability.

### Blocking finding 4 — P14-E-006 Golden Design document is internally contradictory

The document still begins with `STATUS: DESIGN ONLY` and says executable tests/Harness must not exist, while the same document now appends:

`P14-E-006 — Implementation Golden Design (IG-101..IG-107)`

with `STATUS: DESIGN COMPLETE / IMPLEMENTED IN HARNESS / AWAITING INDEPENDENT ACCEPTANCE`.

The acceptance audit simultaneously requires the old `STATUS: DESIGN ONLY` token. This is governance/document-state drift and must be reconciled rather than hidden by a passing assertion.

### Blocking finding 5 — PROJECT_STATUS Current Commit is stale

The actual main HEAD is `7ec854b28f16e4d42c9df01f563c044440261b8f`, but the top-level `Current Commit` still points to the previously accepted P14-E-005 HEAD `70634cbe9e8086d325c2cff7efd377461d3d746a`.

The phase header correctly identifies P14-E-006, but the provenance pointer was not updated for the submitted stage.

### Required narrow repair

**P14-E-006-REPAIR-001 — Authority Consumption + Expected Closure + Governance Sync**

Repair only the above five findings.

Required outcomes:

1. Make the P14-E-006 reference/harness path consume an already-resolved P14-D result. It must not call `run_query` or reconstruct PIT/version selection from `query_result["query"]` inside the P14-E API path.
2. Add a deterministic negative/positive fixture proving that mutating or contradicting the supplied resolved result cannot be silently replaced by a fresh P14-D query.
3. Mechanically exercise the IG-104 RawStore-write and history-rebuild prohibitions; no fixture boolean may stand alone as proof.
4. Give audit records a deterministic ordering/sequence invariant and test append-only behavior non-vacuously.
5. Reconcile `P14-E-GOLDEN-DESIGN.md` status language with the actual stage: it may state Golden/Harness Design implemented and awaiting independent acceptance, but must no longer simultaneously claim that executable Harness files are prohibited. Keep P14-E-005 Contracts frozen.
6. Update `PROJECT_STATUS.md` Current Commit to the actual final repaired HEAD and preserve P14-E-005 PASS / INDEPENDENTLY ACCEPTED.
7. Re-run exact-head GitHub Actions after the repair and verify checkout SHA equality, P14-C/P14-D/P14-E audits, P13-M, and full pytest.
8. Keep production implementation NOT AUTHORIZED.

Forbidden: changes to `src/**`, `data/**`, P14-A/B/C/D semantics, accepted P14-E Contracts/Matrix, P13-T/U, factors, alpha, calibration, policy, recommendation, portfolio, trading, or P14-F.

P14-E-006 remains **FAIL / REPAIR REQUIRED** until this repair is independently accepted.


## P14-E-006-REPAIR-001 Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E-006 acceptance or P14-E Production Implementation.**

Independently inspected against ZCODE repair HEAD `aa595c2244d26c32a4e8c36dc4facc9160c49824`, with repair baseline `7ec854b28f16e4d42c9df01f563c044440261b8f`.

Blocking findings:

1. **Authority boundary is still violated.** `tests/contracts/p14e/golden/implementation.py:create_bundle()` no longer calls `run_query()`, but it still executes `core.is_admissible(...)` and `core.select_lineage(...)`. The former re-applies PIT admissibility and the latter re-selects lineage/selection semantics inside P14-E. P14-E-005 explicitly freezes P14-D as the authoritative query/version-selection layer; P14-E must consume the already-resolved `query_result` rather than reconstructing PIT/selection logic.

2. **IG-103 append-only verification remains vacuous.** `AuditLog.append()` still stores records without any `seq` / `sequence_id`. The test explicitly falls back to `True` when sequence fields are absent:
   `if all("seq" in r for r in audit.records) else True`.
   Therefore the claimed strict append-only ordering is not actually verified.

3. **Expected-value closure still contains a non-behavioral assertion.** IG-104 now performs a real RawStore mutation attempt and a real fail-fast history reconstruction attempt, which is an improvement; however `history_state_unchanged` is still asserted only from the fixture expected value rather than measured from before/after state. This leaves the expected field vulnerable to fixture self-certification.

4. **Exact-head CI evidence is absent.** `fetch_commit_workflow_runs(aa595c...)` returns no workflow runs, and combined commit status is empty. Therefore the reported “full pytest 550 passed / P14-E audit PASS” cannot be independently accepted as CI evidence for the actual repair HEAD.

5. **PROJECT_STATUS governance synchronization is still stale at the repair commit.** The repair commit message says Current Commit was synced to `7ec854b`, but the actual repository HEAD is `aa595c2244d26c32a4e8c36dc4facc9160c49824`. This is itself a governance-drift blocker and must be corrected as part of the repair.

Required repair:
- Make `create_bundle()` consume resolved P14-D state without re-running `is_admissible`, `select_lineage`, PIT filtering, revision selection, or restatement selection.
- Add a real monotonic sequence field to AuditLog records and assert strict ordering/uniqueness in IG-103; remove the vacuous fallback.
- Measure IG-104 history state before/after the rejected rebuild and assert equality from actual state, not from a fixture boolean.
- Run GitHub Actions on the final repair HEAD and provide independently retrievable exact-head evidence, including full pytest, P14-C/D/E audits and P13-M regression.
- Synchronize `PROJECT_STATUS.md` Current Commit to the final repair HEAD after the code/doc repair, then run the exact-head CI again if the status commit is part of the accepted state.
- Preserve P14-E-005 accepted Contract and P14-D authority; no `src/**` production implementation; no `data/**`; no P14-F; no factor/alpha/policy/recommendation/trading changes.

Current phase remains blocked. P14-E production implementation remains NOT AUTHORIZED.


## P14-E-006-REPAIR-002 Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E-006 acceptance or P14-E Production Implementation.**

Independently inspected ZCODE repair HEAD `ba500ddc0eb9a6e64f26cf3c718ef53d75945a35`, with repair baseline `aa595c2244d26c32a4e8c36dc4facc9160c49824`.

### Verified positive

- P14-D re-selection calls previously identified in `create_bundle()` are removed: no direct `core.is_admissible(...)`, `core.select_lineage(...)`, or `build_bundle_and_result(...)` call remains in the function.
- `AuditLog.append()` now assigns deterministic `sequence_id = 1,2,3,...`.
- IG-103 now checks uniqueness, strict monotonicity, and starts-from-one without the previous vacuous fallback.
- IG-104 now measures authoritative record state before and after the rejected history-rebuild attempt and asserts actual equality.
- Scope remains limited to the P14-E-006 harness/golden/status/audit layer; no `src/**` or `data/**` production changes are present in the repair diff.

### Blocking findings

1. **Exact-head CI evidence is still absent.** Independent GitHub retrieval for `ba500ddc0eb9a6e64f26cf3c718ef53d75945a35` returns no workflow runs and no combined commit statuses. Therefore ZCODE's reported `550 passed`, P14-C/D/E audits, and P13-M results are not independently verified for the actual repair HEAD. Agent-reported test output cannot substitute for exact-head CI evidence.

2. **PROJECT_STATUS provenance is stale.** The actual repair HEAD is `ba500ddc0eb9a6e64f26cf3c718ef53d75945a35`, but the Current Commit field still identifies the previous repair HEAD `aa595c2244d26c32a4e8c36dc4facc9160c49824`. The repair therefore has not completed the required governance synchronization.

3. **P14-D authority consumption is improved but not yet cleanly demonstrated.** The direct P14-D calls are gone, but `create_bundle()` still derives selection/rejection reasons by inspecting the full authoritative lineage and applying revision/tie comparisons itself (including the unconditional `or True` expression). The frozen Contract says P14-E must carry accepted selection/rejection semantics without redefining P14-D version-selection logic. This path should consume the already-resolved P14-D result rather than infer the winning/rejection semantics again from the raw lineage.

4. **Golden Design remains internally contradictory.** Its status header now says `DESIGN COMPLETE / HARNESS IMPLEMENTED / AWAITING INDEPENDENT ACCEPTANCE`, but the same document still says it is not executable and that pytest/Harness files must not exist. Those statements cannot simultaneously describe the current P14-E-006 stage and should be reconciled; acceptance checks must not preserve the obsolete prohibition merely as a historical string.

### Required narrow repair

**P14-E-006-REPAIR-003**

Repair only the four blockers above:

- make candidate/selection-reason handling consume P14-D's resolved state without independently reconstructing selection semantics;
- reconcile the Golden Design document and its audit expectations to the actual Design+Harness stage;
- synchronize PROJECT_STATUS to the final repair state;
- run GitHub Actions on the final target HEAD and independently verify exact checkout SHA, P14-C/D/E audits, P13-M regression, and full pytest.

Preserve P14-E-005 Contract/Matrix, P14-D authority, P13-T/U boundaries, and the prohibition on production implementation.

**P14-E-006 remains FAIL / REPAIR REQUIRED. P14-E Production Implementation remains NOT AUTHORIZED. P14-F remains NOT AUTHORIZED.**


## P14-E-006-REPAIR-003 Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E-006 acceptance or P14-E Production Implementation.**

Independently inspected final ZCODE repair HEAD `17afd2d71675df86d443fc6093f822cf437970cb` against repair baseline `ba500ddc0eb9a6e64f26cf3c718ef53d75945a35`.

### Verified positive

- Candidate-trace cleanup removed the prior `or True` expression and the prior complex lineage-wide revision comparison.
- Golden Design governance language is now consistent with an implemented Harness awaiting independent acceptance.
- No `src/**` or `data/**` production changes are present in the repair diff.

### Blocking findings

1. **Exact-head GitHub Actions evidence is absent.** GitHub independently returns 0 workflow runs and 0 combined statuses for final HEAD `17afd2d71675df86d443fc6093f822cf437970cb`. ZCODE-reported test results cannot substitute for exact-head CI evidence.

2. **PROJECT_STATUS Current Commit is stale.** The actual final ZCODE HEAD is `17afd2d71675df86d443fc6093f822cf437970cb`, while the file still reports `70634cbe...` as Current Commit.

### Required narrow repair

**P14-E-006-REPAIR-004 — Final CI + Status Synchronization**

- Synchronize PROJECT_STATUS Current Commit to the final implementation state.
- Produce GitHub Actions evidence for the final target HEAD and independently verify exact checkout SHA, P14-C/D/E audits, P13-M regression, and full pytest.
- Preserve P14-E-005 Contract/Matrix, P14-D semantics, P13-T/U, production `src/**`, `data/**`, factors, alpha, calibration, policy, recommendation, portfolio, trading, and P14-F boundaries.

**P14-E-006 remains FAIL / REPAIR REQUIRED. P14-E Production Implementation remains NOT AUTHORIZED. P14-F remains NOT AUTHORIZED.**


## P14-E-006 — Independent Acceptance — 2026-10-03

**Decision: PASS / INDEPENDENTLY ACCEPTED.**

Independently inspected ZCODE implementation HEAD `17afd2d71675df86d443fc6093f822cf437970cb` against the independently accepted P14-E-005 Contract Draft at `70634cbe9e8086d325c2cff7efd377461d3d746a`.

### Acceptance evidence

- Exact-head GitHub Actions workflow run `37079891815` is **completed / success** and its `head_sha` exactly equals `17afd2d71675df86d443fc6093f822cf437970cb`.
- The `pytest` job `111077854245` succeeded. Its steps explicitly include P14-C audit, P14-D audit, P14-E audit, P13-M regression, and Full pytest suite, all completed successfully.
- The `p13m` job `111077854039` succeeded; its P13-M pooled industry regression step completed successfully.
- The exact-head run was triggered by **push** on `main`; therefore the earlier connector limitation that only surfaced PR-associated runs does not invalidate this evidence.
- Golden Design status is internally consistent: **DESIGN COMPLETE / HARNESS IMPLEMENTED / AWAITING INDEPENDENT ACCEPTANCE** before this acceptance, with no remaining prohibition against the implemented Harness.
- P14-E reference implementation consumes the already-resolved P14-D state; the previously identified direct P14-D re-selection calls and lineage-wide re-selection logic are absent from the repaired candidate-trace path.
- IG-103 now has deterministic `sequence_id` values and mechanically verifies uniqueness, strict monotonicity, and start-from-one; no vacuous fallback remains.
- IG-104 measures authoritative state before and after the rejected history-rebuild attempt and verifies actual equality; expected-value fixture booleans are not used as the sole proof.
- Diff from accepted P14-E-005 baseline contains only Golden/Harness/audit/documentation changes; no `src/**` or `data/**` production implementation changes.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
- No factor, alpha, calibration, policy, recommendation, portfolio, trading, or P14-F promotion was introduced.

### Gate result

- **P14-E-006 Golden/Harness: PASS / INDEPENDENTLY ACCEPTED.**
- **P14-E Production Implementation: NOT AUTHORIZED.**
- **P14-F: NOT AUTHORIZED.**
- **P13-T: STOPPED / NOT EXECUTED.**
- **P13-U: PROTECTED.**

### Next authorized stage

The next stage is **P14-E Production Implementation Design/Tasking only**, under the frozen P14-E Contract/Matrix and the accepted Golden/Harness evidence. Any production implementation remains separately gated and must receive a new exact-head CI + independent acceptance before authorization.



## P14-E Production Implementation Design / Tasking — 2026-10-02

Docs-only design package. **No src/**, no data/, no tests/ changes.**

- `docs/design/p14e/P14-E-PRODUCTION-IMPLEMENTATION-DESIGN.md` (STATUS: DESIGN READY)
- `docs/design/p14e/P14-E-PRODUCTION-IMPLEMENTATION-MATRIX.md` (STATUS: DRAFT, 47 rows)
- `docs/design/p14e/P14-E-PRODUCTION-MIGRATION-PLAN.md` (STATUS: DRAFT)

Dependency audit: ALL COMPATIBLE. DEPENDENCY_CONTRACT_CONFLICT: NONE.
Production Implementation = NOT IMPLEMENTED / NOT AUTHORIZED.


## P14-E Production Implementation Design / Tasking — Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-E Production Implementation.**

Independently inspected actual GitHub HEAD `9c2913d998e1b2577ba6e58ec460757a583ea99f` against the accepted P14-E-006 Golden/Harness gate `17afd2d71675df86d443fc6093f822cf437970cb`.

### Verified positive

- Submission diff from `17afd2d` is docs-only: `docs/PROJECT_STATUS.md` plus the three new design/tasking documents.
- No `src/**`, `data/**`, tests, P14-E Contract/Matrix, P14-A/B/C/D, P13-T/U, or P14-F production changes are present in the submission diff.
- The design correctly preserves P14-D as the sole PIT visibility/version-selection authority and explicitly forbids P14-E from re-running `run_query`, `is_admissible`, `visible_revisions`, `select_lineage`, or other PIT/selection logic.
- The proposed production surface is appropriately limited to `evidence.py` and `evidence_store.py`, with twelve implementation tasks and a separate production CI gate.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.

### Blocking findings

1. **Reverse-trace taxonomy contradicts the frozen P14-E Production Contract.**
   The accepted Production Contract v1.1 freezes **FOUR-CLASS** reverse trace semantics:
   `NOT_FOUND / AMBIGUOUS / IDENTITY_MISMATCH / RAW_RECORD_CORRUPTED`.
   The new Production Acceptance Matrix row `P14E-PI-T-014` describes P14E-P-014 as **“reverse trace 五类错误”**. This directly reintroduces the exact taxonomy error repaired and independently accepted in P14-E-004-REPAIR-001. The same matrix elsewhere correctly says FOUR-CLASS, so the package is internally inconsistent.

2. **Acceptance Matrix closure header is arithmetically inconsistent with its own rows.**
   The matrix contains **47** rows (`P14E-P-001..023` + `P14E-I-001..024`), but its header says they are mapped to `P14E-PI-T-001..024` production test tasks. The actual rows run through `P14E-PI-T-047`. The closure statement must be corrected to `P14E-PI-T-001..047` (or otherwise explicitly define a different grouping), and the one-to-one/coverage claim must be made mechanically consistent.

3. **PROJECT_STATUS was not synchronized to the submitted design HEAD.**
   Before this acceptance write-back, the repository still identified `17afd2d` as Current Commit even though the actual submission HEAD is `9c2913d998e1b2577ba6e58ec460757a583ea99f`. This is a governance/provenance defect in the submitted stage itself.

### Non-blocking observation

- No independently retrievable workflow run or combined status was returned for `9c2913d998e1b2577ba6e58ec460757a583ea99f` through the available GitHub Actions endpoints. Because this stage is docs-only and introduces no executable code/tests, this is recorded as an evidence gap rather than the primary rejection reason. The production implementation stage will require exact-head CI evidence before acceptance.

### Required narrow repair

**P14-E Production Implementation Design / Tasking — REPAIR-001**

Repair only the three blocking findings above:

- Change every Production Matrix reference to P14E-P-014 to the frozen FOUR-CLASS taxonomy; do not alter the accepted taxonomy or create a fifth class.
- Correct the matrix closure header/coverage accounting so all 47 declared contract invariants map consistently to `P14E-PI-T-001..047`, with no orphan/duplicate/undefined rows.
- Synchronize `PROJECT_STATUS.md` Current Commit to the final repair HEAD after all design changes.
- Re-run the design-package closure/audit and preserve the docs-only scope.

Do not implement production code. Do not modify `src/**`, `data/**`, P14-E Contract/Matrix/Golden/Harness, P14-D semantics, P13-T/U, factors, alpha, calibration, policy, recommendation, portfolio, trading, or P14-F.

**Current gate remains:**
- P14-E Production Implementation Design / Tasking: **FAIL / REPAIR REQUIRED**
- P14-E Production Implementation: **NOT AUTHORIZED**
- P14-F: **NOT AUTHORIZED**
- P13-T: **STOPPED / NOT EXECUTED**
- P13-U: **PROTECTED**


## P14-E Production Implementation Design / Tasking — Independent Acceptance Record — 2026-10-03

**PASS / INDEPENDENTLY ACCEPTED.**

Final design repair submission accepted at `bad52f16acaf7f5091215283672834291607cb26`.

The accepted package has:
- FOUR-CLASS reverse-trace taxonomy consistent with the frozen Production Contract v1.1.
- 47/47 Production Matrix coverage: P14E-P-001..023 (23) + P14E-I-001..024 (24), mapped through P14E-PI-T-047, with no orphan/duplicate/undefined mapping identified.
- Docs-only scope; no production runtime implementation.
- P14-D authority, P13-T STOPPED / NOT EXECUTED, and P13-U PROTECTED boundaries preserved.

**Next authorized stage: P14-E Production Implementation.**

Production implementation remains **NOT IMPLEMENTED / NOT AUTHORIZED** until its own exact-head CI and independent acceptance are completed.

## P14-E Production Implementation — Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-F.**

Independently reviewed against the actual `main` HEAD `12828101a4e393d2277d8ccffea529deb0138189`.

### Positive findings

- Production implementation is present in `src/astock_v2/information/evidence.py` and `evidence_store.py`.
- Production diff from the accepted Design/Tasking baseline `bad52f16acaf7f5091215283672834291607cb26` is limited to the authorized P14-E implementation/test/audit/status surfaces; no `data/**` change was observed.
- Exact-head GitHub Actions run `37104761266` is green at the actual `main` HEAD `12828101a4e393d2277d8ccffea529deb0138189`; pytest and P13-M jobs both succeeded.
- The pytest job explicitly ran P14-C, P14-D, P14-E audits, P13-M pooled regression, and the full pytest suite; the run reported **568 passed / 2 warnings / 0 failed**.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.

### Blocking findings

1. **PIT-unsafe candidate-trace construction.** P14-E Contract §6.2 requires candidate_trace to contain only records admissible at the bundle's own as_of. Production `create_bundle()` places every non-selected record in a selected lineage into candidate_trace without filtering it by the already-resolved P14-D admissible state. A post-as-of higher revision can therefore appear in a historical bundle's candidate_trace, and the selection/rejection labeling also reasons over such records. This violates the frozen P14-E PIT boundary and duplicates P14-D version-selection semantics.

2. **P14-D selection semantics are still re-derived inside P14-E.** `_selection_reason()` and `_rejection_reason()` independently compare revision and available_time to classify winners/losers. The accepted architecture permits mechanical labeling of P14-D's resolved state, but the current implementation uses the full authoritative lineage—including records outside the resolved admissible set—to infer those labels. The implementation therefore cannot be considered a pure consumer of P14-D's resolved decisions.

3. **P14-B authority verification is optional on reload.** `EvidenceStore.reload()` performs authoritative RawStore verification only when `raw_store_path` is supplied and exists. Contract §12 makes the `(ingestion_id, raw_payload_hash)` → P14-B `raw_records.jsonl` verification mandatory on reload. A normal `EvidenceStore(path)` instance can therefore reload without authoritative verification. This is a production integrity bypass.

4. **Production tests do not exercise the mandatory authority path.** `test_store_append_and_reload()` constructs `EvidenceStore(tmp_path / "evidence_bundles.jsonl")` without a RawStore path, so the passing reload test does not prove the frozen P14-B authority requirement. The suite also lacks a regression proving that a same-lineage post-as-of record is excluded from candidate_trace.

### Required narrow repair — P14-E Production Implementation REPAIR-001

Repair only the four blockers above:

- Make candidate_trace derive strictly from the P14-D resolved/admissible state for the bundle's own as_of. Post-as-of records must never enter candidate_trace or influence selection/rejection labels.
- Keep P14-D as the sole authority for PIT visibility and version selection. P14-E may only mechanically label decisions already represented by P14-D resolved state; it must not infer selection from the complete raw lineage.
- Make P14-B authoritative RawStore verification mandatory for `EvidenceStore.reload()`; no optional bypass.
- Add production regression tests for post-as-of higher revision in the same lineage, mandatory RawStore authority verification on reload, authority mismatch / missing RawStore failure, and preservation of the existing FOUR-CLASS taxonomy and deterministic bundle behavior.
- Re-run full pytest, P13-M regression, P14-C/D/E audits, and exact-head GitHub Actions on the final repair HEAD.
- Do not modify P14-E Contract semantics, P14-D, P14-C, P13-T/U, data, factors, calibration, policy, recommendation, portfolio, trading, or P14-F.

**Gate remains:**
- P14-E Production Implementation: **FAIL / REPAIR REQUIRED**
- P14-F: **NOT AUTHORIZED**
- P13-T: **STOPPED / NOT EXECUTED**
- P13-U: **PROTECTED**

## P14-E Production Implementation REPAIR-001 — Independent Acceptance — 2026-10-03

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-F.**

Independently inspected the actual `main` HEAD `cc9f1e3f4f7ecdaa1c3bc1a6b0740763a78ad8fe`.

### Verified positive

- Actual `main` HEAD is `cc9f1e3f4f7ecdaa1c3bc1a6b0740763a78ad8fe`.
- Exact-head GitHub Actions workflow run `37130931030` is completed / success, with `head_sha` exactly equal to the actual `main` HEAD.
- Pytest job `111225717061` succeeded and explicitly ran P14-C audit, P14-D audit, P14-E audit, P13-M pooled regression, and the full pytest suite.
- Full pytest reported **580 passed / 2 warnings / 0 failed**.
- P13-M pooled regression job `111225716868` succeeded.
- REPAIR-001 adds real regressions for post-as-of candidate-trace exclusion, future revision not changing selection labels, no P14-D PIT/selection entry-point execution, mandatory P14-B authority on reload, missing/mismatched authority failure, and deterministic behavior.
- `EvidenceStore` now requires a P14-B raw authority path and reload performs authoritative reverse-trace verification.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.
- No factor, alpha, calibration, policy, recommendation, portfolio, trading, or P14-F promotion was introduced.

### Blocking finding

**P14-D version-selection semantics are still re-derived inside P14-E.**

The repaired `evidence.py` no longer calls P14-D entry points and no longer leaks post-as-of records into `candidate_trace`; those parts are correct.

However, `create_bundle()` still constructs `cands` by scanning the authoritative lineage and then `_selection_reason()` / `_rejection_reason()` independently compare `revision`, `available_time`, and canonical JSON to derive the winner/loser semantics. This remains a second implementation of P14-D's version-selection semantics.

The accepted architecture requires P14-D to remain the sole PIT/version-selection authority and P14-E to consume the already-resolved P14-D state, then mechanically package/label that resolved state. Merely removing direct `run_query()` / `select_lineage()` calls is not sufficient if P14-E reconstructs the selection decision from the raw lineage.

This is therefore an **architecture/authority violation**, not a test-count problem.

### Governance finding

`PROJECT_STATUS.md` in the actual HEAD `cc9f1e3f4f7ecdaa1c3bc1a6b0740763a78ad8fe` still reports `e546e3f5ca8c89fddb3f9e256ab08aa6c683a771` as Current Commit. The current status file is therefore stale relative to actual `main` HEAD.

The exact-head CI itself is valid, because run `37130931030` checks out the actual `main` push SHA `cc9f1e3f4f7ecdaa1c3bc1a6b0740763a78ad8fe`.

### Required narrow repair — P14-E Production Implementation REPAIR-002

Repair only:

1. Make P14-E consume P14-D's resolved selection/rejection state without reconstructing version-selection semantics from the complete authoritative lineage.
2. Preserve PIT-safe candidate_trace: post-as-of records must remain excluded.
3. Preserve mandatory P14-B RawStore verification on reload.
4. Preserve the existing FOUR-CLASS taxonomy and deterministic bundle behavior.
5. Synchronize `PROJECT_STATUS.md` Current Commit to the actual final repair HEAD.
6. Run GitHub Actions on the final target HEAD and independently verify exact checkout SHA, P14-C/D/E audits, P13-M regression, and full pytest.

Do not modify:
- P14-E Contract / Matrix / Golden / accepted Design semantics;
- P14-D implementation or authority;
- P14-C;
- P13-T / P13-U;
- data;
- factors / alpha;
- calibration;
- policy;
- recommendation / portfolio / trading;
- P14-F.

**Current gate:**
- P14-E Production Implementation: **FAIL / REPAIR REQUIRED**
- P14-F: **NOT AUTHORIZED**
- P13-T: **STOPPED / NOT EXECUTED**
- P13-U: **PROTECTED**

## P14-E Production Implementation REPAIR-002 — Independent Acceptance — 2026-10-04

**Decision: FAIL / REPAIR REQUIRED. Do not advance to P14-F.**

Independently inspected the actual `main` HEAD `01cbed837802d977654d6ed9c03de547e74c3e4e`.

### Verified positive

- REPAIR-002 successfully removes the prior P14-E lineage-wide version-selection/rejection re-derivation. `src/astock_v2/information/evidence.py` now requires a resolved `selection` state and consumes `selection_reason` / `rejection_reason` verbatim.
- Candidate trace is now projected from the resolved rejected state rather than reconstructed from the full authoritative lineage; PIT-excluded/post-as-of records therefore do not enter candidate_trace.
- Mandatory P14-B RawStore authority verification remains present in `EvidenceStore.reload()`.
- REPAIR-002 adds meaningful regression coverage for resolved-state consumption, under-resolved results, uncovered selected records, authority anchoring, and verbatim label consumption.
- Exact-head GitHub Actions run `37133719147` is completed / success and its `head_sha` exactly equals `01cbed837802d977654d6ed9c03de547e74c3e4e`.
- Pytest job `111233819992` and P13-M job `111233820204` both succeeded. P14-C, P14-D, P14-E audits and P13-M regression all completed successfully.
- Full pytest: **582 passed / 2 warnings / 0 failed**.
- P13-T remains STOPPED / NOT EXECUTED and P13-U remains PROTECTED.

### Blocking findings

1. **REPAIR-002 modified the frozen P14-D implementation/contract despite the repair task explicitly forbidding that scope.**

The REPAIR-002 commit `5dbc9c453df7d51c636a1cd07994c4ac85eb3ac0` changes:
- `src/astock_v2/information/pit.py`
- `src/astock_v2/information/research_query.py`
- `docs/contracts/P14-D-DESIGN-CONTRACT.md`
- P14-D harness tests

The change adds a new top-level `selection` state to P14-D results and introduces `resolve_selection()` in the P14-A/P14-D information path. Although the resulting architecture is conceptually sound and preserves the existing selection semantics, it is still a modification of an independently accepted/frozen P14-D surface. The REPAIR-002 task explicitly required: **“Do not modify P14-D implementation or authority.”**

This is therefore a **governance/scope violation**, not a test failure.

2. **PROJECT_STATUS was not synchronized to the actual final HEAD.**

Actual `main` is `01cbed837802d977654d6ed9c03de547e74c3e4e`, while the submitted status before this acceptance still identified `5dbc9c453df7d51c636a1cd07994c4ac85eb3ac0` as Current Commit. The exact-head CI evidence is valid, but the project status itself was stale.

### Required narrow repair — P14-E Production Implementation REPAIR-003

Repair only:

1. Resolve the authority/scope issue without weakening the frozen P14-D boundary. Preferred approach: expose the already-required resolved selection/rejection state through an explicitly authorized P14-E/P14-D integration surface **only if that surface is first separately authorized and frozen**; otherwise redesign the P14-E handoff so it consumes existing accepted P14-D state without modifying P14-D.
2. Do not change the frozen P14-D implementation, contract, or authority in the repair unless an explicit new P14-D authorization is issued first.
3. Preserve the successful REPAIR-002 properties: no P14-E lineage re-selection, PIT-safe candidate_trace, mandatory P14-B RawStore verification, FOUR-CLASS taxonomy, deterministic behavior, and the new regression coverage.
4. Synchronize `PROJECT_STATUS.md` Current Commit to the actual final HEAD.
5. Run exact-head GitHub Actions and independently verify checkout SHA, P14-C/D/E audits, P13-M regression, and full pytest.

### Forbidden scope

- P14-E Contract / Matrix / Golden / accepted Design semantics
- un-authorized changes to P14-D implementation, contract, or authority
- P14-C
- P13-T / P13-U
- data
- factors / alpha
- calibration
- policy
- recommendation / portfolio / trading
- P14-F

**Current gate:**
- **P14-E Production Implementation: FAIL / REPAIR REQUIRED**
- **P14-F: NOT AUTHORIZED**
- **P13-T: STOPPED / NOT EXECUTED**
- **P13-U: PROTECTED**

## P14-E Production Implementation REPAIR-003 — 2026-10-04

Submitted in response to the REPAIR-002 independent acceptance
(FAIL / REPAIR REQUIRED, record `3b8f8aebc9526bc55065da012023d748230351f2`).

**Blocking #1 (governance/scope) — RESOLVED.** REPAIR-002 (`5dbc9c4`) had
modified frozen P14-D surfaces (pit.py, research_query.py, P14-D design
contract, P14-D harness) despite the task's explicit do-not-modify
scope. REPAIR-003 restores all seven affected files byte-identically to
the reviewed `cc9f1e3` state (verified: `git diff cc9f1e3` over
`src/astock_v2/information/` and `tests/` is empty). Revert commit:
`9de24f1`. No P14-D/P14-A implementation, contract, or authority is
changed relative to its accepted state.

**Blocking #2 (status sync) — ADDRESSED.** Current Commit now records
the newest content commit at authoring time; the convention is stated
in the Current Commit section. The acceptance record remains the
authoritative setter of the actual final HEAD.

**Architecture path per the verdict's preferred approach.** The
resolved selection/rejection state is exposed to P14-E through an
integration surface that is FIRST separately authorized and frozen:
`docs/contracts/P14-E-P14D-SELECTION-STATE-INTEGRATION-CONTRACT.md`
(STATUS: DRAFT — AWAITING INDEPENDENT ACCEPTANCE, commit `4b326b4`).
It is NOT implemented. The REPAIR-002 consumption architecture
(verified positive as "conceptually sound") is restored only after
that contract is accepted; if the contract is rejected, the P14-E
handoff remains at the REPAIR-001 accepted form and the architecture
repair is redesigned.

**Gate:**
- P14-E Production Implementation: ~~REPAIR-003 IMPLEMENTED / AWAITING INDEPENDENT ACCEPTANCE~~ — **SUPERSEDED by the BLOCKED record below**
- P14-E/P14-D integration surface: DRAFT / NOT AUTHORIZED / NOT IMPLEMENTED
- P14-F: NOT AUTHORIZED
- P13-T: STOPPED / NOT EXECUTED
- P13-U: PROTECTED

## P14-E Production Implementation REPAIR-003 — BLOCKED Record — 2026-10-04

**Verdict: REPAIR-003 BLOCKED.** The mandated feasibility checks (priority 1:
consume an existing resolved state; priority 2: a P14-E-local adapter) were
executed against the reverted, independently accepted architecture and both
are infeasible without modifying frozen P14-D surfaces.

```text
REPAIR-003 BLOCKED

Reason:
The accepted P14-D surface does not expose the resolved
selection/rejection state required by P14-E without modifying
the frozen P14-D authority.

No P14-D modification was made.
```

### Feasibility check 1 — direct consumption of the existing accepted state (NOT POSSIBLE)

The frozen P14-D output (`run_query`, verified at the reverted state) is
`{query, records, excluded, counts, result_id}` where `records` carries the
**selected winners only** (P14-A provenance projection) and `excluded`
carries the PIT/scope exclusions. It contains **no** `selection_reason`, no
`rejection_reason`, and no visible-loser records. `pit.py` exposes only
`is_admissible` / `admissible_records` / `visible_revisions` (winners map) —
no label vocabulary. A repo-wide scan confirms the frozen label vocabulary
(`SELECTED_*` / `REJECTED_*`) exists only in (a) `evidence.py`'s own
derivation — the lineage re-derivation the REPAIR-002 verdict removed and
condemned — and (b) the Golden engine `tests/contracts/p14e/golden/core.py`,
which is the test-scope semantic acceptance authority (P14E-P-023), is
barred from the runtime module set (P14E-P-001), and derives labels from its
own records — it is not a P14-D state source. **The accepted P14-E contract
(P14E-P-007, frozen) requires verbatim labels on every evidence and every
candidate-trace entry; the accepted P14-D surface does not emit them.**

### Feasibility check 2 — P14-E-local adapter/handoff (NOT POSSIBLE without violating frozen authority)

A label is a pure function of (visible lineage candidates, resolved winner)
under the frozen comparisons (revision, available_time, canonical_json).
Any P14-E-side producer must either re-apply those comparisons — exactly the
"second implementation of P14-D version-selection semantics" the REPAIR-002
verdict removed — or re-execute PIT/version-selection authority calls inside
P14-E, which the REPAIR-003 task and the verdict's preserved property
("no P14-E lineage re-selection") both forbid. REPAIR-002's own design kept
a single selection-semantics source precisely by placing the classification
NEXT TO the rule (`pit.resolve_selection`) and emitting the state from
`run_query`; relocating that logic into P14-E recreates the condemned
defect, and a new runtime file would violate the frozen module layout
(P14E-P-001). The mandated verbatim-consumption proof (Test B: flipping the
resolved label flips the bundle) is satisfiable only when labels are DATA in
the resolved state; a recomputing adapter contradicts it by construction.

### REPAIR-002 (`5dbc9c4`) change classification (mandated by the repair task)

- **P14-E legitimate repair** (independently reviewed as verified positive,
  "conceptually sound and preserves the existing selection semantics"):
  `evidence.py` rewritten as a pure consumer — lineage-walk /
  complement-inference / label-derivation machinery deleted;
  `selection_reason` by identity-key lookup from the resolved state;
  `candidate_trace` a verbatim field projection of `selection.rejected`;
  `authority_violation` for unlabeled/under-resolved results;
  `identity_failure` for records absent from the P14-B authority; plus the
  P14-E regression coverage.
- **P14-D unauthorized modification** (the governance violation):
  `pit.py` (+6 label constants + `resolve_selection()`),
  `research_query.py` (top-level `selection` emission; `result_id`
  coverage), P14-D design contract §9 (v1.2), P14-D harness
  (key-set assertion + `test_p14d_011`).

The legitimate half is not operational without the unauthorized half:
restoring only the P14-E consumer would sever the real pipeline (every real
`run_query` result lacks `selection`, so `create_bundle` would fail-fast
`authority_violation` unconditionally); restoring both re-commits the
governance violation. Neither is authorized — hence this record, not an
implementation.

### Retained state (preservation audit per the repair task)

- Runtime remains at the REPAIR-001 form (`e546e3f`) — itself under the
  `286f3a9` FAIL verdict for in-P14-E label re-derivation, which is exactly
  the defect only the authorized integration surface can remove — plus the
  test-only Test E adversarial completion (`9b7bf34`). The verified-positive
  REPAIR-001 properties (PIT-safe candidate_trace, mandatory P14-B reload
  authority) are intact.
- PIT safety: post-as-of records are carried as P14-D exclusions and never
  enter `candidate_trace` nor receive `REJECTED_*`
  (`test_candidate_trace_pit_safe_no_post_as_of_leak`,
  `test_selection_reason_not_mislabeled_by_future_revision`).
- P14-B authority: `EvidenceStore.reload()` mandatory RawStore verification
  (missing store / missing ingestion_id / payload-hash mismatch /
  adversarial hash-mismatched authority row via `9b7bf34`); no
  `EvidenceStore(path)` bypass (`test_store_requires_raw_authority_path`).
- FOUR-CLASS reverse-trace taxonomy unchanged; deterministic behavior
  unchanged.
- Not retained (the blocked deliverable): verbatim consumption of
  authority-emitted selection/rejection labels and the literal Test B.
  The existing monkeypatch/static-scan tests
  (`test_create_bundle_never_executes_pit_or_selection`,
  `test_evidence_source_has_no_pit_or_selection_calls`,
  `test_p14e_does_not_rerun_p14d_selection`) lock that P14-E re-executes no
  PIT/selection functions, but the label-restatement comparisons remain in
  P14-E (the `286f3a9` architecture/authority violation) until the
  authorized integration surface replaces them with verbatim consumption.

### Verification evidence (working tree `9b7bf34`, 2026-10-04)

- `python -m pytest -q -ra` → **581 passed / 2 warnings / 0 failed**.
- P13-M regression `tests/test_industry_relative.py` → **3 passed**.
- `audit_p14c_contract.py` → PASS, 0 hard + 0 soft (61/61/61 closure).
- `audit_p14d_contract.py` → PASS (10 contract / 10 matrix / 11 golden /
  11 harness).
- `audit_p14e_contract.py` → PASS (17/17 contract-matrix closure, 26/26
  golden checks, `p13_t: STOPPED`, `p13_u: PROTECTED`, production
  implementation files authorized set unchanged).
- Revert integrity: `git diff cc9f1e3..HEAD` over the seven governance
  files is empty except the test-only `9b7bf34` addition (+22 lines in
  `tests/test_p14e_production_impl.py`).

### Standing authorization request (unchanged, not implemented)

`docs/contracts/P14-E-P14D-SELECTION-STATE-INTEGRATION-CONTRACT.md`
(DRAFT, `4b326b4`) remains the pending preferred-approach authorization
request; its §1 documents the same three-way constraint conclusion
independently re-verified here. Upon explicit authorization and independent
acceptance of that contract, the verified-positive REPAIR-002 P14-E
consumption implementation (`5dbc9c4` P14-E side) is restored verbatim per
that contract's §4/§6. Until then the P14-E handoff remains at the
REPAIR-001 form, under the `286f3a9` architecture FAIL verdict.

**Gate:**
- **P14-E Production Implementation: REPAIR-003 BLOCKED** (pending P14-D integration-surface authorization; underlying implementation verdict FAIL / REPAIR REQUIRED per `286f3a9` architecture finding) — **RESOLVED 2026-10-04: the integration surface was independently accepted and Human-Authorized; implementation delivered — see the Integration Contract v2 Implementation section below**
- P14-E/P14-D integration surface: DRAFT / NOT AUTHORIZED / NOT IMPLEMENTED
- P14-F: NOT AUTHORIZED
- P13-T: STOPPED / NOT EXECUTED
- P13-U: PROTECTED

## P14-D → P14-E Integration Contract v2 — Implementation — 2026-10-04

**Authorization chain.** REPAIR-003 BLOCKED (independently confirmed) →
Integration Contract amended to independent-acceptance readiness
(`51a769f`) → Contract **PASS / INDEPENDENTLY ACCEPTED** (acceptance
record commit `006780705fd93579b89141109de7353593608711`) → **Human
Authorization GRANTED** (record commit
`3ec2b86d2deb52c439f6e861576162e17916ea13`) → this implementation.
Per the contract's four-stage separation: **Implementation Complete ≠
Independent Acceptance**.

**Implemented content = contract §2+§3+§4 exact delta** — the
independently reviewed REPAIR-002 change set (`5dbc9c4`) restored
verbatim, with the two contract-specified deviations:

- P14-D integration surface: `pit.py` (+6 frozen label constants next
  to the rule + `resolve_selection()` classifying the already-resolved
  mapping; existing functions byte-identical); `research_query.py`
  (top-level `selection` emission — {selected, rejected} full
  provenance projection + label in frozen deterministic order;
  result_id covers the state; records/excluded/counts semantics and
  sort keys unchanged; PIT-excluded records stay in `excluded`);
  `__init__.py` (export-only re-export); P14-D design contract v1.2
  (§9 additive `selection` documentation; v1.2 authorization-basis
  line cites Integration Contract v2 per its §6); P14-D harness
  (top-level key-set assertion extension + `test_p14d_011`).
- P14-E restoration surface: `evidence.py` pure consumer —
  `_selection_reason` / `_rejection_reason` / `_visible_candidates` /
  `_check_candidate_consistent` deleted; `selection_reason` consumed
  verbatim from the resolved state by identity-key lookup;
  `candidate_trace` = order-preserving verbatim field projection of
  `selection.rejected`; `authority_violation` (missing/unresolved/
  uncovered resolved state) and `identity_failure` (records absent
  from the P14-B authority) gates intact; label vocabulary re-exported
  from the authority, never classified; reverse-trace FOUR-CLASS and
  mandatory `EvidenceStore` RawStore verification unchanged;
  `tests/test_p14e_production_impl.py` verbatim suite plus the
  REPAIR-003 Test E adversarial regression retained (no regression
  deleted).

**Scope gate.** The implementation commit (`69cfe2a`, rebased onto the
acceptance/authorization records) touches exactly the 7
contract-authorized files (+318/−181). No P14-B / P14-C / P13-T /
P13-U / P14-F / production-domain file was touched.

**Verification.** Full pytest **583 passed / 2 warnings / 0 failed**
(double run identical, 583/583); P14-C audit exit 0 (61/61/61); P14-D
audit exit 0; P14-E audit exit 0 (17/17 contract-matrix closure, 26/26
golden checks); P13-M regression 3 passed. Mandated coverage verified
present: verbatim consumption
(`test_bundle_consumes_p14d_resolved_labels_verbatim`),
no-second-selection-authority (monkeypatch
`test_create_bundle_never_executes_pit_or_selection` + static scan
`test_evidence_source_has_no_pit_or_selection_calls`), PIT safety
(`test_candidate_trace_pit_safe_no_post_as_of_leak`,
`test_selection_reason_not_mislabeled_by_future_revision`),
RawStore authority four failure modes (missing store / missing
ingestion_id / hash mismatch / adversarial hash-mismatched row), and
determinism (double run + `test_bundle_determinism` +
`test_p14d_006_deterministic_result`).

**Contract STATUS lifecycle sync (docs-only, minimal repair).** Per the
acceptance authority's minimal-repair instruction, the contract file
`docs/contracts/P14-E-P14D-SELECTION-STATE-INTEGRATION-CONTRACT.md`
now records **STATUS: ACCEPTED — INDEPENDENTLY ACCEPTED** (Contract
Acceptance `0067807`) with the four-stage lifecycle recorded in its
header: Contract Acceptance (`0067807`) → Human Authorization GRANTED
(`3ec2b86`) → Implementation DELIVERED (`69cfe2a`) → Independent
Acceptance of the implementation **PENDING**. §1-§5 semantics
unchanged; the `0067807` / `3ec2b86` / `69cfe2a` records are
referenced as-is and were not altered.

**Gate:**
- P14-D → P14-E Integration: **IMPLEMENTATION COMPLETE — PENDING INDEPENDENT ACCEPTANCE** (this record is not an acceptance decision)
- P14-F: NOT AUTHORIZED
- P13-T: STOPPED / NOT EXECUTED
- P13-U: PROTECTED

## P14-E Production Implementation — Independent Acceptance — 2026-10-04

**Decision: PASS / INDEPENDENTLY ACCEPTED** (implementation acceptance; the integration
CONTRACT acceptance was separately recorded at `0067807`).

Accepted by the **project owner** (acceptance authority). The decision was communicated by the
owner on 2026-10-04 (via the roadmap-audit task statement: "P14-E INDEPENDENTLY ACCEPTED") and is
recorded in-repo by ZCODE on the owner's explicit instruction — ZCODE is not the acceptance
authority and did not make this decision.

- Accepted implementation: `69cfe2a86d23352e9f74cf7454aad6cf59135e7b` (exactly the 7
  contract-authorized files, +318/−181; REPAIR-002 verified delta restored verbatim; Test E
  regression retained).
- Exact-head CI evidence: run `37189305728` (HEAD `d100d0197744671a83de03af1cc2580ae85e4bd9`)
  and run `37190466113` (HEAD `4ff243c66b1906a4b0a8ddbfc082413b9b9f893f`), both completed /
  success, all steps green (P14-C/D/E audits, P13-M regression, Full pytest suite).
- Repository verification at audit HEAD `c8fdb48`: full pytest 583 passed / 2 warnings /
  0 failed (double run identical); audits exit 0; no integrity problem found by the roadmap
  audit (`docs/ROADMAP_AUDIT_2026-10-04.md`).
- Gate after this record: **P14-E Production Implementation: PASS / INDEPENDENTLY ACCEPTED**;
  next authorized work: **R3-A — Local Historical Store → P14-B real source adapter**, reusing
  the accepted P14-B/C/D/E authority chain with **no semantic change**; P14-F remains
  NOT AUTHORIZED; P13-T remains STOPPED / NOT EXECUTED; P13-U remains PROTECTED.
