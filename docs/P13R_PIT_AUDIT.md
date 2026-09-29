# P13-R PIT Audit — Recommendation Engine Research

- 日期：2026-09-29
- 范围：P13-R 全部分析（`scripts/run_p13r_analysis.py`，产物 `data/industry/p13r/`）

## 1. Probability 来源

全部概率来自 P13-O audit JSON 的 baseline variant 行（生产 walk-forward 252/20/20/1 的 OOS 输出）。P13-Q 的校准器以相同协议重建：Platt/Isotonic **仅用 discovery OOS 行（decision_time < 2025-01-01）的 (p, y) 拟合**，应用于 validation OOS 行。测试 `test_calibration_fit_isolated_to_discovery_rows` 锁定。

## 2. Expected-return / risk information cutoff

`rolling_features` 对 decision day t 的候选只使用**同 symbol 中 decision 日期严格早于 t** 的已完结行（其 next_return 在 t 前一日收盘已公开），窗口 60 行、1%/99% winsorize。测试 `test_rolling_features_ignore_future_rows` 证明：翻转/污染 t 之后的行不改变 t 行的任何 feature。开发中发现并修复一个真实泄漏：fallback 统计原本池化全历史（含未来行）——现限定 discovery 窗口（测试锁定）。

## 3. Regime / liquidity cutoff

Regime 标签复用 P13-O 的 `RegimeLabeler`（等权指数 20 日累计收益仅用至 t−1，阈值 ±3% 先验不变）。流动性：本地数据无绝对成交量字段，未设流动性约束（limitation，见验收报告）；industry 归属使用 P13-O 的 PIT schedule 查询（与因子一致）。

## 4. Transaction cost assumptions

三情景（zero/low/medium = 0、5+5、10+10 bp）全部写入 `analysis_config.json` 的 `cost_scenarios`，无隐藏常量（`COST_SCENARIOS` 与 config 同源）。`net_return = gross − (commission+slippage)/10000 × turnover`；turnover 为相邻决策日持仓集对称差/持仓规模。

## 5. Selection policy

8 个 policy 全部预定义于 `docs/P13R_RESEARCH_PLAN.md`（先验），registry（`decision_policy_registry.json`）记录完整参数。评估前未增删/调参；阈值（0.50/前3/80分位/ER>0/行业≤2）为自然先验点，未扫描。测试 `test_policy_registry_schema_and_predefined_ids` 锁定 8 个 policy 不可变。

## 6. Next-day label

label（= next_return > 0）仅用于评估统计与 discovery 窗口内的 calibration 拟合；从不进入因子、expected-return、risk 或 selection 逻辑。

## 7. Evaluation isolation

所有 policy 在同一 validation OOS 行集（28,965 行，行业 cap 后各 policy N 不同但行集来源一致）上一次性评估。validation 结果未反馈到任何参数（git 历史中 policy 定义先于首次成功运行）。validation 是 **research validation**（P13-O 曾聚合观察该窗口），不是 virgin holdout——所有 registry status = research_only。

## 8. 结论

Recommendation 在 decision_time 产生时可用的信息 = discovery 拟合的校准器 + 该 symbol 在 t 之前已完结的收益历史 + PIT 行业/Regime 标签。无未来信息进入任何环节（测试锁定 + 本审计逐项核验）。
