# P13-Q PIT Audit — Probability / Calibration

- 日期：2026-09-29
- 范围：P13-Q 全部分析（`scripts/run_p13q_analysis.py`，产物 `data/industry/p13q/`）

## 1. Probability 只来自当时可获得的数据

全部被分析的概率来自 P13-O audit JSON 的 baseline variant 行，它们由生产 walk-forward（252/20/20/1）生成：每个 test 行的 logistic 训练集只包含时间上更早的行（`walk_forward_windows` 保证 train_end + gap ≤ test_start），因子输入按 available_time ≤ decision_time 的 PIT 语义准入。P13-Q 未重新训练任何模型，未触碰 `src/astock_v2/**`（提交历史可查）。

## 2. Calibration training 不使用未来 label

Platt 与 Isotonic 的拟合输入只有 `decision_time < 2025-01-01` 的 discovery OOS 行的 (p, y) 对（65,795 对）。测试 `test_no_future_label_leakage_in_calibration_fit` 证明：翻转全部 evaluation 行的 label 后重新拟合，拟合参数逐位不变——拟合函数在结构上不可能消费 fit 窗口之外的数据。

## 3. Evaluation window 未参与 calibration fitting

calibration 拟合行集与评估行集按 `SPLIT_DATE = 2025-01-01` 严格互补且不相交；测试 `test_calibration_training_and_evaluation_do_not_overlap` 锁定时间集合的 disjoint 性，`test_temporal_split_reproducible_and_disjoint` 锁定确定性与覆盖完整性。评估窗口行（28,965 行）从未进入任何拟合。

## 4. Bins 不由未来结果决定

20 个概率桶 `[0.00, 0.05, …, 0.95, 1.00]` 固定于 `docs/P13Q_RESEARCH_PLAN.md`（先验 0.05 网格），与任何 OOS 结果无关；测试 `test_fixed_probability_bins_are_the_prior_grid` 锁定网格与左闭右开/末桶闭合语义。桶边界不含任何拟合参数。

## 5. Label 的合法用途

label 仅用于（a）T1/T4 各窗口的 observed_rate/Brier/LogLoss/ECE 统计（对该窗口全体 OOS 行的描述性统计），（b）discovery 窗口内的 calibration 拟合（历史窗口，合法），（c）bootstrap 的评估窗口重抽样统计（评估行为，非训练）。label 从未进入任何 production 路径或跨窗口拟合。

## 6. Production probability 未被修改

本阶段唯一改动的生产仓库文件是 `scripts/run_p13q_analysis.py`（新增研究脚本）与 `tests/test_p13q_calibration.py`（新增测试）。`src/astock_v2/**` 无 diff（git 可查）；P13-N golden factor rows 与 P13-M/N 的 pooled 指标未被重新生成或覆盖。calibration 方法（Platt/Isotonic）仅存在于研究产物中，未被接入 Recommendation Engine / Agent / live probability。

## 7. 独立性限制（重申）

validation 窗口（2025-01-01 起）曾被 P13-O 的年度聚合表在聚合层面观察过，不是 virgin holdout；calibration-specific 指标与方法比较为首次计算。因此 `calibration_registry.json` 中全部方法 status = research_only（先验规则），不给 validated_candidate。
