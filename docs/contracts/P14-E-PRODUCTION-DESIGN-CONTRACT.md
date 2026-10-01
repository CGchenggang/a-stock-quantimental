# P14-E Production Implementation Contract — Evidence / Provenance / Bundle Runtime

> STATUS: DRAFT — P14-E-004 — awaiting independent contract acceptance
>
> **P14-E Production Implementation is NOT AUTHORIZED** until this contract
> passes independent acceptance.
>
> 修订历史：
> v1.0: P14-E-004 初版——将已独立接受的 P14-E Contract v1.1 + Matrix v2
>       (FROZEN) + Golden Design + Harness/Golden (REPAIR-001) 语义冻结为
>       可实现、可机械验收的生产实现契约。
> v1.1: P14-E-004-REPAIR-001——reverse-trace 错误分类由误写的"五类"统一为
>       实际冻结的**四类**（§11：NOT_FOUND / AMBIGUOUS / IDENTITY_MISMATCH /
>       RAW_RECORD_CORRUPTED）；hash mismatch 在权威 RawStore 状态下与
>       NOT_FOUND 不可区分（同一检测条件与处理语义），不构成第五类。
>       语义范围无其他变化；待独立验收。
>
> Contract SHA-256（本文件冻结后计算）：
> 见 Acceptance Matrix 头部记录。

---

## 1. Purpose

把已接受的 P14-E 语义转化为生产实现蓝图：模块布局、数据模型、身份公式、
持久化、错误分类、确定性规则。生产实现必须逐条满足本契约，并且其可观测
行为（evidence_id / bundle_id / canonical serialization）必须与已接受的
Golden 引擎逐位一致——Golden 是语义验收权威，不是可搬进 src/ 的代码。

## 2. Authority（不重新定义）

| 层 | 权威 | 生产层义务 |
|----|------|-----------|
| P14-B | RawStore、ingestion_id、raw_payload_hash、DUPLICATE/RAW_MUTATION_DETECTED | 唯一 raw authority；不得建立第二份 |
| P14-A | visible_revisions 选择链、is_admissible、parse_boundary | 直接调用，不复制 |
| P14-C | 异常分类（SOURCE_ERROR 等） | 复用，不合并 |
| P14-D | run_query、exclusion 四字段、result_id | 直接消费 |
| P13-U | assert_research_zone、冻结边界 | 查询/bundle 入口守卫 |

## 3. Module Layout（P14E-P-001）

```text
src/astock_v2/information/evidence.py      Evidence + EvidenceBundle 模型
                                           与构造（本契约 §4-§9）
src/astock_v2/information/evidence_store.py 持久化（§10）
```

禁止其他 P14-E runtime 文件；`src/` 文件集不得引入第二 RawStore、第二
选择链或 query/选股语义。Golden 引擎（tests/contracts/p14e/golden/core.py）
是语义权威：生产实现的 evidence_id / bundle_id / canonical serialization
必须与其逐位一致（未来 Harness 用同输入对照断言）。

## 4. Identity Classes（P14E-P-002 / P14E-P-003 / P14E-P-004）

| 类别 | 字段 | 作用 |
|------|------|------|
| Evidence Identity（参与 evidence_id） | source, source_id, revision, event_time, available_time, adapter_version, raw_payload_hash, ingestion_id | "这条 Evidence 是什么" |
| Content Identity | raw_payload 的语义内容，仅以 raw_payload_hash 表示；payload 本体留在 P14-B | "原始内容是什么" |
| Provenance Identity（审计，不参与 evidence_id） | ingested_at | "何时进入本系统" |
| Ingestion Identity | ingestion_id = sha256(source \| source_id \| revision \| raw_payload_hash \| adapter_version)（P14-B 公式逐字继承） | "来自哪一次获取链" |

```text
evidence_id = sha256(canonical_json(8 个 Evidence Identity 字段))
```

canonical_json 规范：`json.dumps(sort_keys=True, ensure_ascii=False,
separators=(",", ":"))`；null 序列化为 `null`；Unicode 不转义；hash 算法
SHA-256。adapter_version 参与身份：同 payload 异 adapter_version → 不同
ingestion_id → 不同 evidence_id（与 P14-E §4.1 一致）。

