# P13-T Research Plan — Frozen Temporal Holdout / Final Out-of-Sample Validation

- 日期：2026-09-29
- 基线：`8dcd4eb`（P13-S 验收终点 `9c33979` 之后的 docs-only commit）
- **判定：NO TRUE VIRGIN HOLDOUT AVAILABLE —— 按 P13-T 交接 §3/§19，本阶段在此停止，不实施 holdout 评估，不伪造。**

## 1. 什么应该发生（如果 holdout 存在）

对冻结的 P13-Q/P13-R 决策链（policy registry 8 个 policy、calibration 参数、cost 情景、universe 全部冻结，SHA256 入 frozen_manifest）在 `holdout_start > research_end` 的时间窗上做一次性评估，指标/判读规则先验写入本计划，不得事后修改。P13-T 只验证，不发现。

## 2. 边界审计（实测，2026-09-29）

| 项 | 实测值 | 来源 |
|---|---|---|
| OOS 决策期跨度 | 2021-02-22 → 2026-09-22（1358 个决策日） | `data/industry/p13o/oos_predictions_76.json` |
| P13-O 消费窗口 | 全部年度切片：2021(213d) / 2022(242d) / 2023(242d) / 2024(242d) / 2025(243d) / 2026(176d) —— **直至 2026-09-22** | 同上，按 decision_time 分年统计 |
| P13-Q calibration | 拟合 < 2025-01-01；评估 ≥ 2025-01-01（至 2026-09-22） | `data/industry/p13q/calibration_methods.json` |
| P13-R policy 评估 | validation 窗口 ≥ 2025-01-01（至 2026-09-22），8 个 policy 全部评估 | `data/industry/p13r/analysis_config.json` |
| 本地数据末端 | `cn_stock_daily` 最新 event_time = **2026-09-24T15:00+08:00**（91 只） | `data/clean/cn_stock_daily/` |

## 3. 判定论证

1. **research_end = 2026-09-22**：这是任何 discovery/validation 活动消费的最后一个 OOS 决策日（P13-O 年度切片与 P13-Q/P13-R validation 窗口共同覆盖 2021-02-22 → 2026-09-22，无缺口）。
2. **holdout_start 必须 > 2026-09-22**（交接 §3），即 ≥ 2026-09-23。
3. **本地数据止于 2026-09-24**：research_end 之后只有 **2 个交易日**（09-23、09-24）的原始行情，从未被任何阶段观察（严格 virgin），但：
   - walk-forward 协议（train=252 / test=20 / step=20 / gap=1）形成 **1 个 test 窗口需要 20 个连续决策日**；2 天 < 20 天，无法产生任何协议内 OOS 预测；
   - policy 评估所需样本（P13-R validation 用了 28,965 行）与 2 天 × 74 股 ≈ 148 行相差两个数量级；
   - 把已有窗口（≥2025-01-01）重标为 holdout 是伪造——P13-R 的 8 个 policy 刚在其上完成评估。
4. **结论：不存在既 virgin 又可评估的 holdout 窗口。** 任何"holdout 结果"都只能来自伪造或重复消费，两者均为交接所禁止。

## 4. 未来获得 virgin holdout 的确切条件

1. 数据采集推进到本地 OOS 末端之后 **≥ 20 个连续交易日**（形成 1 个 test 窗口；有统计意义的评估建议 ≥ 1 个季度，约 60 个决策日）；
2. 新窗口内 universe/PIT 语义/协议不变，且期间不得对该窗口做任何聚合观察；
3. 届时以当时 `data/industry/p13r/` 的冻结 registry SHA256 直接评估，无需重跑 discovery。

按此条件，最早可执行的 P13-T 时点约为 **2026 年 10 月下旬**（20 个交易日）或 **2027 年 1 月**（有统计意义）。

## 5. 本阶段交付

- 本判定文档（替代 holdout 实施记录）。
- **不产出**任何 holdout 指标、policy 结果、bootstrap 结果——避免伪造。
- P13-Q/P13-R 的 registry/audit 产物保持冻结原样，未做任何修改。

## 6. 状态

**STOPPED per task §3/§19: NO TRUE VIRGIN HOLDOUT AVAILABLE.** 待数据推进满足 §4 条件后，可按本计划 §1 的冻结协议实施 P13-T。
