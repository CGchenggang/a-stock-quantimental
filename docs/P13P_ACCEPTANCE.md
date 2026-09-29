# P13-P Acceptance Report — Independent Factor Validation & Candidate Selection

- 日期：2026-09-29
- 基线：`46331af`（P13-O 验收终点）
- 研究计划：`docs/P13P_RESEARCH_PLAN.md`
- 产物：`data/industry/p13p/`（`analysis_config.json` 记录 commit/seed/split/protocol/因子清单）
- 状态：**implementation complete / experiment complete / tests passed**——按交接 §17 不自行宣布 PASS，最终验收归 ChatGPT。

## 1. Research Question

现有 production 因子中，哪些具有足够稳定的独立 OOS 信息可以进入下一阶段 Probability/Calibration Model？重点验证 P13-O 发现的唯一单调结构因子 `volatility`——P13-O 的发现不构成其进入生产的理由。

## 2. Exact Protocol（未改动）

train=252 / test=20 / step=20 / gap=1；logistic 同 baseline；76-stock universe；当前 PIT/label/decision_time/available_time/SW1 membership。评估器复用 `run_local_industry_relative_oos.py::evaluate`（逐 symbol 运行后 pooling，与生产 benchmark 完全一致）。**`src/astock_v2/**` 零改动。**

## 3. Discovery / Validation Periods

- OOS 范围 2021-02-22 → 2026-09-22（1358 个决策日）。
- **Discovery：decision_time < 2025-01-01（65,795 行）；Validation：≥ 2025-01-01（28,965 行）**。边界为整年先验边界（自然年 + 与 P13-O 年度切片协议兼容），固定于查看任何窗口内结果之前。
- Quintile 边界仅在 discovery 样本上计算并应用到所有窗口（测试锁定）。
- **Leakage 声明（如实）**：P13-O 的发现使用了全部历史，validation 窗口在其聚合层面（年度 ΔAccuracy 表）被观察过；因此不存在 virgin holdout。这是 `validation_status` 无法高于 `candidate` 的结构性原因。

## 4. Factor List

momentum、volatility、trend、volume_ratio、industry_relative_return_5、industry_relative_return_20（全部 production 因子；未创造新因子）。

## 5. Volatility Stability（T2，核心验证）

Quintile 边界来自 discovery 样本，应用到全部切片：

| slice | N | Q1 up | Q5 up | spread_up | spread_ret |
|---|---|---|---|---|---|
| all | 94,760 | 0.4542 | 0.4889 | **+0.0347** | +0.00075 |
| discovery | 65,795 | 0.4434 | 0.4959 | **+0.0525** | +0.00167 |
| **validation** | 28,965 | 0.4753 | 0.4727 | **−0.0026** | **−0.00128** |
| year_2022 | 16,648 | 0.4439 | 0.4818 | +0.0380 | +0.00180 |
| year_2023 | 17,266 | 0.4433 | 0.4734 | +0.0301 | −0.00037 |
| year_2024 | 17,402 | 0.4167 | 0.5286 | **+0.1118** | +0.00452 |
| year_2025 | 17,448 | 0.4788 | 0.4833 | +0.0045 | −0.00036 |
| year_2026 | 11,517 | 0.4643 | 0.4644 | +0.0002 | −0.00151 |

- **内部 validation 窗口符号翻转**（+0.0525 → −0.0026 up-rate spread；return spread 同样翻转）。年度看结构集中在 2022–2024（2024 最强 +0.1118），2025–2026 归零/转负。
- 全样本 symbol-clustered bootstrap：spread_up +0.0347 CI95 [+0.0236, +0.0459]、spread_ret +0.00075 CI95 [+0.00014, +0.00136] —— 统计显著，但**由 2022–2024 主导**；显著性反映的是历史结构存在过，不是它在 validation 期仍然存在。
- 个股 spread 分布（74 只）：mean +0.031 / median +0.026 / q10 −0.031 / q90 +0.106——个股间方向不一致。
- Regime（复用 P13-O 的 PIT-safe 标签，阈值未动）：BULL/NEUTRAL/BEAR 的 spread 分别 +0.0405 / +0.0334 / +0.0294——结构不专属某个市场状态，但也没有任何一个 regime 内在 validation 期得到确认。

