# AGENT_RULES — Codex 强制工程规则

本文件是 Codex 的最高优先级工程约束之一。

## 1. 数据真实性

禁止：
- 虚构行情；
- 虚构新闻；
- 虚构公告；
- 虚构财务数据；
- 虚构资金流；
- 虚构实时数据；
- 把缓存数据标记为 realtime；
- 把 proxy 变量描述成客观事实。

所有外部数据必须记录 source、source_type、fetched_at、event_time、available_time、latency、quality、fallback、warning、raw_ref（若有）。

## 2. Point-in-Time 是硬约束
必须区分 event_time 与 available_time。回测只能使用 available_time <= decision_time 的数据。

## 3. LLM 与 Quant Engine 必须隔离
Quant Engine 负责 factor、regime、probability、risk、backtest、calibration；Agent 负责语言理解、事件分类、证据整理、矛盾检测、报告和复盘。Agent 不得直接修改 Quant Engine 数值输出。

## 4. 概率不是保证性胜率
未严格 OOS + calibration 验证的概率必须标记 UNCALIBRATED MODEL OUTPUT。

## 5. 不允许数据泄漏
检查 future financial statement、future revised data、future labels、future scaler、future feature selection、future sector membership、survivorship bias、look-ahead bias。

## 6. A股交易约束
回测考虑 T+1、停牌、涨跌停不可成交、流动性、手续费、滑点。

## 7. 因子不能重复计票
支持 correlation、clustering、neutralization、feature selection、PCA/VIF（适用时）。

## 8. 市场状态不能依赖单一指数
支持多指数、breadth、turnover、volatility、limit-up/down、sector dispersion、style、liquidity。

## 9. 不自动连接券商下单
第一阶段只做 research、paper test、backtest、review。

## 10. 工程质量
要求 type hints、docstrings、logging、config、明确异常、retry/timeout、测试；禁止 except: pass、假 TODO 完成、mock 冒充真实功能。

## 11. 状态标签
IMPLEMENTED / PARTIAL / SCAFFOLD_ONLY / NOT_IMPLEMENTED / BLOCKED_EXTERNAL_DEPENDENCY。

## 12. 每阶段必须产生证据
每阶段更新 docs/progress/Px.md，记录 scope、implemented、modified files、tests、data sources、limitations、blocked、risks、next phase。

## 13. Git 纪律
建议每阶段独立 commit：P0 至 P8。不得为了方便把所有阶段混成一个巨大 commit。
