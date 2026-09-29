# P13-O Research Plan — Factor 稳定性与信息含量

- 日期：2026-09-29
- 阶段：P13-O（P13-N 已验收通过）
- 性质：**描述性研究**。目标不是证明因子有效或无效，而是用严格 OOS、PIT-safe、可复现的方法刻画 industry-relative 因子的实际表现及其稳定性。

## 1. 研究问题

industry-relative return 因子（industry_relative_return_5 / _20，以及作为对照的 stock 因子）是否具有稳定、可重复、样本外的预测信息？这种信息是否依赖特定股票、行业、时间区间或市场状态？

P13-M 已观察到 pooled ΔAccuracy ≈ 0 且方向不稳；P13-O 判定这是时间不稳定、横截面不稳定、regime 依赖，还是统计噪声。

## 2. 固定协议（与 P13-M/N 完全一致，禁止改动）

- walk-forward：train 252 / test 20 / step 20 / gap 1；logistic 与 P13-N baseline 相同
- variants：baseline / industry_5 / industry_20 / industry_5_20
- 数据：76 股验证集、SW1 PIT membership、本地日线（1633 个交易日）
- 指标：Accuracy、Brier、Log Loss（p≥0.5 判类）；一切 delta 在**同一 OOS 行集**内配对计算（baseline_p 随行携带）

## 3. 分析清单与产物

| # | 分析 | 产物 |
|---|---|---|
| O1 | 时间稳定性：全样本 / 前·中·后 1/3 / 每年 / 最近 2 年 | `time_stability.{json,md}` |
| O2 | 股票稳定性：per-symbol delta 分布（mean/median/q10–q90/improved·degraded 计数） | `symbol_stability.{json,md}` |
| O3 | 行业稳定性：decision-time PIT membership 归属（与因子同一 schedule 查询），无合法归属不归类 | `industry_stability.{json,md}` |
| O4 | 因子分位：6 个因子 × OOS 等频 5 组 × {N, mean_factor, up_rate, mean_next_return} | `factor_quantiles.{json,md}` |
| O5 | Regime 条件：等权 universe 指数 20 日累计收益（仅用 t-1 及以前），BULL>+3% / BEAR<-3% / NEUTRAL；阈值为先验，不拟合 | `regime_analysis.{json,md}` |
| O6 | 成本/换手：p≥0.5 持有 1 日、收盘执行、单边 10bp；gross/turnover/cost/net per day | `cost_sensitivity.{json,md}` |
| O7 | Bootstrap：symbol cluster（有放回重抽 76 只），B=1000，seed=20260929，95% 区间 | `bootstrap.{json,md}` |

统一入口：`scripts/run_p13o_analysis.py --audit <predictions.json> --membership <csv> [--root data] {time|symbol|industry|quantiles|regime|cost|bootstrap|all}`

## 4. 数据来源

OOS 明细由 `run_local_industry_relative_oos.py --predictions-out` 导出（76 股一次运行，310s，pooled 指标与 P13-N golden 逐位一致）。每行含 variant/symbol/decision_time/p/y/baseline_p；因子值与 next_return/label 按 (symbol, decision_time) 配套导出。重跑原因：P13-N 只保存了 stdout 汇总与 context JSON，OOS per-prediction 明细从未落盘。

## 5. PIT 与泄漏控制

- 行业归属使用与因子内部一致的 PIT schedule 查询（effective_from/available_time/decision_time），不用当前行业回填。
- Regime 标签只用 decision 日之前的指数收益（t-1 收盘可得），阈值固定为先验。
- Quantile 边界在 OOS 样本内计算——这是描述性单调性检查（声明于产物文件头），不用于任何参数选择。
- 无任何基于测试集表现的股票/行业/参数筛选；不删除表现差的股票；不调整测试集。

## 6. 结果处理纪律

所有切片必须报告 N；均值必须伴随 median 与分位数；bootstrap 必须给出区间与 seed。如果结果显示因子没有稳定增量信息——如实报告。禁止使用"证明有效/保证收益"类结论性表述。