**方向反转已如实报告，未做选择性隐藏。**

## 6. Single-Factor Results（T1）

6 个因子逐一 baseline+factor vs baseline（同 OOS 行集，aligned=yes）：

| factor | Δacc | Δbrier | Δlogloss |
|---|---|---|---|
| momentum | −0.0006 | +0.00002 | +0.00005 |
| volatility | −0.0002 | +0.00005 | +0.00017 |
| trend | −0.0000 | −0.00000 | +0.00000 |
| volume_ratio | −0.0007 | +0.00020 | +0.00057 |
| industry_relative_return_5 | +0.0001 | +0.00000 | +0.00000 |
| industry_relative_return_20 | −0.0007 | +0.00002 | +0.00003 |

**没有任何单因子提供有意义的模型增量；ΔBrier/ΔLogLoss 全部非负**（加因子从不改善概率校准）。

## 7. Incremental Results（T3，Model A–E）

| model | full acc | full Δacc vs A | validation Δacc | full Δbrier vs A |
|---|---|---|---|---|
| A baseline | 0.5229 | — | — | — |
| B +volatility | 0.5227 | −0.0002 | −0.0001 | +0.00005 |
| C +ir5 | 0.5230 | +0.0001 | +0.0001 | +0.00000 |
| D +ir20 | 0.5222 | −0.0007 | −0.0009 | +0.00002 |
| E +vol+ir5+ir20 | 0.5227 | −0.0002 | −0.0003 | +0.00009 |

B-vs-A 的 symbol-clustered bootstrap（B=1000，seed=20260929）：ΔAccuracy −0.00019 CI [−0.00085, +0.00047]（含 0）；ΔBrier +0.00005 [+0.00003, +0.00007] 与 ΔLogLoss +0.00018 [+0.00008, +0.00034] **显著为正（恶化）**。

**结论：volatility 不提供 baseline 之外的独立 OOS 信息；加上它校准反而统计显著地轻微变差。** 这与 T2 的横截面结构并不矛盾——单调分位结构存在过（2022–2024），但它（a）不持续到 validation 期，（b）不足以转化为 logistic 模型内的预测增益。

## 8. Redundancy Analysis（T4）

Rows=114,611，missingness 全部为 0（6 因子在全部 factor rows 上都有值）。volatility 与其余因子相关性低：momentum +0.203（Pearson）/ +0.121（Spearman）、trend +0.071、volume_ratio +0.042、ir5 +0.019、ir20 +0.150。**volatility 的失败不是冗余造成的——它携带的是低相关信息，只是这些信息没有稳定 OOS 增量。** 诊断性高相关：momentum×trend +0.838（记录在案，不做删除）。

## 9. Bootstrap（汇总）

| 检验 | 单位 | B/seed | 结果 |
|---|---|---|---|
| volatility Q5−Q1 up-rate spread（全样本） | symbol | 1000 / 20260929 | +0.0347 [+0.0236, +0.0459]（显著但被 2022–2024 主导） |
| volatility Q5−Q1 return spread（全样本） | symbol | 同上 | +0.00075 [+0.00014, +0.00136] |
| Model B−A ΔAccuracy | symbol | 同上 | −0.00019 [−0.00085, +0.00047]（含 0） |
| Model B−A ΔBrier | symbol | 同上 | +0.00005 [+0.00003, +0.00007]（显著恶化） |
| Model B−A ΔLogLoss | symbol | 同上 | +0.00018 [+0.00008, +0.00034]（显著恶化） |

## 10. Candidate Registry（`data/industry/p13p/factor_candidates.json`）

