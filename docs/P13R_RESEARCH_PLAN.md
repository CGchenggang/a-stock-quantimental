# P13-R Research Plan — Recommendation Engine Research

- 日期：2026-09-29
- 前置：P13-M/N/O/P/Q 均已由 ChatGPT 验收 PASS（P13-Q 的 CI 阻塞项已在 `d8bea19` 修复）。
- 性质：**Research-only**。不接交易、不接 Agent/LLM/broker、不改 `src/astock_v2/**`、不宣布任何 policy 为"最优/validated production strategy"。

## 1. Research Questions

- R1 候选选择：probability threshold / top-k / cross-sectional percentile / expected-return 四类 policy family 的行为差异。
- R2 Calibration-aware：raw vs Platt vs Isotonic 概率驱动同一 selection 逻辑的差异（calibration 仍为 discovery 拟合、validation 评估）。
- R3 Expected return：`p_cal × upside + (1−p_cal) × downside` 的 PIT-safe 定义与 winsorization。
- R4 Risk：历史波动、下行波动、回撤与 decision_time 对齐。
- R5 Regime：BULL/NEUTRAL/BEAR 下各 policy 的 coverage/hit rate/收益/换手差异（复用 P13-O regime 定义，阈值不动）。
- R6 成本敏感性：zero / low / medium 三情景（参数全部写入 analysis_config.json）。
- R7 集中度与换手约束：每日最多推荐数、行业集中度上限、换手上限——作为 Decision Policy constraints 研究。

## 2. 反策略挖掘纪律（本阶段最高优先级）

**全部 8 个 policy 在本计划中预先定义，禁止在看到 validation 结果后新增/调参/删除。** 阈值不扫参：每个 family 用自然先验点（p≥0.5、k=3、top-20%、ER>0）。评估窗口一次性评估（research validation，2025-01-01 起，非 virgin holdout——P13-O/P 消费过历史的限制继续继承）。

## 3. Policy Registry（预定义，先验）

| policy_id | family | calibration | selection rule |
|---|---|---|---|
| hold_all | baseline | none | 持有全部 validation 行（基准） |
| threshold_raw_p50 | threshold | raw | p ≥ 0.50 |
| threshold_platt_p50 | threshold | platt | p_cal ≥ 0.50 |
| threshold_iso_p50 | threshold | isotonic | p_cal ≥ 0.50 |
| topk_platt_k3 | top-k | platt | 每决策日按 p_cal 取前 3 |
| percentile_platt_p80 | percentile | platt | 每决策日 p_cal ≥ 当日 80 分位 |
| er_platt_0 | expected-return | platt | expected_return > 0 |
| er_platt_pos_risk | expected-return+risk | platt | expected_return > 0 且历史波动 ≤ 当日 universe 中位数 |

约束（所有 policy 统一）：每决策日同 SW1 行业最多 2 个候选（industry concentration limit）；每 symbol 每日至多 1 席（自然约束）；不设绝对流动性约束（本地数据无成交量字段，记录为 limitation，以 volume_ratio>0 作粗 proxy 声明不足）。

## 4. Expected Return / Risk 定义（PIT-safe）

- 对 decision day t 的行：可用历史 = 同 symbol 中 `decision_time 日期 < t` 的已完结行（其 next_return 在 t 之前已实现）。窗口 60 行，不足时回退 discovery 全 universe 均值。
- winsorization：历史 next_return 在 1%/99% 分位截尾后再聚合（先验）。
- `upside` = 窗口内正 next_return 均值；`downside` = 负 next_return 均值（负值）；`expected_return = p_cal × upside + (1−p_cal) × downside`。
- Risk：同窗口 next_return 的 std（volatility）、负值 std（downside deviation）、累积路径 max drawdown、risk_score = volatility 标准化分位。

## 5. 成本情景（写入 analysis_config.json）

| scenario | commission | slippage |
|---|---|---|
| zero | 0 bp | 0 bp |
| low | 5 bp | 5 bp |
| medium | 10 bp | 10 bp |

`net_return = gross_return − (commission + slippage) × turnover`；turnover = 相邻决策日持仓集 |Δ|/持仓上限。

## 6. 评估与 Bootstrap

- 评估窗口：validation OOS（≥2025-01-01，28,965 行）。概率指标（Brier/LogLoss/slope/intercept/ECE）在选中子集上；selection 指标（coverage/hit rate/candidate count/stability）；return/risk/friction 指标按 §5。
- Bootstrap：symbol clusters，B=1000，seed=20260929。比较对象（先验）：各 policy vs `hold_all` 的 net return difference、hit-rate difference、Brier/LogLoss difference、coverage difference。
- Regime：复用 `run_p13o_analysis.RegimeLabeler`；年度/行业稳定性表。

## 7. 产物

`data/industry/p13r/`：`analysis_config.json`、`decision_policy_registry.json`、`recommendation_audit.json`（全量 ResearchRecommendationPacket，数据不进 git）、`policy_metrics.json`、`bootstrap_results.json`、`manifest.json`（SHA256+size）。Packet 字段按交接 §9（research-only，无任何交易指令）。

统一入口：`python scripts/run_p13r_analysis.py --audit <p13o json> --membership <csv> all`。

## 8. 测试

17 项（registry schema、policy 确定性、四 family、calibration isolation、PIT cutoff、未来信息拒绝、成本、集中度、换手、bootstrap、manifest、byte-identical、packet schema、production 未改）。全量 pytest 不回退（当前 198）。

## 9. 诚实条款

所有比较限定"在本研究窗口、当前 protocol 与成本假设下观察到"；禁用最优/最佳/高胜率/稳定盈利；validation 是 research validation，不是 production validation；完成后停止等待独立验收。