## 5. ingested_at Semantics（P14E-P-005）

| 维度 | 结论 |
|------|------|
| identity field | 否（不参与 evidence_id） |
| provenance field | 是（审计必须携带） |
| visibility field | 否（P14E-P-006） |
| ordering field | 仅 canonical tiebreak 的比较文本内（P14-A canonical_json 含投影字段；不改可见性） |
| bundle identity field | 间接：bundle_id 覆盖 bundle 全部 canonical 内容，evidence 携带 audit-only ingested_at |

重复 ingestion attempt：P14-B 判 DUPLICATE → canonical stored record 不被
覆盖 → Evidence 使用最终 canonical stored record → evidence_id 不分叉 →
被拒绝的 duplicate attempt 不进入 stored record set，因此 bundle_id 不变。
bundle_id 变化的唯一途径是 stored record set（含其 ingested_at）本身变化。

## 6. PIT Semantics（P14E-P-006）

```text
visible ⇔ available_time <= as_of_time（含边界相等；P14-A is_admissible authority）
```

event_time / ingested_at / query 处理时间 / processing_time 一律不参与
可见性。冻结边界常量（P13-U authority，不得改变）：
`research_end = 2026-09-22`、`virgin_start = 2026-09-23`。
as_of >= virgin_start 时查询与 bundle 构造入口 fail-fast（P13-U）。
P13-T = STOPPED / NOT EXECUTED（生产实现不得访问真实 virgin holdout）；
P13-U = PROTECTED。所有测试 fixture 仅使用合成日期（研究区 2026-03 或
2099-01-01）。

## 7. Version / Restatement Provenance（P14E-P-007 / P14E-P-008）

选择链（继承 P14-D，不重新定义）：

```text
highest visible revision
→ earliest available_time on equal revision
→ smallest canonical_json on equal revision and availability
```

Evidence 携带 `selection_reason` ∈ {SELECTED_HIGHEST_REVISION,
SELECTED_EARLIEST_ON_REVISION_TIE, SELECTED_CANONICAL_TIEBREAK}；
candidate_trace 携带落选候选 ∈ {REJECTED_LOWER_REVISION,
REJECTED_REVISION_TIE_NOT_EARLIEST, REJECTED_CANONICAL_TIEBREAK}，每条
仅含 `{source, source_id, revision, available_time, raw_payload_hash,
ingested_at, rejection_reason}`。

**泄漏禁令（P14E-P-008）**：早于某 revision available_time 的 bundle 不得
包含该 revision 的 payload / raw_payload_hash / ingestion_id / Evidence
内容 / candidate_trace / 选择状态。post-as-of record 在 bundle 中的唯一
呈现是 P14-D exclusion 四字段 `{source, source_id,
reason=NOT_YET_AVAILABLE, available_time}`（OUTSIDE_AS_OF /
UNRESOLVED_AVAILABILITY 同理，枚举继承 P14-D）。
"知道存在未来不可用记录" ≠ "泄露未来 Evidence 内容"。

兼容性注记 N1（P14-B authority）：同键同 payload 异 available_time 的
候选在存储层按 DUPLICATE 折叠（保留首条）；选择链作用于 stored candidate
universe。N2：canonical tiebreak 对单一 RawStore 存储集不可达（同键异
payload 即 mutation），仅对跨存储集合并的记录集可达；Golden 引擎以直接
构造记录覆盖该分支。

## 8. Result ↔ Evidence Mapping（P14E-P-009）

映射键（冻结）：

```text
mapping_key = (source, source_record_id, revision, ingestion_id)
```

规则：result.records 与 bundle.evidence **一一对应**（同 mapping_key 集合
相等）；禁止 orphan evidence（无对应 result record）；禁止 result record
无 evidence；禁止一条 evidence 被多条 result record 引用。counts.evidence
== len(result.records)。bundle 携带 `result_id`（P14-D result 的
sha256）链接。

## 9. Evidence Bundle Model（P14E-P-010）

