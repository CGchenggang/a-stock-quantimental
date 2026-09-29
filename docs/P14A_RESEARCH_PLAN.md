# P14-A Research Plan — Information Contract & Provenance/PIT Infrastructure

- 日期：2026-09-29
- 基线：`8dcd4eb`（P13-S/CI-closure 终点）
- 性质：**通用信息基础设施（infrastructure）**。不是 alpha research、不是 factor development、不是 recommendation development、不是 production strategy。本阶段不接入大量真实外部 API，以 deterministic fixtures 验证契约。

## 1. Scope

建立统一信息数据契约，使未来 A 股行情、公司公告、财报、宏观、海外市场、行业信息、市场状态、新闻/事件能进入统一的信息基础设施。本阶段解决的核心问题：

> 过去某个决策时点，研究层究竟当时能知道什么？

## 2. Information Contract

`RawInformationRecord`（14+ 必需/可选字段，语义见 `src/astock_v2/information/models.py` docstring）：

- `event_time`：事件实际发生/适用时间。**永不**用作 PIT 判断依据。
- `available_time`：市场参与者实际能获得该信息的时间。**唯一** PIT 判据：`available_time <= decision_time`（含等号）。
- `source` / `source_id`：来源 / 来源内的记录身份；共同构成去重键（与 revision 一起）。
- `entity_id` / `entity_type` / `symbol`：信息主体。
- `content` / `value`：文本或数值载体（至少其一）。
- `revision`：同 (source, source_id) 事实的单调修正计数；高 revision 配晚 available_time 是迟到修正，**不是回填**。
- `ingested_at`：入库时间，仅 provenance 记录，绝不用于 PIT/freshness。
- `quality_status`：OK / UNRESOLVED / INVALID；非 OK 不得进入 research layer。
- `freshness_policy_id`：显式引用 registry 中的 freshness policy。

## 3. PIT Contract

`is_admissible(record, decision_time)`：`available_time <= decision_time`（含等号）。handoff Case A/B 已用精确日期测试锁定。late-arriving（event < available）按 available_time 正常准入——事件早于可用时间不构成拒绝理由。

## 4. Freshness semantics（与 PIT 分离）

`freshness_status(record, decision_time, policies)`：age = decision_time − **available_time**，与 record 的 `freshness_policy_id` 指向的显式 policy 比较（max_age 先验定义于 registry）。无 policy id → `unknown`；policy id 未注册 → `missing_policy`。不用全局统一窗口。

## 5. Revision semantics

`visible_revisions(records, decision_time)`：每个 (source, source_id) 只暴露 available_time 已过的最大 revision；高 revision 永远不能改写其 available_time 之前的历史。

## 6. Provenance

`provenance_issues`：placeholder source（unknown 等）、缺 source_id、缺 ingested_at、UNRESOLVED/INVALID 均为 issue；有 issue 的记录被 `normalize` 显式拒绝（fail-fast，不静默洗白）。`to_research_record` 只接受 provenance-valid 记录。

## 7. Deduplication

Dedup key = `(source, source_id, revision)`（文档化）；幸存者按 canonical JSON 最小者确定性选择，输入顺序无关。

## 8. Conflict handling

同 (entity_id, entity_type, event_time, unit, currency) 且 ≥2 个来源给出 ≥2 个不同非空 value → 全组标 `CONFLICT`，全部保留 provenance。**不裁决**（无 highest/latest/average）——source precedence policy 尚不存在。同源不同 revision 是修正，不是冲突。

## 9. Source category registry

7 类：A_SHARE_MARKET / COMPANY / MACRO / OVERSEAS_MARKET / INDUSTRY / MARKET_STATE / PUBLIC_EVENT。9 个代表性 fixture source 已注册（cn_index_daily、cn_stock_quote、company_announcement、macro_pmi_cn、macro_cpi_cn、us_index_daily、industry_classification、market_state_feed、public_event_feed），每个绑定 freshness policy；未注册来源被 normalize 拒绝。真实 adapter 后续接入必须先注册。

## 10. Production boundary & virgin protection

- `src/astock_v2/` 仅新增：`research_boundary.py`（RESEARCH_END/VIRGIN_START/assert_research_zone 的**单一事实来源**，从 scripts/run_p13u_gate.py 提升——scripts 与 src 两层共用同一冻结常量）与 `information/` 模块。无任何既有生产文件修改；无新 factor/policy/calibration。
- Virgin protection：信息层 `select_asof` 直接调用 `assert_research_zone`——decision_time ≥ 2026-09-23 在 P14 层同样 fail-fast，无旁路。
- research-zone fixture 日期全部 < 2026-09-23。

## 11. Reproducibility

`scripts/run_p14a_info_audit.py` 全 deterministic（无时间戳/随机/顺序依赖）；双次运行 2 个 JSON byte-identical；manifest 记录输出 SHA256。
