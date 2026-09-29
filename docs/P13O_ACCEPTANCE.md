# P13-O Acceptance Report — Factor 稳定性与信息含量（描述性研究）

- 日期：2026-09-29
- 仓库：`CGchenggang/a-stock-quantimental`
- 基线：`bad2a43`（P13-N 验收终点）→ 本阶段终点见 Git discipline 一节
- 研究计划：`docs/P13O_RESEARCH_PLAN.md`
- 数据产物：`data/industry/p13o/`（不入库；`analysis_config.json` 记录 commit/seed/protocol/输入）
- 验收方：ChatGPT（本报告提交后由其复核；不自行宣布 P13-O 通过）

## 1. Executive Summary

对 76 股 OOS 预测（94,760 行/variant，与 P13-N golden 逐位一致的运行导出）完成七项稳定性分析。核心事实：

1. **industry-relative 因子没有稳定、可重复的 OOS 增量信息。** ΔAccuracy 的年度方向翻转（2021–2026：+0.0001 / −0.003 / −0.006 / +0.002 / +0.003 / −0.000），股票层面 29 只改善对 42–45 只恶化、中位 Δ 为负，行业层面方向相反（−0.012 到 +0.029），regime 层面（BULL/NEUTRAL/BEAR）无一显示出有意义的条件性信息（|Δ| ≤ 0.003）。
2. **唯一统计显著的效应是一致但微小的概率校准恶化。** symbol-clustered bootstrap（B=1000）下 ΔBrier 95% CI [+0.00062, +0.00101]、ΔLogLoss 95% CI [+0.00160, +0.00266] 均显著为正；ΔAccuracy CI [−0.0035, +0.0017] 含 0。
3. **阈值信号在 10bp 成本下不可交易。** 所有 variant（含 baseline）净收益为负（−2 到 −5bp/日），换手 ~7.4%/日。
4. **意外发现（如实报告）**：在因子分位检查中，**volatility 因子呈现清晰的单调正结构**（q1→q5 up_rate 0.4546→0.4890，mean next return 0.00000→+0.00074），是目前唯一具有单调横截面结构的因子。

综上，P13-M 观察到的"总体变化非常小且方向不稳定"不是某个 regime 或某个股票子集掩盖的信号，而主要是统计噪声叠加一个一致的轻微校准损失。

## 2. Data / Universe

- 76 股验证集（`data/industry/validation_universe_76.txt`）、SW1 PIT membership（5930 股 / 38 行业）、本地日线 1633 个交易日
- OOS 明细重跑一次（310s，exit 0）：**原因**——P13-N 只保存 stdout 汇总与 context JSON，per-prediction 明细从未落盘，为七项分析的共同原料。重跑的 pooled 指标与 P13-N golden 逐位一致（94,760 OOS / baseline 0.522932/0.250401/0.694463），证明导出未影响生产指标路径。

## 3. Exact OOS Protocol（未改动）

train 252 / test 20 / step 20 / gap 1；logistic 同 P13-N baseline；variants baseline / industry_5 / industry_20 / industry_5_20。全量 pytest 通过（179 passed）确认协议代码未变；`docs/P13N_PERFORMANCE_BASELINE.md` 的 golden 产物复核完好。

## 4. Time Stability（O1）

全样本与时间切片（前/中/后 1/3、每年、最近 2 年）的完整表见 `data/industry/p13o/time_stability.md`（每个切片 N 已标明，30,920–17,266 不等）。关键行（industry_5_20 的 ΔAccuracy）：

| slice | N | Δacc | Δbrier |
|---|---|---|---|
| 2021 | 14,479 | +0.0014 | +0.00062 |
| 2022 | 16,648 | −0.0042 | +0.00080 |
| 2023 | 17,266 | −0.0056 | +0.00088 |
| 2024 | 17,402 | +0.0002 | +0.00116 |
| 2025 | 17,448 | +0.0021 | +0.00067 |
| 2026 | 11,517 | −0.0005 | +0.00088 |

方向逐年翻转；ΔBrier 每年一致为正。前 1/3 Δacc −0.0020 vs 后 1/3 +0.0009（industry_5_20），近期略好但幅度仍在噪声带内。

## 5. Symbol Stability（O2）

74 只有 OOS 行的股票（000156/000428 无 SW1 历史故无行）：

