# P13-U Research Plan — Virgin Holdout Data Accumulation & Integrity Gate

- 日期：2026-09-29
- 基线：`8dcd4eb`（P13-S 验收终点）
- 性质：**数据完整性/闸门阶段**。P13-U 不是模型验证、不是绩效评估、不是推荐生成——P13-U 保护 virgin holdout 边界。

## 1. 任务定位

P13-T 已判定 `NO TRUE VIRGIN HOLDOUT AVAILABLE`（research_end=2026-09-22，本地数据仅推进到 09-24）。P13-U 建立可审计、可重复的闸门机制，使 2026-09-23 之后的新数据在达到 P13-T 执行条件前保持 virgin、冻结、不可被研究流程消费。

P13-U 只回答：research_end 是什么、virgin_start 是什么、当前累计多少 virgin trading days、数据是否完整、是否曾被研究流程消费、P13-T 是否达到最低/推荐执行条件。

## 2. 冻结边界（先验，来自 P13-T 判定；测试锁定）

```text
RESEARCH_END = 2026-09-22   # 研究消费边界（常量，不随最新数据日期移动）
VIRGIN_START = 2026-09-23
MINIMUM_TRADING_DAYS = 20   # 1 个 walk-forward test 窗口
RECOMMENDED_TRADING_DAYS = 60
```

Gate 状态：`ACCUMULATING`（<20）/ `READY_MINIMUM`（≥20）/ `READY_RECOMMENDED`（≥60）/ `BLOCKED`（检出污染）。**P13-U 永不自动执行 P13-T**；`research_end` 禁止跟随 latest data date 前移（测试锁定 2026-10-10 场景）。

## 3. Virgin 判定与污染检测

- **consumed 集合的事实来源**：P13-O audit 的全部 decision_time（1358 天，2021-02-22→2026-09-22）——P13-P/Q/R/S 的全部行均由该 audit 派生，无缺口。
- **virgin trading day** = 本地 76-stock 价格数据中存在、日期 > research_end、且 ∉ consumed 的日期。无法证明未消费的日期不认定为 virgin（宁可少算）。
- **污染检测（两层）**：(a) consumed ∩ [virgin_start, ∞) 非空；(b) 扫描已知研究产物（P13-R recommendation_audit、P13-S research_reports）中任何 `decision_time`/`data_available_time` ≥ virgin_start。任一命中 → `contamination_detected=true`、`status=BLOCKED`，按 §23 停止等待人工决定。运行时读取行为无法从产物检测——文档如实声明此边界。

## 4. 范围与缺失报告

使用现有 76-stock universe（不扩、不删、不换）。对每个 virgin 交易日报告 `expected(76)/observed/missing_symbols`；缺失如实报告（实测 09-23/09-24 各缺 `000004`、`000016`），不因缺失修改 universe。

## 5. Research-zone guard

`assert_research_zone(dates)`：任何 `decision_time ≥ virgin_start` → `ValueError("VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE ...")` fail-fast。已接入 P13-Q（`run_p13q_analysis.main`）与 P13-R（`run_p13r_analysis.main`）两个研究入口（最小修改，语义零变化，回归测试锁定）；P13-S 输入同源受同一保护。未来 P13-T 评估必须显式绕过该 guard（知情豁免），当前不实现。

## 6. 产物（data/industry/p13u/）

`analysis_config.json`（配置+冻结常量）、`virgin_gate.json`（状态摘要）、`coverage.json`（逐日 expected/observed/missing）、`integrity_report.json`（research_end/virgin_start/latest/virgin_trading_days/missing/contamination/status）、`frozen_manifest.json`（边界 + universe/audit/两 registry/cost-risk config/P13-S schema/P13-T 判定的 SHA256）、`manifest.json`（输出 SHA256）。全部无动态时间戳。

## 7. 禁止（本阶段可执行性证明）

Gate 代码不含任何性能指标计算路径；输出结构断言锁定无 accuracy/brier/log_loss/hit_rate/recommendation/policy_metrics 字样；不生成任何 recommendation packet；不修改 policy/calibration/factor（生产 factor registry 快照测试 + gate 无 registry 写路径测试）。
