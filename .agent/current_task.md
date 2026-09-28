# Current Task

## P13-M: Verify pooled context matches single-stock context

Goal: prove that pooled execution preserves single-stock industry context and factor inputs under identical PIT-safe inputs.

Required checks:
1. focused pooled-vs-single regression
2. full pytest regression
3. CLI/backtest smoke only if affected
4. performance benchmark after correctness is green
5. inspect for state contamination/cache leakage
6. update agent state and test results

Debug budget: 3 automatic rounds. Do not weaken assertions to make tests pass.