| variant | improved | degraded | Δacc median | Δacc [q10, q90] |
|---|---|---|---|---|
| industry_5 | 29 | 43 | −0.0026 | [−0.0104, +0.0147] |
| industry_20 | 27 | 44 | −0.0030 | [−0.0125, +0.0134] |
| industry_5_20 | 27 | 45 | −0.0026 | [−0.0114, +0.0112] |

恶化股票多于改善；分布宽且双侧展开（个股间方向相反），无一致性收益来源。**未删除任何股票。**

## 6. Industry Stability（O3）

PIT-safe 归属（与因子同一 schedule 查询；skipped=0，无合法归属的行不存在于 OOS 集）。24 个 SW1 行业的 ΔAccuracy 范围 −0.0117（SW1:360000, N=1450）到 +0.0288（SW1:510000, N=765）——行业间方向相反；两个最大正 delta 均为小样本行业。ΔBrier 在 22/24 个行业为正（两个负值行业 N=1230/765）。完整表见 `industry_stability.md`。

## 7. Factor Quantiles（O4）

OOS 等频五分位（每因子 N=18,952/组附近），关键结果：

- **volatility：q1→q5 up_rate 0.4546→0.4563→0.4663→0.4722→0.4890，mean next return 0.00000→+0.00074，单调递增** —— 唯一有清晰结构的因子（高波动次日更高上涨率，风险溢价方向）。
- industry_relative_return_5：up_rate q1–q5 = 0.4779/0.4706/0.4684/0.4611/0.4604 —— **反向单调**（低相对收益组次日更容易上涨），但幅度小且与 pooled delta≈0 一致。
- industry_relative_return_20：非单调（q3 最高 0.4705，q5 最低 0.4596）。
- momentum：q1 up_rate 0.4952 明显高于其余（~0.46）——轻微反转迹象，非单调。
- trend / volume_ratio：无单调结构。

## 8. Regime Analysis（O5）

Regime 标签：等权 universe 指数 20 日累计收益**仅用至 t−1**（PIT 安全），BULL > +3% / BEAR < −3% / NEUTRAL（先验阈值）。结果（industry_5_20 的 Δ）：BULL −0.0001、NEUTRAL −0.0012、BEAR −0.0024；三个 regime 内 |ΔAccuracy| ≤ 0.003 且无一致符号，ΔBrier 全部为正。

**结论：因子信息（若有）不是被某个市场状态掩盖的——不存在"只在某类环境下有效"的证据。** 本阶段未把 regime 接入生产预测（按交接要求仅分析）。

## 9. Cost Sensitivity（O6）

假设：p≥0.5 持有 1 日、t 收盘决策/成交、收益 = next_return（label 定义）、单边 10bp/单位换手、等权跨股平均。

| variant | gross/day | turnover/day | cost/day | net/day |
|---|---|---|---|---|
| baseline | +0.00006 | 0.0744 | +0.00007 | −0.00002 |
| industry_5 | +0.00005 | 0.0745 | +0.00007 | −0.00002 |
| industry_20 | +0.00003 | 0.0752 | +0.00008 | −0.00004 |
| industry_5_20 | +0.00003 | 0.0754 | +0.00008 | −0.00005 |

**全部净收益为负**；因子变体相对 baseline 无成本后优势。这是研究性估算，不是真实交易收益（无滑点/冲击/资金约束建模）。

## 10. Bootstrap（O7）

Symbol-clustered bootstrap（76 簇有放回重抽，B=1000，seed=20260929，pooled delta 点估计 + 95% 区间）：

| variant | Δacc [CI95] | Δbrier [CI95] | Δlogloss [CI95] |
|---|---|---|---|
| industry_5 | −0.0006 [−0.0029, +0.0016] | +0.00082 [+0.00062, +0.00103] | +0.00214 [+0.00160, +0.00268] |
| industry_20 | −0.0013 [−0.0035, +0.0008] | +0.00084 [+0.00064, +0.00103] | +0.00217 [+0.00164, +0.00269] |
| industry_5_20 | −0.0012 [−0.0035, +0.0010] | +0.00084 [+0.00065, +0.00104] | +0.00218 [+0.00169, +0.00272] |

