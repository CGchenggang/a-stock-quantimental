# P13-S PIT Audit — Research Report Generation Layer

- 日期：2026-09-29
- 范围：P13-S 全部分析（`scripts/run_p13s_report.py`，产物 `data/industry/p13s/`）

## 1. 输入数据边界

唯一输入是 P13-R recommendation packet（`data/industry/p13r/recommendation_audit.json`，14 字段真实 schema）。P13-S 不读取任何行情、新闻、模型输出或其他数据源；不重新计算概率、收益、风险或 regime。

## 2. decision_time

packet 原样透传到 report 的 `decision_time` 字段，是报告语义上的"研究决策时点"（16:00 +08:00 保守截止）。P13-S 不修改、不重新解释该时点。

## 3. data_available_time

原样透传。P13-R 中该字段等于 decision_time（保守截止声明：packet 全部输入在决策边界可得）。P13-S 不伪造任何更细粒度的 source publication time。

## 4. Freshness rule

固定规则（`freshness_of`）：`data_available_time <= decision_time` → fresh；`>` → stale；缺失 → missing；解析失败 → unknown。P13-R 语义下正常 packet 均为 fresh；stale/missing/unknown 是对异常 packet 的显式标记（golden fixtures 覆盖），不会静默通过。

## 5. Future-row immunity

报告是 packet 的纯函数（`build_report`/`render_markdown` 无任何全局状态、无时间读取、无跨行依赖）。`test_future_row_immunity` 证明：向批处理加入任何未来行，过去 decision_time 的报告逐字节不变；`test_packet_pit_availability_ignores_future_rows`（P13-R 层）与 `test_renderer_does_not_modify_packet`（本层）共同锁定输入不被污染。

## 6. Report generation boundary

`build_report` 只读 packet（测试锁定 renderer 与 build 均不修改输入 dict）；唯一新增内容是确定性 validation 结论（freshness/uncertainty/p13s_validation_flags）、固定 evidence 映射表与 `research_only=true`。这些新增项的规则先验定义于 `docs/P13S_RESEARCH_PLAN.md`，由测试锁定，不依赖运行时输入或 LLM。

## 7. 自然语言生成为何不引入未来信息

`render_markdown` 是纯模板函数：每一行输出都由 report object 的固定字段格式化而来（None → `MISSING (insufficient_evidence)`），没有自由文本生成、没有外部知识、没有时间读取。LLM renderer 仅保留接口骨架（未实现、CI 不实例化）；即使未来接入，其契约也限定为"重组/解释已有字段"，且任何输出仍需通过同一组禁词与追溯测试。

## 8. 结论

P13-S 不使用 future recommendation、future label 或 future market data 影响任何历史报告；报告对 packet 的关系是纯函数，对未来输入的关系是免疫的。
