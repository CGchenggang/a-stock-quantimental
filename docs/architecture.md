# Architecture

```text
Agent / Skills
      |
      v
Research Orchestrator
      |
      +-- Data Gateway ---------> Providers
      +-- Point-in-Time Store
      +-- Factor Engine
      +-- Regime Engine
      +-- Probability Model
      +-- Risk Engine
      +-- Decision Engine
      +-- Recommendation Ledger
```

## 数据

所有数据必须有：
`event_time`, `available_time`, `source`, `quality`, `raw_ref`, `revision`。

回测只能使用 `available_time <= decision_time` 的信息。

## 信息层

Market：行情、盘口、指数、宽度、涨跌停、ETF。
Fundamental：收入、利润、现金流、ROE/ROIC、估值、盈利预期变化。
Event：公告、财报、回购、增减持、解禁、监管、订单、并购等。
Macro：利率、汇率、商品、海外市场。
Sentiment：涨跌停、炸板、连板、融资、ETF 流量等。

## Agent 边界

LLM 可以做：新闻/公告摘要、事件分类、证据归纳、矛盾解释、研究报告。
LLM 不可以做：虚构行情、修改量化权重、把代理变量写成确定事实、把未验证概率写成保证性胜率。