```text
EvidenceBundle:
    schema_version   "p14e-evidence-bundle-1"          参与 bundle_id
    query            规范回显（entity/information_type/as_of/source）  参与
    as_of            同 query.as_of                    参与
    result_id        P14-D result sha256               参与
    evidence[]       §4 Evidence 列表                  参与
    candidate_trace[] §7 落选候选                      参与
    exclusions[]     P14-D excluded 原样               参与
    counts           {evidence, candidates, exclusions, examined}  参与
    bundle_id        sha256(canonical_json(去除 bundle_id 的全部内容))  派生
```

排序键冻结：evidence[] 按 (source, source_id, revision)；candidate_trace[]
按 (source, source_id, revision, available_time, raw_payload_hash)；
exclusions[] 按 (source, source_id, reason)。bundle 内 evidence_id 唯一、
trace 键 (source, source_id, revision, available_time, raw_payload_hash)
唯一。诊断性字段（若有）不得进入 bundle_id 输入。

## 10. Persistence（P14E-P-013）

持久化**必需**（durable evidence artifact）：

```text
文件        evidence_bundles.jsonl（路径由调用方提供，P14-B RawStore 同模式）
格式        JSONL，每行一个完整 bundle（canonical serialization）
写入        append-only；单行原子（newline 终止的一行写入）；禁止就地修改
幂等        同 bundle_id 重复 append → 拒绝（返回 False），不产生第二行
reload      逐行重算 bundle_id 必须与存储值一致；且每条 Evidence 的
            (ingestion_id, raw_payload_hash) 必须经 reverse trace 解析回
            P14-B raw_records.jsonl 权威行；任一失败 fail-fast
```

## 11. Reverse Trace API（P14E-P-014）

```text
输入: Evidence（identity 字段）+ P14-B raw rows
输出: 恰匹配的 authoritative raw record
失败分类（不得合并为 NOT_FOUND）:
    REVERSE_TRACE_NOT_FOUND        零匹配
    REVERSE_TRACE_AMBIGUOUS        多行匹配（同一对 identity 出现多次）
    REVERSE_TRACE_IDENTITY_MISMATCH 唯一 hash 匹配但 source/source_id/revision/
                                   event_time/available_time 不等
    RAW_RECORD_CORRUPTED           raw 行无法解析 / 必备字段缺失
```

hash mismatch 表现为 NOT_FOUND（(ingestion_id, hash) 对无匹配行）；
identity mismatch 在唯一行匹配但字段不等时触发。

兼容性注记 N3：已接受的 Golden 引擎仅断言 reverse trace "raise"（不分类）；
本节将其细化为四类错误——这是细化而非语义变更，Golden 的既有断言
（任何不合法情形 raise）在细分类下依然全部成立。

## 12. Tamper / Mutation Matrix（P14E-P-015）

| Case | 篡改 | 检测点 | 结果 |
|------|------|--------|------|
| A | Evidence 内容 | bundle_id 重算不匹配 | 检出，reload fail-fast |
| B | ingestion_id | hash 完整性（若未重算 bundle_id）或 reverse trace NOT_FOUND（若重算） | 检出，fail-fast |
| C | raw_payload_hash | reverse trace NOT_FOUND | 检出，fail-fast |
| D | result/evidence mapping | mapping_key 集合不等 | 检出，验收失败 |
| E | as_of_time | bundle_id 变化（as_of 参与内容）→ 与 result_id 链接断裂 | 检出 |
| F | canonical ordering | 重算 canonical serialization 与存储字节不等 | 检出 |

构造期：同 (source, source_id, revision) 异 raw_payload_hash 的候选 →
构造 fail-fast（P14-B RAW_MUTATION_DETECTED 为权威检测者，生产层消费）。

## 13. Missing / Failure States（P14E-P-016 / P14E-P-017）

| 状态 | Bundle 语义 |
|------|------------|
| 正常 / EXPECTED_ABSENCE / UNEXPECTED_MISSING / SOURCE_EMPTY / SOURCE_ERROR / PARSE_FAILURE 类 | 正常构造（exclusions/evidence 如实呈现） |
| provenance 不完整 | 构造整体 fail-fast；无部分 bundle；无降级标记 bundle；无持久化 |
| 同键异 hash（mutation） | 构造 fail-fast |
| reverse trace 失败（reload） | reload fail-fast |

枚举不合并；P14-C/P14-D 分类为权威。空结果（无可见记录）是**合法 bundle**
（evidence=[], exclusions 如实），允许持久化。

