# Code Agent Handoff

在 CGchenggang/a-stock-quantimental 基础上做保守式重构。保留旧版代码，新核心进入 src/astock_v2/。

## P0
Point-in-Time、provider 接口、freshness/source/fallback/quality、ledger、schema validation。

## P1
realtime、daily、intraday、index、sector、breadth、flow proxy、fundamentals、announcements、news、macro adapters；统一 timeout/retry/source metadata。

## P2
trend、momentum、liquidity、flow_proxy、quality、valuation、earnings_revision、event、sentiment、macro；统一 winsorize -> normalize -> missing -> neutralization -> decorrelation。

## P3
多指数、breadth、turnover、limit-up/down、sector dispersion、volatility、style。

## P4
先 Logistic + Ridge；输出 1/3/5/10 日 P(up)、expected return、volatility、drawdown、Brier/calibration。

## P5
walk-forward、PIT、survivorship-aware、slippage、transaction cost、涨跌停不可成交、停牌、T+1。

## P6
data-health -> market-snapshot -> stock-research -> event-research -> decision-review；LLM 不能修改量化输出。

## P7
记录 input snapshot、model/feature version、decision time、probability、expected return、risk、evidence、invalidation；回填 T+1/T+3/T+5/T+10。

## P8
核查 intraday、fundflow、realtime index、cache TTL、market regime，并建立 compatibility layer。

禁止虚构数据、把 proxy 当事实、把未 OOS 概率写成保证性胜率、自动券商下单。

验收：
pytest -q
python -m astock_v2.cli init
python -m astock_v2.cli demo 000001
python -m astock_v2.cli backtest --csv data/sample_ohlcv.csv
