# P14-A PIT Audit — Information Contract & Provenance/PIT Infrastructure

- 日期：2026-09-29
- 范围：`src/astock_v2/information/`（全部为新增通用基础设施）、`src/astock_v2/research_boundary.py`（新增，单一事实来源）、`scripts/run_p14a_info_audit.py`（新增）

## 1. 五个时间字段的语义与用途

| 字段 | 语义 | 用于 |
|---|---|---|
| `event_time` | 事件实际发生/适用时间 | 仅作为事实属性记录；**禁止**用于 PIT/freshness 判断 |
| `available_time` | 市场参与者首次可得时间 | PIT 判据（`available_time <= decision_time`，含等号）+ freshness 起点 |
| `decision_time` | 研究决策时点（调用方传入） | PIT 与 freshness 的对照时点 |
| `revision` | 同 (source, source_id) 事实的单调修正计数 | 决定同一事实的可见版本；不可回填 |
| `ingested_at` | 我方管线入库时间 | 仅 provenance 记录；不参与任何决策 |

## 2. 三个示例（均为测试锁定的事实）

### Example 1 — PIT 边界（handoff Case A/B，`test_pit_boundary_is_inclusive_and_uses_available_time_only`）

event_time=2026-01-01T09:00+08:00, available_time=2026-01-03T09:30+08:00：
- decision_time=2026-01-02T09:00+08:00 → **NOT ADMISSIBLE**
- decision_time=2026-01-03T09:30+08:00 → **ADMISSIBLE**（含等号）

### Example 2 — Late-arriving information（`test_late_arriving_information_is_admissible_by_available_time`）

event_time=2026-01-10, available_time=2026-01-12：event < available 不构成拒绝；decision 01-11 不可见、01-12 可见。PIT 判断只依据 available_time。

### Example 3 — Revision boundary（`test_revision_visibility_boundary`）

PMI rev0（available 02-01, value 50.1）与 rev1（available 02-15, value 50.3）：
- decision_time=2026-02-10 → 只能看到 rev0（50.1）
- decision_time=2026-02-15 → rev1（50.3）可见
- **禁止用最新 revision 回填过去**：rev1 在 02-15 之前的任何决策时点都不可见。

## 3. Freshness 与 PIT 的分离

PIT：`available_time <= decision_time`（准入问题，二值）。Freshness：`decision_time − available_time ≤ policy.max_age`（时效问题，按 source 的显式 policy；macro 35d / market 16h / announcement 72h / overseas 20h / industry 100d / event 7d）。两者使用不同的时间差（freshness 同样不含 event_time）。测试锁定：同一 age 在不同 policy 下可分别为 fresh/stale；无 policy id → unknown；未注册 policy id → missing_policy。

## 4. Dedup / Conflict 的确定性

- Dedup key=(source, source_id, revision)，幸存者=canonical JSON 最小；输入顺序无关（测试锁定）。
- Conflict 组=(entity_id, entity_type, event_time, unit, currency) 内 ≥2 来源 ≥2 个不同 value；只标注 CONFLICT 并保留全部 provenance，不裁决。同源不同 revision 是修正不是冲突；同值不同来源不是冲突。

## 5. Virgin holdout 保护（§14 最高优先级）

- 边界常量提升为 `src/astock_v2/research_boundary.py` 单一事实来源；`scripts/run_p13u_gate.py` 改为从其导入（P13-U 的 18 个测试全部通过——行为零变化，仅消除双份定义）。
- P14 信息层 `select_asof` 首行调用同一 `assert_research_zone`：decision_time ≥ 2026-09-23 → `ValueError("VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE ...")`。测试 `test_information_layer_rejects_virgin_decision_time`（含 2027 年极端 case）与 `test_virgin_guard_constant_shared_with_p13u`（三层常量同一性）锁定。
- 无任何绕过路径：信息层的所有准入都经由 `select_asof` 或显式传入 research-zone decision_time 的调用方。

## 6. Production boundary 说明（§33/§15 要求）

`git diff 77594d9a..HEAD -- src/astock_v2` 的全部内容为**新增文件**（无既有文件修改）：

| 文件 | 原因 | 行为变化 |
|---|---|---|
| `research_boundary.py`（新增） | 冻结边界此前定义在 scripts/run_p13u_gate.py；P14 信息层（src）与 P13-U（scripts）需要单一事实来源 | 无——常量值与 guard 行为与原实现逐位一致，P13-U 18 测试不回退 |
| `information/`×9（新增） | P14-A 交付物本身 | 无——新模块，未被任何既有生产代码引用 |

无 new production factor、无 factor weight、无 policy、无 calibration、无 recommendation logic。
