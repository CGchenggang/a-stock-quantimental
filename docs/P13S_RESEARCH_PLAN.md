# P13-S Research Plan — Research Agent / Research Report Generation Layer

- 日期：2026-09-29
- 前置：P13-M/N/O/P/Q/R 均已通过独立验收（P13-R 终点 `77594d9a…`，CI run 36543819808 全绿）。
- 性质：**Explanation / Reporting Layer（research-only）**。不修改 `src/astock_v2/**`、不修改 P13-R/P13-Q 任何逻辑、不接在线 LLM、不接交易。

## 1. 核心边界

```text
P13-R = Decision Layer（candidate/policy/probability/calibration/ER/risk/cost/regime/reason）
P13-S = Explanation / Reporting Layer（validation/organization/explanation/traceability/uncertainty/rendering）
```

**P13-S 可以解释 P13-R，但不能推翻 P13-R**：所有数值原样透传，不得重新预测、重新选股、二次校准、修改任何决策字段。

## 2. 输入（真实 schema 已确认）

P13-R Recommendation Packet（`data/industry/p13r/recommendation_audit.json`，8 policy 共 45,613 个），实际字段：

```text
symbol, decision_time, policy_id, calibration_method, raw_probability,
calibrated_probability, expected_return, risk_score, cost_scenario,
cost_adjusted_expected_return, market_regime, selection_reason,
risk_flags, data_available_time
```

已知事实：calibration_method ∈ {raw, platt, isotonic, none}；policy_id ∈ 8 个 registry policy；risk_flags 当前为 `[]`（passthrough 契约仍锁定）。

## 3. 架构

```text
packet → validate_packet() → build_report() → render_markdown() → report.md
                (确定性规则)      (deterministic object,   (纯模板；LLMRenderer
                                  report_id=sha256[:16])    接口预留, CI 不依赖)
```

- **Validation Layer**：必需字段存在性（缺失→`missing_data`）、freshness（`data_available_time` vs `decision_time`）、policy 已知性（不在 8 个 registry policy → `unknown_policy`）、raw/calibrated 方向一致性。
- **Deterministic Report Object**：固定 schema（`SCHEMA_VERSION="p13s-report-1"`），`report_id = sha256(json.dumps(packet, sort_keys=True) + schema_version)[:16]`；相同输入必然相同输出；`generated_at` 等运行时元数据分离，不进确定性 artifact。
- **Renderer**：`render_markdown` 纯模板（结构参照交接 §36 示意）；`LLMRenderer` 仅定义 protocol 骨架（输入=report object，禁止修改 packet），CI 一律 deterministic。
- **Manifest**：输入文件/输出文件 SHA256 + schema_version + configuration；无时间戳。

## 4. 确定性规则（先验定义，测试锁定，不得看结果后调整）

| 规则 | 定义 |
|---|---|
| freshness | `data_available_time <= decision_time` → `fresh`；`>` → `stale`；缺失 → `missing`；解析失败 → `unknown`。P13-R 中两者相等（保守截止）→ 正常为 fresh。不伪造更细粒度发布时间。 |
| missing_data | 14 个必需字段任一缺失/None |
| stale_data | freshness == `stale` |
| low_confidence | `calibration_method == "none"`（raw 概率未经校准；P13-Q 实测 slope≈0.17，字面概率强度不可信——确定性规则，非 LLM 判断） |
| contradictory_evidence | raw 与 calibrated 相对 0.5 的方向不一致（`raw>=0.5` XOR `calibrated>=0.5`）；**不静默裁决**，仅标记 |
| unknown_policy | `policy_id` 不在 P13-R registry 的 8 个已知 policy |

P13-R 的 `risk_flags` 原样保留；P13-S 自己的 validation 结论放独立字段 `p13s_validation_flags`，不混入。

## 5. Evidence Traceability（claim → field → packet → stage）

固定映射表（代码常量）：概率字段 ← packet ← `p13q_calibration`/`p13r_packet`；expected_return/cost ← `p13r_expected_return_model`；risk ← `p13r_risk_features`；market_regime ← `p13o_regime_labeler`；selection_reason ← `p13r_policy_registry`；data_available_time ← `p13r_pit_audit`。报告中无不可追溯的 AI opinion。

## 6. 输出

- `data/industry/p13s/report_schema.json`：schema 定义。
- `data/industry/p13s/golden_reports/`：8 类 fixture（正常 / missing data / stale / low confidence / contradictory / unknown policy / risk flags / calibration×4）——由确定性 packet 生成（data/industry 不入 git；测试在 tmp_path 重建比对）。
- `data/industry/p13s/manifest.json`：输入/输出 SHA256（动态时间戳不进 manifest）。
- 入口：`python scripts/run_p13s_report.py --packets <p13r audit> [--policy <id>] --out-dir <dir>`。

## 7. 测试（对应交接 §25 的 18 项）

`tests/test_p13s_research_agent.py`：正常生成、schema、字段透传、calibration 对应、ER/cost-ER 不混淆、policy_id/reason 保留、risk_flags 不丢、availability 不伪造、missing/stale/unknown policy/contradictory 显式标记、calibration×4 渲染、byte-identical、future-row immunity、无交易执行词汇、renderer 不可变 packet。

## 8. 边界重申

无交易执行能力、无 broker、无 live trading、无新因子、无 P13-R policy 修改、无在线 LLM 依赖。完成后提交 `implementation complete; awaiting independent acceptance`，PASS 由外部验收判定。
