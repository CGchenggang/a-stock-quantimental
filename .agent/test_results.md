# Test Results

## 2026-09-28

- Focused P13-M pooled regression: passed in GitHub Actions run 36423156472, job 108930579792.
- The regression now compares pooled output with an independent single-stock execution for every symbol in the synthetic validation universe and repeats the pooled build to detect state leakage.
- Full pytest job 108930580083 failed in the existing Agent/backtest/ledger step on the pre-existing P7 Ledger API/test mismatch. P8 and P13-M steps were skipped by job fail-fast ordering; this is unrelated to P13-M.
- P13-M correctness is therefore green independently of the unrelated full-suite P7 failure.
- Performance validation remains pending on the real local 76-stock dataset because that dataset is not stored in the repository/CI.
- Prior local performance attempt exhausted memory/time before completion; the pooled implementation has since been optimized to share PIT return state and industry aggregates.