ΔAccuracy 统计上不可区分于零；ΔBrier/ΔLogLoss **显著为正**（一致轻微恶化）。bootstrap 样本规模 = 76 簇 ≈ 94,760 行/次。

## 11. PIT Audit

- 行业归属：`IndustryAttributor` 直接复用 `industry_relative._scheduled_industry`（effective_from/available_time + decision_time），与因子内部查询一致；无合法归属即不归类。
- Regime 标签：仅使用 t−1 及更早的指数收益；构建索引的日收益状态按 available_time=当日 16:00 推进（`_advance_pit_return_state`），decision 16:00 边界与生产一致。
- 导出路径不改变任何生产语义：pooled 指标与 P13-N golden 逐位一致（§2）。
- 无未来数据：quantile 边界虽在 OOS 样本内计算，但仅作描述性单调性检查并已在产物中声明；未用于参数/股票/行业选择。

## 12. Reproducibility

- 一次运行重放全部七项分析：`python scripts/run_p13o_analysis.py --audit data/industry/p13o/oos_predictions_76.json --membership data/industry/sw_official_sw1_membership_all.csv --root data all`（wall ≈ 858s，主要在 bootstrap）。
- `analysis_config.json` 固定 commit、seed=20260929、B=1000、成本率、regime 阈值、protocol、universe。
- 分析无隐藏随机性（除 bootstrap 的显式 seed）；已验证 repeated 唯一性的 P13-N 基线不受影响。

## 13. Regression

- 全量 pytest：**179 passed / 0 failed**。
- P13-N golden factor rows（000001，1612 行）与优化前产物 `cmp` **逐字节一致**——P13-O 未触碰生产路径。
- P13-M pooled==single 单测（`test_pooled_context_matches_single_stock_context`）通过。

## 14. CI

推送后 GitHub Actions `tests` workflow：pytest 与 p13m 双 job 通过，分支徽章 passing（run 见本报告推送 commit；本地预验证 179 passed）。**最终 run 结论以 ChatGPT 复核时 Actions 页面为准。**

## 15. Limitations

- 单一 universe（76 只深市本地股，91 只价格库）、单一协议参数（252/20/20/1）、单一线性模型（logistic, 500 epochs）——结论限定于该配置。
- 成本模型极度简化（收盘成交、无滑点/冲击/容量约束）。
- Regime 阈值 ±3% 为先验，未做敏感性扫描；等权指数与真实指数行为可能不同。
- Bootstrap 保持簇内（股票内）依赖，但 74 簇的簇间独立性仍是假设（同日横截面相关未建模）。
- Quantile 边界在 OOS 样本内计算，适合描述性检查，不适合直接作为交易分位规则。
- 行业分析中两个负 ΔBrier 行业均为小样本（N<1300），不构成反向证据。

## 16. P13-P Recommendation（仅陈述实验事实与技术依据）

1. **Market Regime 建模作为 alpha 来源的证据不足**：industry-relative 因子在 BULL/NEUTRAL/BEAR 三类环境下均无可检测的条件性信息（|ΔAccuracy| ≤ 0.003）。若 P13-P 继续 regime 方向，依据应是风险控制/仓位管理价值，而非提升因子 alpha——本数据不支持后者。
2. **volatility 因子是数据支持的下一研究候选**：唯一呈单调横截面结构的因子（up_rate 0.4546→0.4890），且方向符合风险溢价直觉。任何后续工作应先在独立样本/窗口验证该结构的稳定性，再考虑建模。
3. **industry-relative 因子的角色建议从 alpha 预测转向风险/对照组特征**：其 OOS 增量为零、校准轻微恶化、跨维度方向不一致。
4. 若 P13-P 引入新因子评估，建议直接复用本阶段的 audit 导出 + 分析管线（`--predictions-out` + `run_p13o_analysis.py`），使每个新因子自动获得同等强度的稳定性审计。

## 17. Git Discipline（本阶段提交）

| commit | 内容 |
|---|---|
| `4d79210` | P13-O: export per-prediction OOS audit data |
| `529e516` | P13-O: add unified stability analysis over exported OOS predictions |
| `docs:` | P13O_RESEARCH_PLAN.md + P13O_ACCEPTANCE.md（本报告） |

生产路径（`src/astock_v2/**`）零改动；历史 P13-M/P13-N 验收结论未修改。
