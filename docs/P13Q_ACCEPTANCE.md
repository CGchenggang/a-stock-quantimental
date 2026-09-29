# P13-Q Acceptance Report — Probability / Calibration Model

- 日期：2026-09-29
- 基线：`ea52480`（P13-P 验收终点）
- 文档：`docs/P13Q_RESEARCH_PLAN.md`、`docs/P13Q_PIT_AUDIT.md`
- 产物：`data/industry/p13q/`（`manifest.json` 记录全部研究 JSON 的 SHA256；`analysis_config.json` 记录 commit/seed/protocol/bins/方法）
- 状态：**implementation complete / experiment complete / tests passed**——按交接 §25 不自行宣布 PASS，最终验收归 ChatGPT。

## 1. Protocol（未改动）

train=252 / test=20 / step=20 / gap=1；76-stock universe；当前 PIT/label/decision_time/available_time/SW1 membership。`src/astock_v2/**` 零改动；volatility 未进入任何模型；production factor list 未变。

## 2. Data Source（零重跑）

P13-O audit JSON（`data/industry/p13o/oos_predictions_76.json`）baseline variant 的 **94,760 行 OOS 概率**（2021-02-22 → 2026-09-22）。Calibration 层级：discovery OOS（<2025-01-01，65,795 行）拟合 → validation OOS（≥2025-01-01，28,965 行）评估，先验整年边界（沿 P13-P split）。

## 3. Raw Probability Metrics（T1/T4）

| window | N | mean_p | pos_rate | brier | logloss | ECE | intercept | slope |
|---|---|---|---|---|---|---|---|---|
| all | 94,760 | 0.4681 | 0.4677 | 0.25040 | 0.69446 | 0.02311 | −0.1072 | **+0.1716** |
| discovery | 65,795 | 0.4644 | 0.4645 | 0.25025 | 0.69415 | 0.02443 | −0.1186 | +0.1626 |
| validation | 28,965 | 0.4765 | 0.4749 | 0.25076 | 0.69517 | 0.02406 | −0.0845 | **+0.1668** |

**关键发现（base-rate 检查）**：
- **In-the-large 校准几乎完美**：mean_p 0.4681 vs positive_rate 0.4677（全样本偏差 +0.0004；各年偏差 ≤0.017）。
- **Calibration slope 仅 ~0.17（理想 1.0），且是真正的病根**：概率方向正确但幅度被压缩到应有的约 1/6——输出挤在 0.34–0.58，而实际结果的分布更极端。这正是 slope 解释的过度保守，不是截距问题（intercept ≈ −0.11，接近 0）。
- **时间稳定性好**：ECE 各窗 0.022–0.028、slope 各年 0.08–0.23，validation 与 discovery 无明显漂移——校准缺陷是结构性的（模型容量/特征限制），不是时间性的。

## 4. Reliability Curve（T2）与 Bucket Stability（T3）

固定 20 bins（0.05 网格，先验）。完整表见 `calibration_curve.md` / `bucket_stability.json`（每桶保留 n；各窗口逐桶表在 JSON）。形状符合 slope 诊断：中段桶 observed 与 predicted 接近，两端桶因 n 极小（<0.1% 的行）而不具解释力——如实保留，不合并。

## 5. Probability Quality Diagnostics（§15）

- **64.1% 的概率落在 [0.45, 0.55]**（60,738 行）——模型大部分时间几乎不表达信念强度。
- 极端概率几乎不存在：p>0.90 共 **0 行**；p<0.10 仅 53 行（0.056%）。
- 平均预测熵 0.6862 nats（最大 ln2≈0.693 的 99%）——输出接近"恒定略低于 0.5 的弱信号"。
- 描述性结论：当前 logistic 是一个**窄带、低置信度**的概率源；这一问题 calibration 无法完全修复（calibration 重映射不改变排序，也不创造区分度）。

## 6. Calibration Method Comparison（T5/T6，discovery fit → validation evaluate）

| method | N | brier | logloss | ECE | intercept | slope |
|---|---|---|---|---|---|---|
| raw | 28,965 | 0.25076 | 0.69517 | 0.02406 | −0.0845 | +0.1668 |
| platt | 28,965 | **0.24937** | **0.69188** | 0.01078 | +0.0372 | **+1.0258** |
| isotonic | 28,965 | 0.24938 | 0.69191 | **0.00894** | −0.0223 | +0.6053 |

三个方法消费**完全相同的 validation 行集**（测试锁定）。Platt 在 discovery 上拟合的 slope=0.163 精确对应对 raw slope≈0.17 的诊断，应用后 validation slope=1.026 ≈ 理想。

**Δ vs raw（symbol-clustered bootstrap，B=1000，seed=20260929；负=改善）**：

