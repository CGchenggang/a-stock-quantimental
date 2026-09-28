# Current Task

## P13-M: Performance validation and final acceptance

Goal: validate that the pooled PIT-safe industry-relative implementation is materially faster and completes on the real 76-stock local universe without changing single-stock semantics.

Required checks:
1. focused pooled-vs-single regression — PASS
2. full pytest regression — P13-M independent regression PASS; full job remains blocked by pre-existing P7 failures
3. CLI/backtest smoke only if affected
4. performance benchmark on the real 76-stock local universe
5. inspect output completeness and pooled/single semantic equivalence
6. update agent state and test results

Debug budget: 3 automatic rounds. Do not weaken assertions to make tests pass.
