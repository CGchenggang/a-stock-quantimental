# P8 Legacy Migration Audit

## Current checkpoint

The V2 package is locally executable and its current test suite passes. The legacy layer remains intact; migration is deliberately incremental.

## New migration boundary

`astock_v2.data.legacy_adapter.datapoint_from_legacy` converts a legacy observation into the V2 `DataPoint` contract only when the caller supplies an explicit `event_time`. The adapter never assumes that a fetch time is the historical event time.

Fallback observations are retained as fallback provenance and default to quality `C` unless a higher quality is explicitly justified by the source contract.

## Legacy audit priorities

| Area | Current risk | Required V2 treatment |
|---|---|---|
| Realtime cache | A cached result can outlive the intended freshness window | Preserve fetched time and freshness; never relabel cache as realtime |
| Intraday data | Legacy code has a separate intraday path, but granularity must be verified | Require actual timestamped bars/ticks before migration |
| Fund flow | Some legacy fields are explicitly proxies | Keep proxy labels through factors and reports |
| Market regime | Legacy checker is centered on CSI 300 and weather labels | Migrate only into the multi-input V2 regime engine |
| Daily fallback | Previous-close fallback is useful operationally but is not realtime | Keep fallback provenance and exclude it from realtime-only claims |
| Orchestration | Legacy collectors write broad snapshots | Replace with typed P1/P6 packets gradually |

## Backtest demonstration note

`data/sample_ohlcv.csv` is a smoke-test fixture, not a performance dataset. Its short, hand-constructed sequence can produce extreme metrics such as a 1.0 hit rate or very large Sharpe. These values must not be interpreted as validated strategy performance.

Production backtests must use Point-in-Time inputs, walk-forward folds, transaction costs/slippage, liquidity constraints, suspension and limit rules, and calibrated out-of-sample evaluation.

## Migration gate

A legacy path is considered migrated only after:

1. V2 provenance is preserved.
2. Timing semantics are explicit.
3. A regression fixture covers the intended equivalence.
4. The V2 path passes the full test suite.
5. The old path remains available until the migration is validated.