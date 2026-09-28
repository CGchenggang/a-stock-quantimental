# Test Results

## 2026-09-28

- Baseline commit before current fix: dd28171.
- GitHub Actions status: no workflow/status was present.
- Known focused-test failure before current fix: pooled context for 000001 was empty while single-stock context had decision-time rows.
- Root cause: pooled target calculation block was accidentally outside `for symbol in symbols`.
- Fix commit: 3dffccdece8e5abd7292d6aa2df7e0a7fe96d42f.
- Local historical test result retained from prior run: 2 passed, 1 failed on pooled-vs-single equality.
- Current verification: pending GitHub Actions run after CI workflow is added.
