# P13-P Research Plan — Independent Factor Validation & Candidate Selection

- 日期：2026-09-29
- 前置：P13-M / P13-N / P13-O 均已由 ChatGPT 验收 PASS
- 性质：**研究验证层**。不修改生产预测路径（`src/astock_v2/**` 零改动）；不宣布任何因子"有效"。

## 1. Research Question

现有 production 因子中，哪些具有足够稳定的**独立**样本外信息，可以进入下一阶段 Probability / Calibration Model？重点验证 P13-O 发现唯一呈单调横截面结构的 `volatility`（Q1→Q5 up_rate 0.4546→0.4890）——但 P13-O 的发现不构成其进入生产的理由。

## 2. Exact Protocol（与 P13-M/N/O 完全一致）

train=252 / test=20 / step=20 / gap=1；logistic 同 baseline 实现；76-stock universe；当前 PIT semantics、label、decision_time、available_time、SW1 PIT membership。**本阶段禁止修改任何协议**；如必须改变，停止并上报人工。

评估器直接复用 `scripts/run_local_industry_relative_oos.py::evaluate`（同一 walk-forward 与 logistic 实现）；`walk_forward_windows` 只依赖行序列长度，因此同一行集上所有模型的 OOS 行完全对齐（测试锁定）。

## 3. 数据来源（零重跑）

全部输入来自 P13-O 的 audit JSON（`data/industry/p13o/oos_predictions_76.json`，94,760 OOS 行/variant × 4，另含每 symbol 全部 1612 factor rows 的 6 因子值 + label + next_return）。不重新运行 76-stock pipeline。

## 4. Discovery / Validation Split（先验固定，非结果驱动）

- OOS 决策日范围：2021-02-22 → 2026-09-22（1358 个交易日）。
- **Discovery period：decision_time < 2025-01-01**（2021-02-22 → 2024-12-31）。
- **Validation period：decision_time ≥ 2025-01-01**（2025-01-01 → 2026-09-22）。
- 边界为整年先验边界，选择依据是"自然年 + 与 P13-O 年度切片协议兼容"，在查看任何窗口内结果之前固定于本计划。
- Quintile 边界只在 discovery 样本上计算，原样应用到 validation（validation 分布不参与边界确定）。

**Leakage 声明（如实）**：P13-O 的发现阶段使用了全部历史，其全样本 pooled quintile 与年度 ΔAccuracy 聚合表在 validation 窗口上有过聚合层面暴露。因此本阶段不存在严格的 virgin holdout：窗口内 volatility 的模型级增量指标与分位稳定性是首次计算，但窗口本身曾被聚合观察。按交接 §6 判定标准，若独立验证数据不足，volatility 的 `validation_status` 最高只能为 `candidate`，并在 registry 与验收报告中写明 `insufficient independent validation data` 的原因。

## 5. 分析清单

| 任务 | 内容 | 产物（data/industry/p13p/） |
|---|---|---|
| T1 单因子 audit | 6 因子 × (Model A baseline vs Model B baseline+factor)，同一 OOS 行集；N/acc/brier/ll/mean_p/pos_rate/Δ 三项 | `single_factor_audit.json` |
| T2 volatility 稳定性 | 时间片（全/1-3-1/年/最近2年）× Q1–Q5（discovery 边界）× up_rate / mean_next_return / Q5−Q1 spread；个股 spread 分布；regime 条件（复用 P13-O 的 PIT-safe RegimeLabeler，阈值不重找）；symbol-clustered bootstrap（B=1000，seed=20260929） | `volatility_stability.json` |
| T3 增量验证 | Model A / B(+volatility) / C(+ir5) / D(+ir20) / E(+vol+ir5+ir20)，同一行集；含 discovery/validation 窗口拆分 | `incremental_models.json` |
| T4 冗余 | 6×6 Pearson + Spearman + missingness + 分布统计；重点 volatility×其余 5 因子 | `factor_redundancy.json` |
| T5 候选注册表 | `factor_candidates.json`，schema 见交接 §8；validation_status 枚举受限 | `factor_candidates.json` |

统一入口：`scripts/run_p13o_analysis.py` 模式沿用——`scripts/run_p13p_analysis.py --audit <p13o json> --membership <csv> --root data all`。

## 6. 禁止事项（重申）

- 不用 validation 结果选因子/调定义/选阈值/删股票/选年份/改参数。
- volatility 不接入生产（Recommendation Engine / Agent / probability output / live logic 全部不碰）。
- validation_status 禁用 best/strongest/winner/guaranteed/high_probability。
- 不宣布 PASS/PASSed；最终验收归 ChatGPT。

## 7. 测试与复现性

新增测试（`tests/test_p13p_analysis.py`）：OOS 行对齐、quintile 可复现、split 可复现与 PIT 边界、bootstrap seed 可复现、registry schema、无 validation 泄漏（split 无重叠且 discovery 统计不含 validation 行）、重复分析 byte-identical。全量 pytest 保持 179 passed 不回退。JSON/Markdown 产物 sort_keys + 固定 seed 确保重复运行 byte-identical。