| factor | validation_status | 依据 |
|---|---|---|
| volatility | **candidate** | 发现期结构真实存在；内部 validation 翻转 + 模型增量为零 + 校准恶化 → 不得高于 candidate（registry 内附 insufficiency 说明） |
| momentum / trend / volume_ratio | context_only | 已在 Model A 内；单因子 audit 无增量声明 |
| industry_relative_return_5 / _20 | rejected_for_alpha | P13-O 无稳定增量 + P13-P 同行集确认 |

枚举仅使用交接 §8 的六个允许值；禁用词（best/strongest/winner/guaranteed/high_probability）未出现（schema 测试锁定）。

## 11. PIT Audit

- volatility 因子值来自 P13-O audit（生产 `volatility_factor` 的输出），其输入行的 available_time ≤ decision_time（16:00 边界），lookback 窗口只含过去收盘——P13-N 的 PIT 回归测试继续覆盖。
- label（next_return）只进入评估，不进入因子计算。
- Split 按决策时间划分（测试锁定：边界行归 validation、无重叠、覆盖完整）。
- Quintile 边界仅来自 discovery 样本（测试锁定：validation 值域完全在 discovery 范围外时不得移动边界）。
- validation 数据不参与任何因子选择/阈值/参数决定（本阶段唯一被"选择"的是 registry 的 status 措辞，规则先验固定于研究计划）。

## 12. Reproducibility

- 一次命令重放全部产物：`python scripts/run_p13p_analysis.py --audit data/industry/p13o/oos_predictions_76.json --membership data/industry/sw_official_sw1_membership_all.csv --root data all`（wall ≈ 960s）。
- `analysis_config.json` 固定 commit/seed/split_date/bootstrap_rounds/protocol/universe/因子清单/模型清单。
- 全量真实数据重跑一次，五个核心 JSON **byte-identical**（cmp 通过，见 §14 CI 前验证记录）。
- 测试锁定的确定性：bootstrap seed、quintile 边界、split 边界、字节级重跑（合成数据）。

## 13. Pytest

- 新增 `tests/test_p13p_analysis.py` 8 个测试：OOS 行对齐、quintile 可复现、split 确定性与 PIT 边界、bootstrap seed 可复现、registry schema 与状态词表、discovery-only 边界（泄漏控制）、build_rows 顺序、重复分析 byte-identical。
- 全量：**187 passed / 0 failed**（179 既有 + 8 新增），未删除或弱化任何既有测试。

## 14. GitHub Actions

推送后 `tests` workflow 双 job 通过、badge passing（具体 run 结论以 ChatGPT 复核时 Actions 页面为准）。推送前本地已完成：全量 pytest 187 passed + 复现性 byte 对比（单因子 audit / volatility / incremental / redundancy / registry 五个 JSON 全部 IDENTICAL）。

## 15. Limitations

- 无 virgin holdout（P13-O 发现阶段消费了全部历史）；validation 是内部一致性检查。
- 单一 universe（76 只深市股）、单一协议参数、单一模型族（logistic 500 epochs）。
- Quintile 边界为 OOS 内等频切分（discovery 定界），描述性。
- Bootstrap 保持簇内依赖；74 簇间同日横截面相关未建模。
- Regime 标签沿用 P13-O 先验阈值（±3%、等权指数），未做敏感性。
- 000156/000428 无 SW1 membership，无 OOS 行，不参与 delta 统计（bootstrap 已跳过空行集）。

## 16. Next-Stage Recommendation（只陈述发现与依据）

1. **volatility 不满足进入 Probability/Calibration Model 的门槛**：模型增量 CI 含 0、校准 CI 显著恶化、结构在内部 validation 期翻转。建议保持 `candidate`，仅在未来出现真正独立（P13-O 之后）的样本时重新评估。
2. industry-relative 双因子的 `rejected_for_alpha` 状态经同行集复核确认；其作为风险/对照组特征的价值未在本阶段评估。
3. 若 P13-Q 继续，可考虑：扩大 universe/时间以获得真正的 virgin holdout；或将验证层（本阶段脚本 + 测试）作为任何新因子候选的标准准入管线。
4. 生产预测路径本阶段零改动，无需回滚或迁移。
