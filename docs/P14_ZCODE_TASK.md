# P14 ZCODE Task — Multi-Market Information Infrastructure

## 0. Task positioning

Repository: `CGchenggang/a-stock-quantimental`

Current accepted state:
- P13-M PASS
- P13-N PASS
- P13-O PASS
- P13-P PASS
- P13-Q PASS
- P13-R PASS
- P13-S PASS
- P13-T STOPPED / NOT EXECUTED because no evaluable virgin holdout existed
- P13-U PASS as the virgin-holdout integrity/accumulation gate

Your task is **P14 — Multi-Market Information Infrastructure**.

P14 is research/infrastructure work only. It is NOT a new-alpha search, not production-factor promotion, not policy tuning, not calibration tuning, and not execution/trading.

The protected P13-T virgin zone is:
- research_end = 2026-09-22
- virgin_start = 2026-09-23
- minimum P13-T holdout condition = 20 trading days
- recommended condition = 60 trading days

P13-U's research-zone guard must remain intact.

## 1. First step — inspect before changing anything

Before implementation, independently inspect:
1. docs/PROJECT_STATUS.md
2. docs/P13T_RESEARCH_PLAN.md
3. docs/P13U_RESEARCH_PLAN.md
4. docs/P13U_PIT_AUDIT.md
5. docs/P13U_ACCEPTANCE.md
6. src/astock_v2/data/**
7. existing PIT/freshness/provider/legacy adapter code
8. tests covering PIT, freshness, providers, adapters, P13-Q/P13-R/P13-U
9. .github/workflows/tests.yml

Do not assume a new abstraction is necessary if existing infrastructure can be safely extended.

## 2. Core objective

Build an auditable information infrastructure that can ingest and normalize heterogeneous research information while preserving:

raw source
→ provenance
→ event_time
→ available_time
→ revision/version
→ normalization
→ deduplication/conflict handling
→ PIT-safe query
→ freshness state
→ research-ready information record

The infrastructure should be suitable for future A-share research involving:
- company announcements
- company/financial information
- macroeconomic information
- overseas market information
- market-state information
- other externally sourced research information

Do not yet turn these into predictive factors.

## 3. Mandatory temporal semantics

Every research information record must distinguish at minimum:

- source_id
- source_type
- source_uri or stable source reference when available
- symbol/entity scope
- event_time
- available_time
- retrieved_time if useful
- revision/version identity
- content/value payload
- provenance metadata
- normalization status
- freshness metadata

Rules:
1. event_time is when the underlying event/information is about.
2. available_time is when the information could legitimately have been known by the research system.
3. retrieved_time must never be substituted for available_time.
4. A later revision cannot retroactively overwrite an earlier PIT state.
5. Research queries at decision_time D may use only information with available_time <= D.
6. Equal-boundary semantics must be explicitly tested.
7. Missing available_time must never silently become decision_time.
8. Unknown temporal provenance must be represented explicitly and conservatively excluded from PIT-sensitive research unless an explicit policy allows it.

## 4. Provenance

Implement an explicit provenance model.

At minimum preserve:
- source identity
- source type/category
- source reference
- retrieval timestamp if applicable
- upstream revision/version
- parser/normalizer version
- ingestion batch/run identifier if applicable
- original/raw record hash
- normalized record hash

The same source record ingested twice must be deduplicated deterministically.

Different revisions of the same logical event must remain distinguishable.

## 5. Revision and late-arrival handling

Implement and test:
- late-arriving information
- revised information
- multiple revisions of one event
- out-of-order ingestion
- duplicate ingestion
- conflicting records from different sources

Do not solve conflicts by silently choosing the latest retrieved record.

Define deterministic rules and document them.

For PIT queries:
- a revision is usable only from its own valid available_time;
- earlier decision dates must remain unchanged after later revisions arrive.

## 6. Normalization

Create a deterministic normalization layer for research information.

It should:
- canonicalize timestamps
- canonicalize symbols/entity identifiers where possible
- normalize source metadata
- normalize field names/types
- preserve original raw values where necessary
- generate stable record identifiers/hashes

Normalization must be deterministic:
same raw input + same normalization version = byte-identical normalized output.

## 7. Deduplication

Define a stable deduplication key.

It must distinguish:
- exact duplicate records
- same event with different revisions
- same event from different sources
- materially conflicting records

Do not deduplicate different revisions into one irreversible record.

Add tests for repeated ingestion and reordered ingestion.

## 8. Conflict handling

Define explicit conflict states, for example:
- resolved_by_precedence
- unresolved_conflict
- duplicate
- superseded_revision
- invalid

Do not silently discard conflicting evidence.

Every resolution must be auditable.

## 9. Freshness

Build a reusable freshness evaluation layer.

It should distinguish:
- fresh
- stale
- unknown

Freshness must be based on explicit available_time / reference decision_time semantics, not file modification time.

Do not let freshness logic change PIT eligibility.

## 10. PIT query interface

Provide a simple, deterministic interface for queries such as:

get_information(entity, decision_time)

The returned set must satisfy:
available_time <= decision_time

and must apply revision/deduplication rules consistently.

Add a test that appends future records and proves all historical PIT query results remain byte-identical.

## 11. P13-T virgin holdout protection

This is mandatory.

P14 must not consume:
- decision dates >= 2026-09-23
- P13-T virgin prices
- future holdout-derived labels
- future holdout-derived factors
- future holdout-derived policy/calibration information

P13-U's `assert_research_zone` guard must remain active at all existing research entry points.

If P14 needs to test temporal infrastructure, use synthetic fixtures or data at/before the consumed research boundary.

Do NOT weaken, bypass, relocate, or reinterpret the guard.

Do not create a fake "P14 exception" that permits production research code to consume the virgin zone.

## 12. No alpha/policy/calibration work

Explicitly forbidden:
- new predictive factors
- factor weight tuning
- model tuning
- calibration tuning
- policy threshold tuning
- recommendation optimization
- holdout evaluation
- changing P13-Q registry
- changing P13-R registry
- promoting volatility or any other research candidate
- using the virgin zone to select parameters

P14 output is infrastructure, not a new investment conclusion.

## 13. Suggested architecture

Prefer a small, composable architecture such as:

raw source
  ↓
raw record store
  ↓
provenance
  ↓
normalizer
  ↓
revision/version resolver
  ↓
deduplicator/conflict resolver
  ↓
PIT information store/query
  ↓
freshness evaluator
  ↓
research-information interface

Reuse existing project PIT/freshness abstractions where appropriate.

Do not duplicate incompatible PIT implementations.

## 14. Initial source adapters

Do not attempt to build every real-world source.

Implement a minimal, deterministic adapter framework with synthetic/local fixtures that proves the semantics.

If existing project data providers can be safely adapted, reuse them.

A real external source may be added only if:
- provenance is explicit;
- available_time semantics are documented;
- the source is reproducible enough for tests;
- no online dependency is required for CI.

CI must remain offline-capable.

## 15. Tests

Add focused tests covering at least:

1. event_time vs available_time
2. available_time boundary equality
3. future record exclusion
4. late arrival
5. revision ordering
6. historical PIT immutability after later revision
7. duplicate ingestion
8. reordered ingestion
9. cross-source conflict
10. deterministic conflict resolution
11. unknown provenance handling
12. freshness states
13. normalization determinism
14. stable hashes/IDs
15. future-row immunity
16. virgin holdout guard
17. P13-Q guard regression
18. P13-R guard regression
19. no policy/calibration registry mutation
20. no factor registry mutation
21. byte-identical repeated run
22. malformed/missing timestamps
23. malformed provenance
24. unknown entity/symbol
25. empty input

Also preserve all existing tests.

## 16. Research artifacts

Use a dedicated research-only area, for example:

data/industry/p14/

Do not commit large generated market datasets unless the repository already has a deliberate policy for doing so.

Recommended deterministic artifacts:
- analysis_config.json
- normalized_fixture.json
- provenance_fixture.json
- conflict_results.json
- pit_query_results.json
- freshness_results.json
- manifest.json

Generated artifacts must contain no dynamic UUID/timestamp fields unless explicitly part of the tested semantics.

Record SHA256 hashes where useful.

## 17. Documentation

Create:
- docs/P14_RESEARCH_PLAN.md
- docs/P14_PIT_AUDIT.md
- docs/P14_ACCEPTANCE.md

The acceptance report must describe what was actually implemented and tested. It must not claim production readiness or alpha validation.

## 18. Production boundary

Before finishing, compare against the P13-R production baseline.

Preferred result:

git diff 77594d9a5b4f142865f6a17885a846b2b13c6e8b..HEAD -- src/astock_v2

should contain no P14 factor/model/policy/calibration changes.

If generic infrastructure changes under src/astock_v2 are necessary, document every one and prove that:
- existing semantics are preserved;
- P13-M through P13-U tests remain green;
- no production recommendation behavior is changed.

## 19. CI requirements

GitHub Actions must continue to run:
- full pytest: python -m pytest -q -ra
- P13-M regression
- all P13-U tests
- all new P14 tests

Inspect actual workflow jobs and steps.

Do not merely report that CI is green.

## 20. Determinism

Run important P14 analysis/fixture generation twice.

Require byte-identical outputs after excluding explicitly documented non-deterministic metadata.

Test input-order invariance where semantics require it.

## 21. Acceptance standard

ZCODE's task is complete only when:
- implementation is complete;
- temporal semantics are explicit;
- provenance is explicit;
- revision/late-arrival behavior is explicit;
- normalization/deduplication/conflict handling is deterministic;
- PIT queries are tested;
- freshness is tested;
- future-row immunity passes;
- P13-U virgin holdout protection remains intact;
- no alpha/model/policy/calibration promotion occurs;
- production diff is reviewed;
- full pytest passes;
- P13-M regression passes;
- P13-U tests pass;
- P14 tests pass;
- CI workflow jobs/steps are green;
- docs/P14_ACCEPTANCE.md accurately reflects reality.

## 22. Stop conditions

STOP and report instead of guessing if:
- available_time semantics cannot be established;
- a source's revision semantics are unknowable;
- a conflict cannot be deterministically resolved;
- P14 implementation would require consuming virgin holdout data;
- a production behavior change becomes necessary;
- existing PIT semantics conflict with the proposed design.

Do not weaken a safety boundary to make tests pass.

## 23. Final handoff

At completion, report:
1. commits
2. files changed
3. architecture
4. temporal/PIT semantics
5. provenance/revision/conflict rules
6. tests added
7. full pytest result
8. P13-M result
9. P13-U result
10. CI run ID and actual job/step results
11. production diff
12. deterministic artifact hashes
13. known limitations
14. explicit statement that P13-T virgin holdout remains protected

Do not declare P14 independently accepted. The external acceptance step will do that.
