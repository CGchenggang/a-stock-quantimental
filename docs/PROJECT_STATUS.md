# Project Status — A-Stock Quantimental

> Long-lived project handoff / acceptance state. Update this file after every independently accepted stage or material boundary change.
> Repository: `CGchenggang/a-stock-quantimental`

## Current Phase

**P13-U — Virgin Holdout Data Accumulation & Integrity Gate**

P13-T was correctly stopped because no evaluable true virgin temporal holdout existed. P13-U now protects that virgin zone while new market data accumulates.

Current gate state at last verified run: **ACCUMULATING**.

- `research_end = 2026-09-22`
- `virgin_start = 2026-09-23`
- virgin trading days observed: **2** (2026-09-23, 2026-09-24)
- P13-T minimum execution condition: **20 trading days**
- P13-T recommended execution condition: **60 trading days**
- contamination detected: **False**

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
| P13-U | PASS | Virgin-holdout integrity gate; currently ACCUMULATING |

**Important:** P13-U PASS does not mean P13-T PASS. P13-T remains pending until the frozen virgin zone reaches an executable holdout condition without contamination.

## Current Commit

`38c4692a74bf88bcdc9c477605e63707d1b3a1f5`

Latest verified commit message: `docs: record P13-U CI verification facts`.

Relevant CI verification:
- workflow: `tests`
- run: `36591228302`
- commit containing the corrected P13-U guard wiring: `96a2aaeb65d7962ac4ad5c603f7df0f7f402cf1b`
- pytest job: success
- Full pytest suite: success
- P13-M regression: success
- p13m job: success
- reported full suite: **261 passed / 0 failed**

## Current Research Boundary

### Consumed research zone

Last consumed decision date:

`2026-09-22`

P13-O/P13-Q/P13-R research consumed the OOS history through this date.

### Frozen virgin zone

`2026-09-23 onward
`

No P13-Q/P13-R research pipeline may consume decision dates in this zone.

P13-U `assert_research_zone` is a fail-fast guard. Any decision date `>= 2026-09-23` entering the protected research entry points must raise an error.

### P13-T execution rule

P13-T may only execute against a genuine virgin temporal holdout after the boundary is frozen and the minimum/recommended data condition is satisfied. Existing P13-R validation data must never be relabeled as holdout data.

## Data Boundary

- Validation universe: frozen 76-stock universe.
- Latest data observed by the last P13-U gate run: **2026-09-24**.
- Virgin dates observed: 2026-09-23 and 2026-09-24.
- Missing symbols on both observed virgin dates: `000004`, `000016`.
- Missing data is reported; symbols are not silently dropped.
- P13-U checks date/symbol existence and integrity; it does not calculate performance metrics.
- Two stocks without SW1 membership remain subject to data-existence checking and are not silently removed.

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

P13-U records SHA256 hashes for the frozen inputs in `data/industry/p13u/frozen_manifest.json`.

## Known Limitations

1. P13-T has not produced final holdout metrics because the virgin zone is still too short.
2. P13-U cannot prove arbitrary runtime reads that leave no auditable artifact; its contamination check covers the defined consumed-date set and known research artifacts.
3. Trading-day identification uses actual universe data rather than an external exchange calendar; missing coverage is therefore reported explicitly.
4. The virgin zone currently contains only two trading days, so no model/policy performance conclusion may be drawn from it.
5. P13-U is an integrity gate, not a prediction or recommendation stage.
6. P13-U does not automatically execute P13-T when the threshold is reached; independent acceptance is still required.
7. Research-only calibration/policy discoveries remain non-production until independently validated.

## Next Phase

**P14 — Multi-Market Information Infrastructure**

P14 should proceed independently of the still-accumulating P13-U virgin holdout.

P14 must:
- preserve the P13-U research-zone guard;
- avoid consuming or contaminating the virgin holdout;
- build the information/data infrastructure needed for the eventual information-factor and overseas-market extensions;
- remain research-only;
- avoid adding unvalidated factors to production;
- preserve PIT, freshness, source traceability and deterministic/reproducible outputs.

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

Accepted because:
- frozen boundary is explicit and does not move with latest data;
- virgin dates are identified conservatively;
- contamination checks and research-zone guards are implemented;
- missing coverage is reported without silently changing the universe;
- no performance/recommendation metrics are produced;
- repeated artifacts are byte-identical;
- future-row immunity is tested;
- full pytest and P13-M CI regression are green;
- production source diff from the P13-R baseline is empty according to the acceptance report.

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