## 14. Reproducibility Boundary（P14E-P-018）

相同 (query, as_of, records snapshot, contract version) → 相同 result_id、
evidence_id 集合、bundle、bundle_id。bundle 内禁止 runtime timestamp /
UUID / random / machine path / 环境相关顺序。外部实时行为（如远端源可用
性）不属于可保证范围。

## 15. Contract Versioning（P14E-P-020）

本契约版本 `P14-E Production Contract v1.1`；schema_version 字段
`p14e-evidence-bundle-1`。冻结后：文件内容变更（含任何字符）→ 新版本号 +
新 SHA-256 + 独立验收；不得以"同一契约"名义变更语义。bundle 的
`schema_version` 与本契约版本绑定。

## 16. Anti-Cheat / Scope（P14E-P-021 / P14E-P-022 / P14E-P-023）

- 禁止 fixture_mode / expected_result_override / golden_override /
  test_only / skip_validation / force_visible / force_hidden /
  running_under_test 分支；禁止以 fixture 名、golden id、环境变量改变行为。
- 禁止第二 RawStore authority、第二选择链、第二 query 语义。
- 公开 API 面仅限 evidence/bundle 构造、持久化、重载、核验；禁止
  scoring/ranking/recommendation/prediction/trading/portfolio/alpha。
- P14-E-003 Golden/Harness 是语义验收权威：生产实现不得修改 Golden；
  两者冲突时 STOP 并报告 DEPENDENCY_CONTRACT_CONFLICT。

## 17. Invariant Registry（P14E-P-001..P14E-P-023）

- **P14E-P-001**: 模块布局冻结（§3：evidence.py + evidence_store.py；
  文件集 pin 不得出现其他 P14-E runtime 文件）。
- **P14E-P-002**: evidence_id = sha256(canonical_json(8 Identity fields))，
  内容寻址、顺序/环境无关。
- **P14E-P-003**: 四类身份字段分类冻结（§4）；audit-only 字段不参与
  evidence_id。
- **P14E-P-004**: ingestion_id 继承 P14-B 公式逐字实现，不得有第二套。
- **P14E-P-005**: ingested_at 语义冻结（§5 表）；DUPLICATE → 不覆盖 →
  不分叉 → bundle_id 不因被拒 attempt 改变。
- **P14E-P-006**: PIT 可见性继承（available_time <= as_of 含边界）；
  event_time/ingested_at/处理时间不改可见性。
- **P14E-P-007**: 选择链与 selection_reason/rejection_reason 枚举冻结。
- **P14E-P-008**: candidate trace 四字段排除呈现；post-as-of 内容泄漏禁令。
- **P14E-P-009**: mapping_key 冻结；1:1 映射；无 orphan；counts 相等。
- **P14E-P-010**: bundle 模型与字段参与性冻结（§9）。
- **P14E-P-011**: canonical serialization 规范冻结（§4）。
- **P14E-P-012**: bundle_id 确定性；同逻辑输入同 ID；重复 evidence 折叠。
- **P14E-P-013**: 持久化语义冻结（§10：append-only/幂等/reload 双重校验）。
- **P14E-P-014**: reverse trace API 与四类错误分类冻结（§11）。
- **P14E-P-015**: tamper Cases A-F 检测矩阵冻结（§12）。
- **P14E-P-016**: missing/failure 状态的 bundle 语义冻结（§13）；枚举不合并。
- **P14E-P-017**: provenance 失败整体 fail-fast；无降级 bundle。
- **P14E-P-018**: 重放边界冻结（§14）。
- **P14E-P-019**: adapter_version 参与 ingestion identity 与 evidence
  identity；异 adapter_version → 异 evidence_id。
- **P14E-P-020**: 契约版本/冻结/变更规则冻结（§15）。
- **P14E-P-021**: 反作弊键与调用形态禁止；文件 pin。
- **P14E-P-022**: 公开 API 面仅限 evidence/bundle 构造、持久化、重载、
  核验；无决策语义。
- **P14E-P-023**: Golden 为语义验收权威；生产实现必须与 Golden 引擎的
  evidence_id/bundle_id/canonical serialization 逐位一致。
