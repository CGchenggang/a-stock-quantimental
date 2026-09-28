# Decisions

## P13-M

- Keep pooled and single-stock outputs semantically identical; do not relax assertions for numeric differences.
- Treat pooled shared context as an optimization only; it must not alter PIT membership, peer exclusion, factor windows, or target-specific results.
- Use exact fallback for sparse/short-lived industry membership rather than silently changing the observation population.
