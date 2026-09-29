# P13-Q Research Plan — Probability / Calibration Model

- 日期：2026-09-29
- 前置：P13-M/N/O/P 均已由 ChatGPT 验收 PASS。
- 性质：**研究/验证层**。`src/astock_v2/**` 零改动；不把 volatility 加入任何模型；不修改 label/PIT/协议。

## 1. Research Question

当前 production baseline logistic 输出的 raw probability 是否具有足够好的 OOS calibration，可以作为后续 Recommendation Engine 的概率输入？

继承事实：volatility 的 `validation_status = candidate`，本阶段不进入任何模型；industry_relative 双因子 `rejected_for_alpha`；production factor list 不变。

## 2. Protocol（未改动）

train=252 / test=20 / step=20 / gap=1；76-stock universe；当前 PIT/label/SW1 membership。概率全部来自 P13-O audit（`data/industry/p13o/oos_predictions_76.json` baseline variant 的 94,760 行）——**零重跑 production pipeline**。

## 3. Calibration Temporal Protocol（先验固定）

- **Calibration training window：discovery OOS = decision_time < 2025-01-01（65,795 行）**
- **Evaluation window：validation OOS = decision_time ≥ 2025-01-01（28,965 行）**
- 边界沿用 P13-P 的先验整年 split（在查看任何窗口内结果之前固定）。
- 层级：production logistic 训练（历史）→ walk-forward OOS 概率（2021–2026）→ calibration 拟合（仅 discovery OOS 的 (p,y) 对）→ **未来** validation OOS 上评估。calibration 拟合与评估零重叠（测试锁定）。
- **独立性限制（如实声明）**：P13-O 的发现消费了全部历史，validation 窗口在其聚合层面（年度 Brier/LogLoss 表）被观察过；calibration-specific 指标（ECE/slope/intercept、方法比较）为首次计算，但窗口本身不是 virgin holdout。因此本阶段所有 calibration method 的 `status = research_only`（先验规则，不依赖任何结果），不给 `validated_candidate`。

## 4. 固定参数（先验，不因结果调整）

- Probability bins：`[0.00, 0.05, 0.10, …, 0.95, 1.00]` 共 20 桶；左闭右开，最后桶闭。
- Calibration methods：Raw（基线）、Platt Scaling（logistic on logit p）、Isotonic Regression（PAVA）。Beta calibration 不在本阶段范围（记录为 limitation）。
- Bootstrap：symbol clusters，B=1000，seed=20260929；对象为 evaluation 窗口的 ΔBrier/ΔLogLoss/ΔECE（calibrator 固定后重抽评估行；单位=symbol）。
- Seed：20260929；所有 JSON `sort_keys` 输出；manifest 记录 SHA256。

## 5. 分析清单

| 任务 | 内容 | 产物（data/industry/p13q/） |
|---|---|---|
| T1 | Raw probability audit：n/positive_rate/mean_probability/mean_label/brier/log_loss/calibration_intercept/slope（y 对 logit(p) 的 OOS logistic 回归，纯 OOS 行）/ECE；全样本与时间窗 | `probability_audit.json` |
| T2 | Reliability curve：固定 20 bins，每桶 n/mean_p/observed_rate/difference | `calibration_curve.{json,md}` |
| T3 | Bucket stability：固定 buckets × {all, discovery, validation, 2022–2026}；每桶 N/mean_p/observed_rate/calibration_error/mean_next_return | `bucket_stability.json` |
| T4 | Temporal calibration stability：full/discovery/validation/年 × {N,Brier,LogLoss,ECE,intercept,slope,mean_p,positive_rate} | `temporal_stability.json` |
| T5/T6 | 方法比较（同 OOS 行集）：Raw/Platt/Isotonic × {Brier,LogLoss,ECE,slope,intercept} + Δ；discovery-fit → validation-evaluate | `calibration_methods.json` |
| 诊断 | 概率直方图（固定 bins）、entropy、extreme（<0.1 / >0.9）与 near-0.5（[0.45,0.55]）频率——描述性，不调整 | `probability_diagnostics.json` |
| Bootstrap | ΔBrier/ΔLogLoss/ΔECE point + 95% CI | 并入 `calibration_methods.json` |
| Registry | 每方法 method/role/training_period/evaluation_period/n_*/指标/status（枚举受限，本阶段全部 research_only） | `calibration_registry.json` |
| Manifest | 所有研究 JSON 的 filename/sha256/size | `manifest.json` |

统一入口：`scripts/run_p13q_analysis.py --audit <p13o json> all`。

## 6. 禁止与诚实条款

- 禁止用 evaluation label 训练/调参/选 bins/删股票/选年份。
- 若 calibration 改善 CI 包含 0 → 不得声称稳定改善。
- base-rate 检查：mean_p vs mean_label、intercept/slope 必须报告；存在偏差则明说。
- 全部方法本阶段 `research_only`；不产生 winner 排序；最终 PASS/FAIL 归 ChatGPT。

## 7. 已知数据事实（分析前探查，仅描述性）

- p 范围 0.0002–0.8931；99% 分位 0.575；64.1% 的行在 [0.45,0.55]；p>0.9 占 0%。
- mean_p 0.4681 vs positive_rate 0.4677（in-the-large 几乎无偏）。
- 固定 20 bins 下大量桶将接近空——如实保留 n，不合并。
