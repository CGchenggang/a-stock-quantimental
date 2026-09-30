# P14-C Acceptance Report — Data Quality / Reconciliation / Source Health

- 日期：2026-09-30
- 基线：`84021d6`（P14-B 验收终点）
- 文档：`docs/P14C_RESEARCH_PLAN.md`、`docs/P14C_QUALITY_AUDIT.md`
- 产物：`data/industry/p14c/`（quality_report.json、source_health.json、completeness.json、reconciliation.json、manifest.json；双次运行 byte-identical）
- 状态：**implementation complete; awaiting independent acceptance**——PASS 由外部验收判定。

## 1. Implementation

- `src/astock_v2/information/quality.py`（新增）：missingness 六类分类、timestamp quality（malformed/时区/顺序违规/语义不确定三类结果）、revision integrity（gap/duplicate revision/same-revision-different-payload/available_time regression——只报告不删除）、PIT quality（完全委托 P14-A）、freshness quality（UPPERCASE 报告键）、per-record quality decision（ADMISSIBLE/ADMISSIBLE_WITH_WARNING/REJECTED/UNRESOLVED + quality_reasons[]，PIT 委托 P14-A）。
- `src/astock_v2/information/reconciliation.py`（新增）：`ReconciliationPolicy`（policy_id/policy_version/absolute_tolerance/relative_tolerance）+ `reconcile`（分组确定性、双值/difference/relative_difference/sources 全保留、不裁决）+ `reconcile_pair`。
- `src/astock_v2/information/source_health.py`（新增）：从可观测 ingestion 证据 deterministic 聚合 OK/DEGRADED/STALE/EMPTY/ERROR/UNRESOLVED，无 ML、理由全记录。
- `scripts/run_p14c_quality_audit.py`（新增）：10 个 deterministic fixture（覆盖 handoff §20 全部异常类型）全链路 audit，5 个 JSON 产物。

## 2. Production Code 边界（§27）

`git diff 84021d6..HEAD -- src/astock_v2` = **空**（P14-C 全部为新增 tests/scripts/docs；quality 模块位于既有 `information/` 包内的新文件，未修改任何 P14-A/B 语义）。无 factor/policy/calibration/recommendation mutation。

## 3. P13-U / P13-Q / P13-R 保护

- virgin 边界常量未动（`research_boundary.py` 零 diff）。
- P13-Q/P13-R 入口 `assert_research_zone` fail-fast 回归测试保持通过。
- Quality audit 全部 fixture 日期 < 2026-09-23（research zone）；无 virgin 数据消费。

## 4. Known Limitations

- reconciliation tolerance 默认 strict equality；真实 source 间的 tolerance 需要在未来以冻结 policy 显式引入（本阶段 fixture 不需要）。
- source health 的 coverage 度量基于 fixture attempted/accepted；76-stock universe 的逐股 coverage 由 P13 阶段覆盖。
- timestamp 顺序检查仅在 source contract 声明时可报 VIOLATION，否则 UNKNOWN——这是按 §7 的保守选择。
- `freshness_quality` 报告键为大写规范化；P14-A 层仍返回小写状态（单一事实来源不变）。

## 5. Reproducibility / CI

- `data/industry/p14c/` 双次全新运行 5 个 JSON 全部 byte-identical（append-only raw store 的对比需清理输出目录后进行——audit 累积是设计行为）。
- 推送后以 GitHub API 核验 run → job → step（pytest / p13m / Full pytest suite），run ID 记录于下方 Git Commits 更新（以 Actions 页面为准）。

## 6. Git Commits（本阶段）

| commit | 内容 |
|---|---|
| feat: add P14-C quality/reconciliation/source health layer | quality.py + reconciliation.py + source_health.py |
| test: add P14-C quality/reconciliation/source health tests | 23 项 |
| docs: add P14-C research plan, quality audit and acceptance report | 三份文档 |

**implementation complete; awaiting independent acceptance**——P14-C 完成 ≠ P14 整体 PASS。
