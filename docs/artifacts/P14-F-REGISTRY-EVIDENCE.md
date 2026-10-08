# P14-F Feature Registry Evidence

Registry: `docs/contracts/p14f/FEATURE_REGISTRY.json`

```json
{
  "registry_sha256": "401c772d1c67a3e55f52305139bbd5ca33ecf8d271a9b3b844742adbdf95112f",
  "feature_set_id": "fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe",
  "registry_version": 1,
  "definition_count": 6,
  "frozen_binding": {
    "model_version": "97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664",
    "feature_set_id": "fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe",
    "model_variant": "industry_5_20"
  }
}
```

## Blob verification (HEAD = b7b7192)

| source_file | pinned blob | `git cat-file -e` |
|---|---|---|
| `src/astock_v2/local_pipeline.py` | `0582f91ef406d329c7ce3d7460db8f467c20ef75` | PASS (4 stock factors) |
| `scripts/run_local_industry_relative_oos.py` | `0b6c0f140fad636a50cee67d2502d6ce27adc5cb` | PASS (2 industry factors) |

## Membership resolution (frozen MODEL_APPLICATION order)

```
1. momentum                         -> src/astock_v2/local_pipeline.py@0582f91…
2. volatility                       -> src/astock_v2/local_pipeline.py@0582f91…
3. trend                            -> src/astock_v2/local_pipeline.py@0582f91…
4. volume_ratio                     -> src/astock_v2/local_pipeline.py@0582f91…
5. industry_relative_return_5       -> scripts/run_local_industry_relative_oos.py@0b6c0f1…
6. industry_relative_return_20      -> scripts/run_local_industry_relative_oos.py@0b6c0f1…
```

Derived `feature_set_id` = `fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe`
(matches the frozen MODEL_APPLICATION's `feature_set_id` — P14F2-019 closure PASS).

## RV7-1 FS6 computation-identity equivalence

The research run (R4-A) consumes the two industry-relative factors via the
single-stock builder `build_stock_industry_relative_context_map` (the FS6
integration, already landed on main). The registry's `entry_symbol` pins the
pooled builder `build_universe_industry_relative_context_maps` per the
contract's lineage-definition authority. These two builders are
**field-exact equivalent** per the standing P13-M regression
`tests/test_industry_relative.py::test_pooled_context_matches_single_stock_context`:
for every (symbol, decision_time), both builders emit byte-identical
`industry_relative_return_5` / `industry_relative_return_20` values; the
pooled builder only differs in amortizing the universe-wide computation.
The equivalence is a standing CI invariant, not a P14-F invariant, and
runs independently of the registry.

## Date

2026-10-08

## Authorization

ZCODE V8 / P14F-IMPL-001 (design contract v5 ACCEPTED; owner authorization
2026-10-08).
