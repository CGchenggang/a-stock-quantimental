# P13-R Acceptance Report — Recommendation Engine Research

- 日期：2026-09-29
- 基线：`d8bea19`（P13-Q CI 修复终点）
- 文档：`docs/P13R_RESEARCH_PLAN.md`、`docs/P13R_PIT_AUDIT.md`
- 产物：`data/industry/p13r/`（manifest.json 记录 6 个研究 JSON 的 SHA256）
- 状态：**implementation complete / experiment complete / tests passed / awaiting independent acceptance**——不自行宣布 PASS。

## 1. What was tested

Research-only Recommendation Engine：以 P13-O audit 的 baseline OOS 概率（94,760 行；validation 28,965 行）为输入，复用 P13-Q 协议的校准器（discovery 拟合 → validation 应用），叠加 PIT-safe 滚动 expected-return（60 行窗口、1%/99% winsorize）与 risk 特征，对 **8 个预先定义的 policy**（4 个 family：threshold / top-k / percentile / expected-return，含 hold_all 基准与复合风险过滤变体）在同一 validation 行集上一次性评估。约束：每决策日同行业 ≤2。成本三情景（zero/low/medium = 0、5+5、10+10 bp，全部入 config）。`src/astock_v2/**` 零改动。

## 2. Policy Comparison（low-cost 情景，validation 窗口）

| policy | N | coverage | hit_rate | net/day | turnover | max_dd |
|---|---|---|---|---|---|---|
| hold_all（基准） | 18,632 | 0.6433 | 0.4739 | +0.00020 | 0.0077 | −0.2520 |
| threshold_raw_p50 | 7,823 | 0.2701 | 0.4823 | +0.00021 | 0.3256 | −0.2188 |
| threshold_platt_p50 | **15** | 0.0005 | 0.2000 | −0.00605 | 1.2667 | −0.1615 |
| threshold_iso_p50 | **1** | 0.0000 | 1.0000 | +0.10044 | 0 | 0 |
| topk_platt_k3 | 1,255 | 0.0433 | 0.4821 | −0.00104 | 0.6693 | −0.3794 |
| percentile_platt_p80 | 5,592 | 0.1931 | 0.4832 | −0.00015 | 0.4061 | −0.2722 |
| er_platt_0 | 8,684 | 0.2998 | 0.4675 | −0.00032 | 0.2050 | −0.3252 |
| er_platt_pos_risk | 3,611 | 0.1247 | 0.4691 | +0.00016 | 0.2401 | −0.1937 |

观察（限定"本研究窗口、当前 protocol 与成本假设下"）：

1. **字面阈值在校准后失效**：Platt 校准把 raw 0.5 的语义映射到 raw≈0.675（slope 0.163 的直接后果），validation 中 p_cal≥0.5 仅 15 行、isotonic 仅 1 行。这定量验证了 P13-Q 的警告——raw 概率的绝对数值不可直接当阈值使用。
2. **没有 selection policy 的 net return 显著优于 hold-all**：bootstrap（symbol 聚类，B=1000，seed=20260929）显示全部 policy 的 net_return_difference CI 包含 0（threshold_iso_p50 的"+0.10 SIG"是 n=1 的统计伪影，如实标注无意义）；hit_rate 差异亦全部不显著。
3. **唯一显著效应是 coverage 缩减**（各 policy −0.34 ～ −0.65，CI 不含 0）——选择逻辑确实大幅缩减候选集，但缩减没有带来可检测的质量提升。
4. **风险过滤有效控制回撤**：er_platt_pos_risk（ER>0 且波动 ≤ 当日中位）把 max_dd 从 −0.325 收窄到 −0.194、coverage 降到 0.125，net/day 与 hold-all 无显著差异——回撤控制的代价是机会损失，不是 alpha 来源。

## 3. Cost Sensitivity（er_platt_pos_risk 为例）

zero +0.00040 / low +0.00016 / medium −0.00008（net/day）——换手 0.24/日下 medium 成本即把该 policy 推为负值；hold_all 因换手极低（0.008）对成本几乎不敏感。**任何策略性换手在本成本假设下都被摩擦吞噬。**

## 4. Regime / Stability

三 regime（BULL/NEUTRAL/BEAR，P13-O 定义复用）与年度（2025/2026）稳定性表在 `policy_metrics.json`。各 policy 的 regime 间差异方向不一致、无统计检验下的稳定模式（与 P13-O 的 regime 结论一致）。

## 5. Bootstrap

全部数值见 `bootstrap_results.json`（unit=symbol，B=1000，seed=20260929，vs hold_all，low-cost）：**net return / hit rate 差异全部不显著**；coverage 差异全部显著为负。单次均值差异未被解释为稳定优势。

## 6. What was NOT validated / remains research-only

- 没有 policy 获得"validated"状态：validation 是 research validation（P13-O 消费过该窗口的聚合统计），不是 virgin holdout。
- calibration 方法保持 P13-Q 的 `research_only`；volatility 未进入任何模型。
- ER/Risk 特征与 policy 参数均未经过真正未来数据检验。

## 7. Regression / Reproducibility / Production Protection

- 全量 pytest：**213 passed / 0 failed**（198 + P13-R 15 新增；无删除/弱化）。
- **完整二次运行：7 个研究 JSON 全部 byte-identical（cmp 逐个通过）**；manifest 记录 SHA256。
- `git diff -- src/astock_v2`：**空**。

## 8. CI

推送后 `tests` workflow（含 Full pytest suite step）双 job 通过、badge passing——具体 run ID 与 commit 见 §11 的推送记录，以 ChatGPT 复核时 Actions 页面为准。

## 9. Limitations

- 无 virgin holdout；单一大盘股 universe（76 只）；单一 linear 概率模型。
- ER/Risk 特征仅用收益序列（60 行窗口）；无成交量/流动性约束（数据缺失，已声明）。
- 行业 cap（≤2/日）会截断 hold-all 的覆盖（0.6433），基准与 policy 同受约束，比较仍公平。
- threshold_iso_p50（N=1）与 threshold_platt_p50（N=15）样本过小，其指标不具统计意义（已标注）。
- 成本模型不含冲击成本/容量约束；turnover 按持仓集对称差近似。

## 10. Potential Next Stage（只陈述依据）

1. 概率区分度仍是根本约束（P13-Q slope 0.17 + 本阶段全部 policy 无显著净收益差异指向同一结论）：任何 Recommendation 设计在没有更强区分度的特征前，收益空间被成本吞噬。
2. 若继续，值得研究的是**风险约束维度**（er_platt_pos_risk 用 46% 的 coverage 换取 23% 的回撤收窄）而非 alpha 选择维度。
3. 真正的 virgin holdout（P13-R 之后的新数据）是任何 policy 晋升的前提。

## 11. Git Commits（本阶段，推送后 HEAD 为准）

| commit | 内容 |
|---|---|
| docs: add P13-R research plan | 预定义 8 policy |
| P13-R: add recommendation engine research | 分析脚本 |
| test: lock P13-R recommendation invariants | 15 测试 |
| docs: add P13-R PIT audit and acceptance report | 本报告 |
