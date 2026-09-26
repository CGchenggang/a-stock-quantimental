# A-Stock Quantimental 2.0 — Codex 完整实施计划

## 0. 项目定位

目标：将 `CGchenggang/a-stock-quantimental` 从一个信息抓取 + 规则/脚本型系统，升级为：

> Point-in-Time 数据 + 因子工程 + A股市场状态 + 概率模型 + 风险模型 + Walk-forward OOS + AI Research Agent + Recommendation Ledger

的 Quantimental Research System。

不是：

> LLM 猜股票 / 生成一个“看起来专业”的买卖答案。

---

# P0 — Data Infrastructure

## P0.1 Point-in-Time Schema

核心对象至少包含：

```text
symbol
field
value
event_time
available_time
source
source_type
fetched_at
quality
raw_ref
revision
```

必须支持：

- PIT 查询；
- 时间过滤；
- revision；
- source；
- quality；
- fallback。

## P0.2 Provider Interface

所有数据源通过统一 Provider 接口接入。

Provider 不应该散落在业务逻辑中。

建议：

```python
class DataProvider(Protocol):
    def fetch(...)
    def health(...)
```

## P0.3 Quality

质量检查：

- freshness；
- missing；
- duplicate；
- schema；
- timestamp；
- source agreement；
- stale；
- fallback；
- coverage。

## P0.4 Acceptance

必须能证明：

```text
available_time > decision_time
```

的数据不会进入历史决策。

---

# P1 — Data Sources

设计 adapter：

```text
realtime
daily
intraday
index
sector
breadth
flow_proxy
fundamentals
announcements
news
macro
```

## P1.1 市场数据

至少覆盖：

- OHLCV；
- turnover；
- index；
- intraday；
- suspension；
- limit status。

## P1.2 市场广度

包括：

- advancers；
- decliners；
- limit-up；
- limit-down；
- failed limit-up；
- highs；
- lows；
- consecutive boards（若数据可靠）。

## P1.3 行业

包括：

- sector return；
- sector turnover；
- relative strength；
- sector dispersion；
- rotation；
- concentration。

## P1.4 基本面

包括：

- revenue；
- revenue growth；
- net profit；
- profit growth；
- ROE；
- ROIC；
- operating cash flow；
- debt ratio；
- gross margin；
- net margin。

必须 Point-in-Time。

## P1.5 估值

包括：

- PE；
- PB；
- PS；
- EV/EBITDA；
- historical percentile；
- sector percentile。

不能使用：

```text
PE 越低越好
```

这样的单变量规则。

## P1.6 事件

标准化：

```text
symbol
event_type
event_time
available_time
direction
magnitude
horizon
confidence
source
source_url
```

事件：

- earnings；
- forecast；
- buyback；
- insider；
- unlock；
- M&A；
- restructuring；
- contract；
- penalty；
- inquiry；
- litigation；
- guarantee；
- shareholder change。

## P1.7 宏观

支持：

- rates；
- RMB；
- DXY；
- US equities；
- US Treasury；
- commodities；
- gold；
- oil；
- PMI；
- credit;
- fiscal / monetary events。

所有外部依赖必须有 fallback / warning。

---

# P2 — Factor Engine

统一流程：

```text
raw factor
 ↓
missing handling
 ↓
winsorize
 ↓
normalize
 ↓
neutralization
 ↓
decorrelation
 ↓
factor score
```

因子族：

```text
trend
momentum
liquidity
flow_proxy
quality
valuation
earnings_revision
event
sentiment
macro
```

## P2.1 Technical

至少支持：

- 1/3/5/10/20/60D return；
- MA5/20/60/120；
- MA gap；
- RSI；
- ATR；
- volatility；
- volume z-score；
- breakout；
- drawdown；
- relative strength。

## P2.2 Fundamental

至少：

- growth；
- ROE；
- ROIC；
- cash flow；
- leverage；
- margin；
- earnings quality。

## P2.3 Earnings Revision

关注：

- forecast revision；
- estimate dispersion；
- earnings surprise；
- guidance；
- revision direction。

## P2.4 Event

事件必须有：

- direction；
- magnitude；
- confidence；
- horizon。

---

# P3 — Market Regime

输出：

```text
TREND_UP
TREND_DOWN
RANGE
HIGH_VOL
RISK_OFF
UNKNOWN
```

