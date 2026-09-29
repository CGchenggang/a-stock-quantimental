# P14-A Acceptance Report — Information Contract & Provenance/PIT Infrastructure

- 日期：2026-09-29
- 基线：`38c4692`（P13-U 验收终点）
- 文档：`docs/P14A_RESEARCH_PLAN.md`、`docs/P14A_PIT_AUDIT.md`
- 产物：`data/industry/p14a/`（research_information_audit.json、manifest.json；双次运行 byte-identical）
- 状态：**implementation complete; awaiting independent acceptance**——PASS 由外部验收判定。

## 1. Implementation

- `src/astock_v2/research_boundary.py`（新增）：RESEARCH_END/VIRGIN_START/MINIMUM/RECOMMENDED + `assert_research_zone` 的单一事实来源；`scripts/run_p13u_gate.py` 改为从其导入，P13-U 的 18 个测试不回退。
- `src/astock_v2/information/`（新增 9 文件）：models（canonical record + 字段语义 docstring）、pit（inclusive 边界 + late-arriving + revision 可见性）、provenance（placeholder/unknown 拒绝）、freshness（显式 per-source policy，与 PIT 分离）、dedup（key=(source, source_id, revision)）、conflict（CONFLICT 只标注不裁决）、registry（7 source category + 9 个 fixture source）、normalization（确定性管线）、research_boundary_guard（`select_asof` 接入共享 virgin guard）。
- `scripts/run_p14a_info_audit.py`（新增）：deterministic fixture audit（7 raw → 6 research，1 dedup，1 conflict group 保留），双次运行 byte-identical。

## 2. Production Code 边界说明（§33 要求）

`git diff 77594d9a..HEAD -- src/astock_v2` 的内容 = **全部新增文件**（research_boundary.py + information/×9），无任何既有生产文件修改、无行为变化：

| 文件 | why | what | semantic impact | regression coverage |
|---|---|---|---|---|
| research_boundary.py | P13-U guard 常量需被 src 层信息模块与 scripts 层 gate 共用（单一事实来源，消除双份定义漂移风险） | 常量 + assert_research_zone 从 scripts 提升 | 无（值与行为逐位一致） | test_p13u_holdout_gate.py 18 项全过 |
| information/* | P14-A 交付物 | 统一信息契约基础设施 | 无（新模块，无既有调用方） | test_p14a_information.py 20 项 |

## 3. Tests

- 全量 pytest：**281 passed / 0 failed**（261 + 20 P14-A 新增；既有测试零删除零弱化）
- P14-A dedicated：**20 passed**（覆盖 §19 全部 24 项要求：schema、event/available 时间、PIT Case A/B、含等号边界、late-arriving、revision 边界与不可回填、provenance 拒绝、source identity registry、freshness policy 语义、dedup、冲突标注与不裁决、missing source 拒绝、确定性归一、byte-identity、future/P13-U/P13-Q/P13-R 保护、factor/policy/calibration 快照、无推荐生成）

## 4. Virgin Protection（§14）

P14 信息层 `select_asof` 调用与 P13-U gate 同一 `assert_research_zone`（常量同源测试锁定）：decision_time ≥ 2026-09-23 → fail-fast，含 2027 年极端 case。P13-Q/P13-R 入口 guard 保持激活（同一函数，`__module__` 检查放宽为允许定义处或 re-export 处）。research-zone fixture 日期均 < 2026-09-23。

## 5. Reproducibility

`data/industry/p14a/` 双次运行：`research_information_audit.json` 与 `manifest.json` **byte-identical**（cmp 通过）；无时间戳/随机字段。

## 6. Known Limitations

- 仅 fixture source；真实外部 adapter 未接入（按 §16 有意为之）。
- Conflict 处理只标注不裁决；source precedence policy 留待未来冻结。
- freshness 的 max_age 值为先验估计，未做历史敏感性校准。
- Beta calibration 类高级概率工具不属于本层。

## 7. CI

推送后以 GitHub API 核验 run → job → step（pytest / p13m / Full pytest suite，均应 success）——具体 run ID 于推送后核验补记（以 Actions 页面为准）。

## 8. Git Commits

| commit | 内容 |
|---|---|
| feat: add P14-A information contract and provenance/PIT infrastructure | src 基础设施 + fixture audit |
| test: add P14-A information layer tests | 20 项 |
| docs: add P14-A research plan, PIT audit and acceptance report | 三份文档 |

**implementation complete; awaiting independent acceptance**——P14-A 完成 ≠ P14 整体 PASS。
