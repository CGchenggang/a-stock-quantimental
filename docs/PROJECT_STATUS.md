# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P14 — Multi-Market Information Infrastructure**

P13-U has been independently accepted as PASS. P13-T remains a future data-condition gate and is **STOPPED / NOT EXECUTED** until a genuine virgin temporal holdout reaches the frozen execution threshold.

Current P13-U gate state at the last verified data run: **ACCUMULATING**.

- `research_end = 2026-09-22`
- `virgin_start = 2026-09-23`
- virgin trading days observed: **2** (2026-09-23, 2026-09-24)
- P13-T minimum execution condition: **20 trading days**
- P13-T recommended execution condition: **60 trading days**
- contamination detected: **False**

P14 is infrastructure/research-only work. It must not consume the protected virgin zone or promote new information into production factors, policy, or calibration.

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
| P14 | READY TO START | Multi-market information infrastructure; research-only, no alpha promotion |

**Important:** P13-U PASS does not mean P13-T PASS. P13-T remains pending until the frozen virgin zone reaches an executable holdout condition without contamination.

## Current Commit

`967f52da5682d6e2b46f2fe73d8403d6c8a38588`

Latest commit message: `docs: add long-lived project status and handoff state`.

Current HEAD was independently checked on 2026-09-29.

Relevant current-head CI:
- workflow: `tests`
- run: `36594103957`
- HEAD: `967f52da5682d6e2b46f2fe73d8403d6c8a38588`
- pytest job: success
- p13m job: success
- Full pytest: **261 passed / 2 warnings / 0 failed**
- Full pytest step executed `python -m pytest -q -ra`
- P13-M regression step: success
- P13-U dedicated tests are included in the 261-test suite; the workflow log enumerates all 18 P13-U tests.

The earlier P13-U guard-wiring CI run `36591228302` on `96a2aae` was also independently inspected. The subsequent docs-only HEAD `967f52d` has its own successful CI run `36594103957`, so CI evidence is current rather than inherited from an older commit.

## Current Research Boundary

### Consumed research zone

Last consumed decision date:

`2026-09-22`

P13-O/P13-Q/P13-R research consumed the OOS history through this date.

### Frozen virgin zone

`2026-09-23 onward`

No P13-Q/P13-R research pipeline may consume decision dates in this zone.

P13-U `assert_research_zone` is a fail-fast guard. Any decision date `>= 2026-09-23` entering the protected research entry points must raise an error.

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

**Reproducibility note:** `data/industry/` is intentionally ignored by `.gitignore`, so the generated P13-U gate JSON artifacts and the local historical price store are not part of the GitHub commit. Therefore the live 2026-09-24 data endpoint is documented from the independently inspected P13-T/P13-U evidence, while current-head CI independently verifies the gate implementation and its tests. This is a data-availability limitation, not a P13-U acceptance failure.

## Frozen Parameters

- `RESEARCH_END = 2026-09-22`
- `VIRGIN_START = 2026-09-23`
- `MINIMUM_TRADING_DAYS = 20`
- `RECOMMENDED_TRADING_DAYS = 60`
- 76-stock validation universe
- P13-Q calibration registry
- P13-R policy registry
- P13-R cost/risk assumptions
- P13-S report schema
- P13-T determination
- P13-O consumed-date audit boundary

P13-U records SHA256 hashes for the frozen inputs in `data/industry/p13u/frozen_manifest.json` when the local gate is run.

## Known Limitations

1. P13-T has not produced final holdout metrics because the virgin zone is still too short.
2. P13-U cannot prove arbitrary runtime reads that leave no auditable artifact; its contamination check covers the defined consumed-date set and known research artifacts.
3. Trading-day identification uses actual universe data rather than an external exchange calendar; missing coverage is therefore reported explicitly.
4. The virgin zone currently contains only two trading days, so no model/policy performance conclusion may be drawn from it.
5. P13-U is an integrity gate, not a prediction or recommendation stage.
6. P13-U does not automatically execute P13-T when the threshold is reached; independent acceptance is still required.
7. Research-only calibration/policy discoveries remain non-production until independently validated.
8. The local P13-U generated data artifacts are intentionally outside Git version control; acceptance must therefore distinguish source/CI verification from the latest local data-state evidence.

## Next Phase

**P14 — Multi-Market Information Infrastructure**

P14 should proceed independently of the still-accumulating P13-U virgin holdout.

P14 must:
- preserve the P13-U research-zone guard;
- avoid consuming or contaminating the virgin holdout;
- build an auditable information/data infrastructure for A-share, company, macro, overseas and market-state information;
- explicitly model `event_time` versus `available_time`;
- enforce PIT, freshness, provenance, revision and deduplication semantics;
- remain research-only;
- avoid adding unvalidated factors to production;
- avoid changing production weights, P13-R policy, or calibration;
- produce deterministic/reproducible outputs;
- add full pytest coverage and preserve P13-M regression plus P13-U integrity protection.

P13-T remains a parallel future gate: once the virgin zone reaches the agreed execution condition, stop new research consumption of that zone, freeze the manifest, and execute the pre-registered holdout evaluation.

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
- acceptance documentation.

ZCODE's acceptance report is evidence, not the final acceptance decision.

### P13-U

**Independent acceptance: PASS.**

Verified:
- frozen boundary is explicit and does not move with latest data;
- virgin dates are identified conservatively;
- contamination checks and research-zone guards are implemented;
- missing coverage is reported without silently changing the universe;
- no performance/recommendation metrics are produced;
- repeated-artifact determinism is tested;
- future-row immunity is tested;
- all 18 P13-U tests are included in the current 261-test suite and pass;
- current HEAD GitHub Actions run `36594103957` is green at `967f52d`;
- P13-M regression is green;
- production source diff from the P13-R baseline contains no `src/astock_v2` changes attributable to P13-U/P13-S handoff work.

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

### P14 acceptance

P14 may be accepted only after independent verification of:
1. raw → provenance → normalization → event/available time → PIT → freshness → deduplication → research information layer;
2. explicit source provenance and source identity;
3. late-arriving and revised information handling;
4. available-time boundary correctness;
5. future-row immunity;
6. deterministic normalization and repeated-run byte identity;
7. missing/duplicate/conflicting-source handling;
8. virgin holdout protection;
9. P13-U research-zone guard preservation;
10. no production factor/policy/calibration mutation;
11. production diff review;
12. full pytest, P13-M regression, P13-U integrity tests and all new P14 tests in GitHub Actions;
13. workflow job/step inspection;
14. acceptance documentation matching actual implementation.

## Operating Rule

When a new ZCODE stage is reported complete:

1. Inspect the GitHub diff and current HEAD.
2. Inspect the implementation and tests.
3. Inspect data/provenance/PIT boundaries.
4. Verify CI from workflow jobs/steps, not merely from a status claim.
5. Compare production-zone changes against the frozen baseline.
6. Decide PASS / FAIL / STOPPED independently.
7. Update this file in the same repository when the project state changes materially.
8. If PASS, issue the next ZCODE task prompt.
9. If STOPPED because a data condition is not met, build/maintain integrity infrastructure rather than fabricating evidence.

Last independently updated: 2026-09-29.
Independent acceptance recorded against HEAD: `967f52da5682d6e2b46f2fe73d8403d6c8a38588`.