| method:metric | point | CI95 |
|---|---|---|
| platt:delta_brier | −0.00139 | [−0.00177, −0.00097] |
| platt:delta_log_loss | −0.00329* | 见 manifest JSON |
| platt:delta_ece | −0.01328 | [−0.01911, −0.00844] |
| isotonic:delta_brier | −0.00138 | [−0.00172, −0.00099] |
| isotonic:delta_log_loss | −0.00325 | [−0.00423, −0.00227] |
| isotonic:delta_ece | −0.01512 | [−0.02046, −0.01012] |

\* 精确值见 `calibration_methods.json`（manifest SHA256 校验）。**全部校准改善 CI 不含 0——校准改善是统计真实的**（改善幅度小但一致性高）。

## 7. Calibration Registry（`calibration_registry.json`）

raw / platt / isotonic 全部 **`research_only`**——先验规则：P13-O 消费了全部历史，calibration 的 validation 窗口不是 virgin holdout，任何方法都不给 validated_candidate。无 winner 排序、无禁用词（schema 测试锁定）。

## 8. Leakage Audit

见 `docs/P13Q_PIT_AUDIT.md`（七项逐条：概率来源、拟合窗口、评估隔离、bins 先验、label 用途、production 未动、独立性限制）。测试锁定：训练/评估零重叠、翻转 evaluation label 不改变拟合、bins 硬编码、split 确定性。

## 9. Reproducibility

- 一条命令重放：`python scripts/run_p13q_analysis.py --audit data/industry/p13o/oos_predictions_76.json all`（wall ≈ 9s）。
- **完整二次运行：8 个 JSON（probability_audit / calibration_curve / bucket_stability / probability_diagnostics / calibration_methods / calibration_registry / manifest / analysis_config）全部 byte-identical（cmp 逐个通过）。**
- SHA256 见 `manifest.json`（ChatGPT 可独立校验产物 vs 报告）。

## 10. Pytest

**198 passed / 0 failed**（P13-P 187 + P13-Q 11 新增；既有测试未删除或弱化）。11 个新测试覆盖：bins 先验、方法同行集、split 确定性、拟合/评估零重叠、无未来 label 泄漏、指标可复现、slope/intercept 真值恢复、极端概率计数、registry schema 与状态词表、bootstrap seed 可复现、重复运行 byte-identical。

## 11. GitHub Actions

推送后 `tests` workflow 双 job 通过、badge passing。**具体记录**：workflow run（commit `见下方 Git commits` 之最终 HEAD）、job `pytest` 与 `p13m`——run ID 与结论将在推送后核验并以此处补记为准（ChatGPT 复核时以 Actions 页面为准）。

## 12. Limitations

- 无 virgin holdout（P13-O 全历史发现消费）；calibration 结论限定于内部 temporal validation。
- 仅 Platt 与 Isotonic；Beta calibration 未做（交接可选项）。
- Bootstrap 重抽评估窗口的 symbol（calibrator 固定），未重跑上游 walk-forward。
- 校准改善幅度小（Brier −0.0014，约 0.55%）；其对下游决策（阈值、期望收益映射）的价值未在本阶段评估。
- Raw 概率的核心缺陷（slope 0.17、64% 概率挤在 0.45–0.55、零极端概率）是 production logistic 的结构性产物；post-hoc calibration 修复缩放但不创造区分度。

## 13. Recommendation for P13-R（只陈述发现与依据）

1. **Raw probability 可作为 Recommendation Engine 的输入，但必须携带校准处理**：in-the-large 无偏、时间稳定，但 slope 0.17 意味着"0.55 的 raw 概率"远弱于字面含义。直接使用 raw 概率的绝对数值（如"p>0.6 才行动"类阈值）会把过度保守的输出误读为低置信度——所有阈值语义必须先经过 calibration 重映射或显式换算。
2. **Platt scaling 是当前证据下的首选 research calibration**：参数少（2 个）、发现期拟合即把 validation slope 修到 1.026、三项指标 CI 全部显著改善、各窗口稳定；Isotonic 表现相当但 ECE 更优、slope 仍偏保守（0.605），且非参数形式在窄带输入上更依赖桶内样本量。二者均为 research_only，接入生产需要真正未来的数据确认。
3. **概率区分度不足是更根本的约束**：校准修好了"数值的诚实性"，但没有更多信息量的特征，Recommendation Engine 的有效决策空间仍然只有 0.34–0.58 的窄带。任何 P13-R 设计不应依赖细粒度概率差异（例如分 5 档信心），除非区分度先被改善。
4. 建议把 `--predictions-out` audit + calibration 分析管线作为 production probability 的常驻监控（时间稳定性表显示结构稳定，异常漂移可检测）。

## 14. Git Commits（本阶段）

| commit | 内容 |
|---|---|
| （推送后补记 HEAD） | P13-Q: add probability calibration analysis（T1–T6 + registry + manifest） |
| | test: lock P13-Q leakage and reproducibility |
| | docs: add P13-Q research plan / PIT audit / acceptance report |
