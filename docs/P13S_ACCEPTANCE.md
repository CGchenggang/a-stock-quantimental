# P13-S Acceptance Report — Research Agent / Research Report Generation Layer

- 日期：2026-09-29
- 基线：`77594d9a…`（P13-R 验收终点）
- 文档：`docs/P13S_RESEARCH_PLAN.md`、`docs/P13S_PIT_AUDIT.md`
- 产物：`data/industry/p13s/`（report_schema.json、research_reports.json、reports_md/、golden_reports/×10、manifest.json）
- 状态：**implementation complete; awaiting independent acceptance**——PASS 由外部验收判定。

## 1. What was tested

以 P13-R 真实 packet（14 字段 schema，45,613 个中按 policy cap 取 316 个）为输入，实现三层 research-only 报告管线：

1. **Validation layer**：14 个必需字段存在性、freshness（fresh/stale/missing/unknown）、policy 已知性（8 个 registry policy）、raw/calibrated 方向一致性。
2. **Deterministic report object**：`SCHEMA_VERSION="p13s-report-1"`；`report_id = sha256(canonical packet + schema_version)[:16]`；全部数值原样透传；新增项仅为 validation 结论（`p13s_validation_flags` 独立字段，不混入 P13-R `risk_flags`）、固定 evidence 映射与 `research_only=true`；`generated_at` 不进确定性 artifact。
3. **Renderer**：`render_markdown` 纯模板（None → `MISSING (insufficient_evidence)`）；`LLMRenderer` 仅接口骨架（未实现，CI 不实例化）。

架构边界：P13-R = decision，P13-S = explanation/reporting；`src/astock_v2/**` 零改动。

## 2. What was discovered

- 真实 316 packet 上的 uncertainty 分布：`contradictory_evidence` 108、`low_confidence` 50（threshold_raw_p50 的 raw 行）——两类确定性规则在真实数据上大量触发，报告如实标记，不做裁决。
- 10 个 golden fixture（正常/missing/stale/low confidence/contradictory/unknown policy/risk flags/calibration×4）全部按预期生成。

## 3. What was NOT validated / remains research-only

- 报告是 research artifact，不是 order/execution/broker instruction（schema 与渲染文本双重声明，测试锁定禁词）。
- `low_confidence` 规则（calibration=="none"）基于 P13-Q 的 slope≈0.17 结论，属于确定性标注，不是新的风险模型。
- LLM renderer 未实现（接口预留）；在线 LLM 未接入。

## 4. Verification Results

| 项 | 结果 |
|---|---|
| 本地全量 pytest | **243 passed / 0 failed**（221 + 22 新增） |
| P13-S dedicated tests | **22 passed**（覆盖交接 §25 的 18 项要求 + freshness 表/evidence map/required-fields schema 3 项补充） |
| Reproducibility | **byte-identical = yes**（research_reports.json、manifest.json、10 个 golden fixture 双次运行 cmp 全过） |
| Future-row immunity | **pass**（`test_future_row_immunity` + P13-R 层 PIT 测试） |
| Production diff | `git diff 77594d9a..HEAD -- src/astock_v2` = **空** |
| Manifest | `data/industry/p13s/manifest.json`（显式输出文件集 + 输入 SHA256；确定性文件集，无时间戳） |

开发中由测试抓到并修复的实现问题：`write_manifest` 最初 rglob 整个输出目录，把非本脚本的文件（report_schema.json）卷进 outputs、且会受目录残留影响——改为显式收集本次生成的文件集，保证 manifest 确定性；`process_packets` 的一次静默替换失败（调用点更新了、函数体没更新）导致 KeyError——本会话已知坑的再次实例化。

## 5. CI

`tests.yml` 的 Full pytest suite step 保留；P13-S 测试文件被完整套件覆盖。推送后以 GitHub API 核验 run → job → step（pytest / p13m / Full pytest suite），具体 run ID 在推送后核验并记录于下方 Git Commits 同轮的报告更新中（以 Actions 页面为准）。

## 6. Known Limitations

- 报告渲染为纯文本模板，未接 LLM；`LLMRenderer` 是未实现的接口骨架。
- uncertainty 规则是保守的确定性标注：`low_confidence` 只覆盖 calibration=="none" 的情形；P13-Q 发现的窄带区分度问题（64% 概率在 [0.45,0.55]）未建模为 flag（避免引入新的阈值参数）。
- 报告不含 P13-R bootstrap 区间等聚合统计（packet 层无此字段；聚合解释属后续阶段）。
- golden fixtures 由构造 packet 生成（data/industry 不入 git；测试在 tmp_path 重建比对，不依赖 gitignore 文件）。

## 7. Git Commits（本阶段）

| commit | 内容 |
|---|---|
| docs: add P13-S research plan | 架构与先验规则 |
| feat: add P13-S research report layer | validation/report object/renderer/manifest |
| test: add P13-S research report tests | 22 项 |
| docs: add P13-S PIT audit and acceptance | 本报告 |

（最终 HEAD SHA 与 CI run ID 见推送后报告更新；P13-S 不自行宣布 PASS。）