输入至少：

```text
index trend
breadth
turnover
volatility
sector dispersion
limit-up/down
style
liquidity
```

核心不是简单判断“牛/熊”，而是：

```text
P(stock outcome | factors, market_regime)
```

---

# P4 — Probability Model

## P4.1 第一阶段

优先：

- Logistic Regression；
- Ridge。

不要一开始就堆复杂模型。

## P4.2 后续

只有 OOS 证明有效才增加：

- LightGBM；
- XGBoost；
- Random Forest。

## P4.3 输出

至少：

```text
P(up, 1D)
P(up, 3D)
P(up, 5D)
P(up, 10D)

expected_return
volatility
drawdown
```

## P4.4 Calibration

必须：

- Brier；
- reliability curve；
- calibration error。

训练与 calibration 必须严格遵守时间顺序。

---

# P5 — Backtest

必须：

- walk-forward；
- PIT；
- survivorship-aware；
- no leakage；
- transaction cost；
- slippage；
- T+1；
- limit-up/down；
- suspension；
- liquidity。

## Metrics

至少：

```text
hit rate
average return
median return
profit factor
Sharpe
Sortino
max drawdown
turnover
Brier
calibration error
```

并按：

- regime；
- confidence；
- factor bucket；
- market environment

分解。

---

# P6 — AI Research Agent

## Agent Tool Layer

Agent 不能直接调用杂乱 API。

Agent → Structured Tool → Engine / Data Provider

## Skills

```text
market-snapshot
stock-research
screen
event-research
decision-review
backtest-review
postmortem
data-health
```

## 股票研究流程

```text
data-health
 ↓
market-snapshot
 ↓
stock-research
 ↓
event-research
 ↓
quant model
 ↓
risk
 ↓
decision-review
```

## Stock Research 内容

固定顺序：

1. current market；
2. company basics；
3. technical；
4. fundamental；
5. valuation；
6. earnings；
7. flow proxy；
8. news；
9. announcements；
10. regime；
11. quant output；
12. risk；
13. contradiction；
14. final research state。

必须输出：

- supporting evidence；
- contradictory evidence；
- missing evidence。

---

# P7 — Recommendation Ledger

记录：

```text
symbol
decision_time
model_version
feature_version
input_snapshot
market_regime
probability
expected_return
volatility
drawdown
risk_flags
evidence
invalidation
decision_class
```

自动回填：

```text
T+1
T+3
T+5
T+10
```

形成：

```text
Prediction Ledger
```

用于计算历史实际表现。

---

# P8 — Legacy Migration

保留旧版。

建立 compatibility layer。

重点审查：

### 1. intraday

`intraday_reversal_detector` 是否真的使用 minute/intraday 数据。

### 2. fundflow

资金流计算是否进入最终决策。

### 3. realtime

“realtime index” 是否真实实时，还是缓存。

### 4. cache TTL

不同数据类型必须不同：

```text
realtime quote: very short
intraday: short
daily: session based
fundamental: long
macro: event dependent
```

### 5. market regime

从单一指数升级为：

```text
multi-index
+
breadth
+
liquidity
+
volatility
+
sector
+
style
```

---

# 最终架构

```text
                    User
                      |
                      v
              AI Research Agent
                      |
             Structured Tool Layer
                      |
          +-----------+-----------+
          |                       |
          v                       v
     Quant Engine             Evidence
          |                       |
   +------+-------+               |
   |      |       |               |
 Data  Factor  Regime             |
   |      |       |               |
   +------+-------+               |
          |                       |
          v                       |
 Probability + Risk <-------------+
          |
          v
   Walk-forward / OOS
          |
          v
 Recommendation Ledger
          |
          v
     Postmortem
          |
          v
   Model Improvement
```

---

# 最终验收

```bash
pytest -q
python -m astock_v2.cli init
python -m astock_v2.cli demo 000001
python -m astock_v2.cli backtest --csv data/sample_ohlcv.csv
```

最终报告必须包含：

```text
Market Environment
Fundamentals
Technicals
Flow / Behavior
Events
Quant Model
Supporting Evidence
Contradictory Evidence
Missing Evidence
Risks
Invalidation Conditions
Decision Class
```

`Decision Class` 是研究系统状态，不是收益保证。
