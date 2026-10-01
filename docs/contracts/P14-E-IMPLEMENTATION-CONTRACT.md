# P14-E Implementation Contract — Evidence Runtime / Store / Bundle / Trace

> STATUS: DRAFT — P14-E-005 — awaiting independent contract acceptance
>
> **P14-E Production Implementation is NOT AUTHORIZED.** 本契约指导未来实现；
> 在通过独立验收前不得写任何生产代码。
>
> 上游已接受权威：
> - P14-E-004 Production Contract **v1.1**（SHA-256
>   `8619873053dd29736ebd7f61c4c88edf4e9406ae2adb71d45a4a5a5f738ef6ff`），
>   经 PROJECT_STATUS 验收记录（commit `144b38f6f5ab11e4000ecabf2512aa0a1e422bb2`）
>   独立验收 PASS；其文件头部保留 draft-era 状态行，验收以 PROJECT_STATUS
>   记录为权威（与 P14-E Design Contract 惯例一致）。
> - P14-E Design Contract v1.1 / Matrix v2 (FROZEN) / Golden Design /
>   Harness+Golden（REPAIR-001）。
>
> 修订历史：
> v1.0: P14-E-005 初版——实现边界、运行时架构（六组件）、权威模型、
>       Evidence 身份继承、Bundle 生命周期七态、Reverse Trace 四类、
>       持久化规则、失败模型六层、API 接口语义、兼容性结论。

---

## 1. Purpose

P14-E-004 冻结了生产实现"必须满足什么"。本契约冻结"如何构建"：组件划分、
职责、生命周期状态机、接口语义、失败分层与持久化规则——全部不写代码，
只定义实现必须遵守的工程结构。

## 2. Implementation Boundary（P14E-I-001 / P14E-I-002）

### 2.1 Included

```text
Evidence object model 与 evidence_id 处理
Evidence Bundle 生命周期状态机
EvidenceStore 持久化
Reverse Trace 接口
Provenance/Audit 元数据处理
Validation 层
失败模型与错误分层
```

### 2.2 Excluded（永久出界）

```text
Alpha 计算 / 因子生成 / 交易推荐 / 组合决策
执行逻辑 / 券商接口 / 订单路由
LLM 选股 / 预测 / 信号
P13-T holdout 消费 / P13-U 边界修改
第二 RawStore / 第二选择链 / PIT 查询语义重定义
```

## 3. Authority Model（P14E-I-003）

```text
P14-B RawStore          raw evidence 唯一权威
        ↓ （只读）
P14-D PIT Query Layer   可见性与版本选择唯一权威
        ↓ （只读消费 result）
P14-E Evidence Runtime  evidence/bundle 构造、持久化、追溯
```

禁止：Evidence Runtime 修改 RawStore；重建历史状态；覆盖 PIT 查询结果；
引入平行权威。P14-D exclusion 的 reason 枚举
（NOT_YET_AVAILABLE / OUTSIDE_AS_OF / UNRESOLVED_AVAILABILITY）由运行时
原样携带，不合并、不重定义。

## 4. Runtime Architecture — 六组件（P14E-I-004..009）

每个组件以七元组冻结（Responsibility / Input / Output / Authority Source /
Failure Behavior / Persistence Requirement / Test Requirement）。

### C1 Evidence Runtime Layer — P14E-I-004

| 项 | 定义 |
|----|------|
| ID | CMP-EVIDENCE |
| Responsibility | 从 P14-B records + P14-D result 构造 Evidence（§5 身份）与 Evidence Bundle（§6 结构）；携带已接受的 selection/rejection 枚举（SELECTED_HIGHEST_REVISION / SELECTED_EARLIEST_ON_REVISION_TIE / SELECTED_CANONICAL_TIEBREAK / REJECTED_LOWER_REVISION / REJECTED_REVISION_TIE_NOT_EARLIEST / REJECTED_CANONICAL_TIEBREAK），不重定义 |
| Input | RawIngestRecord 列表、ResearchQuery、P14-D run_query result |
| Output | Evidence 对象、EvidenceBundle 对象（内存态） |
| Authority Source | P14-B identity 原语、P14-A 投影、P14-D result_id |
| Failure Behavior | mutation / provenance 不完整 → fail-fast（无部分产物） |
| Persistence | 无（内存构造；持久化归 C2） |
| Test Requirement | 与 Golden 引擎同输入逐位对照（evidence_id / canonical 序列化） |

### C2 EvidenceStore — P14E-I-005

| 项 | 定义 |
|----|------|
| ID | CMP-STORE |
| Responsibility | 冻结 bundle 的 append-only 持久化、幂等去重、带权威校验的重载 |
| Input | 冻结后的 EvidenceBundle；可选 P14-B raw rows（reload 校验） |
| Output | STORED / DUPLICATE-REJECTED；重载后的 bundle 列表 |
| Authority Source | 已接受的 JSONL 持久化语义（P14-E Design §12 / Production §10 冻结：append-only canonical JSONL——已有架构约束，不另选数据库） |
| Failure Behavior | 写失败 → 无部分状态；重载 hash 不匹配 / 权威解析失败 → fail-fast |
| Persistence | 是（本组件即持久化点） |
| Test Requirement | 写→重载→重算 bundle_id→权威回溯 全链；重复 append 拒绝；篡改负例 |

### C3 Evidence Bundle Manager — P14E-I-006

| 项 | 定义 |
|----|------|
| ID | CMP-MANAGER |
| Responsibility | 驱动 §6 生命周期状态机（CREATE→VALIDATE→FREEZE→STORE 及 QUERY/TRACE/AUDIT 编排） |
| Input | 生命周期命令 + 载荷 |
| Output | 状态迁移结果或迁移失败错误 |
| Authority Source | 本契约 §6 冻结的状态机 |
| Failure Behavior | 非法迁移 → 拒绝并产出 audit 记录；不产生部分迁移 |
| Persistence | 经 C2 间接 |
| Test Requirement | 全部合法迁移成功；全部非法迁移被拒 |

### C4 Reverse Trace Service — P14E-I-007

| 项 | 定义 |
|----|------|
| ID | CMP-TRACE |
| Responsibility | Evidence → P14-B 权威 raw record 的反向解析与分类错误 |
| Input | Evidence identity 字段（或 bundle_id / evidence_id 定位后的 identity） |
| Output | 恰匹配的权威 raw record；失败时四类错误之一 |
| Authority Source | P14-B raw_records.jsonl |
| Failure Behavior | 四类错误逐类抛出（§8），不合并、不静默 |
| Persistence | 无 |
| Test Requirement | 四类各一负例 + 成功路径；与 Golden G-001 篡改负例语义一致 |

### C5 Provenance/Audit Layer — P14E-I-008

| 项 | 定义 |
|----|------|
| ID | CMP-AUDIT |
| Responsibility | 生命周期迁移的 audit 元数据记录；audit-only 字段（ingested_at 等）的携带与呈现 |
| Input | 迁移事件、构造失败事件 |
| Output | append-only audit 记录流 |
| Authority Source | P14-E Type C / audit-only 字段分类（Production Contract §4） |
| Failure Behavior | audit 写失败 → 迁移失败（audit 与迁移同生命周期）；不得静默丢审计 |
| Persistence | 是（audit 流 append-only） |
| Test Requirement | 每次迁移/失败均有对应记录；记录内无 runtime 字段 |

### C6 Validation Layer — P14E-I-009

| 项 | 定义 |
|----|------|
| ID | CMP-VALIDATION |
| Responsibility | provenance 完整性、mapping 1:1、排序冻结、schema/枚举合法性校验 |
| Input | 构造期对象（bundle 草稿 / 冻结前 bundle） |
| Output | 校验通过或分类错误 |
| Authority Source | Production Contract §4/§7/§9 冻结规则 |
| Failure Behavior | 任一校验失败 → 对应失败层错误（§8），fail-fast |
| Persistence | 无 |
| Test Requirement | 每条冻结规则至少一正一负用例 |

## 5. Evidence Identity（P14E-I-010）

逐字继承已接受语义（Production Contract §4 / P14-E Design §8.3）：

```text
Evidence Identity（参与 evidence_id）:
    source, source_id, revision, event_time,
    available_time, adapter_version, raw_payload_hash, ingestion_id
evidence_id = sha256(canonical_json(8 Identity fields))
Content Identity: 仅以 raw_payload_hash 表示（payload 本体留在 P14-B）
Provenance/Audit-only: ingested_at —— 不参与 evidence_id（不可重新进入）
Ingestion Identity: ingestion_id = sha256(source | source_id | revision |
    raw_payload_hash | adapter_version) —— P14-B 公式，无第二套
```

## 6. Evidence Bundle Lifecycle（P14E-I-011..017）

状态机（QUERY/TRACE/AUDIT 为 STORED 态上的只读操作）：

```text
CREATE → VALIDATE → FREEZE → STORED ─┬→ QUERY
                                     ├→ TRACE
                                     └→ AUDIT
```

### 6.1 CREATE — P14E-I-011

```text
Allowed transition:   → VALIDATE
Forbidden transition: 直接 STORE / 直接 FREEZE / 对外可见
Required metadata:    query 规范回显、as_of、result_id、输入记录集快照身份
Failure mode:         mutation（同键异 hash）或 provenance 缺失 → fail-fast，
                      无 bundle 对象存活，C5 记录构造失败事件
```

### 6.2 VALIDATE — P14E-I-012

```text
Allowed transition:   → FREEZE（通过）/ 终止（失败）
Forbidden transition: 跳过校验直接 FREEZE/STORE；失败后继续迁移
Required metadata:    校验清单结果（完整性/1:1 映射/排序/枚举）
Failure mode:         分类错误 → C5 audit 记录 → 终止
```

### 6.3 FREEZE — P14E-I-013

```text
Allowed transition:   → STORE
Forbidden transition: 冻结后任何内容变更（变更即篡改，可检测）
Required metadata:    最终 canonical serialization 字节与最终 bundle_id
Failure mode:         冻结时重算 bundle_id 与构造期不一致 → identity failure
```

### 6.4 STORE — P14E-I-014

```text
Allowed transition:   → STORED（进入 QUERY/TRACE/AUDIT）
Forbidden transition: 覆盖写 / 就地修改 / 同 bundle_id 第二行
Required metadata:    存储位置身份、append 结果（STORED / DUPLICATE-REJECTED）
Failure mode:         存储失败 → 无部分状态；reload 校验失败 → fail-fast
```

### 6.5 QUERY — P14E-I-015

```text
Allowed transition:   只读；STORED → STORED
Forbidden transition: 任何状态变更；跨 as_of 重建
Required metadata:    查询身份（bundle_id 或 query identity）
Failure mode:         未找到 → 报告性错误（不篡改状态）
```

### 6.6 TRACE — P14E-I-016

```text
Allowed transition:   只读；对 STORED bundle 的每条 Evidence 执行
Forbidden transition: 绕过 C4 直接访问 raw；trace 失败后继续其他断言
Required metadata:    四类错误之一（失败时）或权威 raw record 定位（成功时）
Failure mode:         四类错误 → CMP-TRACE 逐类抛出（§8 trace failure 层）
```

### 6.7 AUDIT — P14E-I-017

```text
Allowed transition:   每个迁移/失败事件附加一条 audit 记录
Forbidden transition: 修改或删除既有 audit 记录；runtime 字段进入记录
Required metadata:    事件类型、迁移前后状态、失败层与错误类（如失败）
Failure mode:         audit 写失败 → 该迁移整体失败（同生命周期）
```

## 7. Reverse Trace Runtime（P14E-I-018）

FOUR-CLASS 冻结（禁止重新引入 HASH_MISMATCH 作为第五类；hash mismatch
表现为 NOT_FOUND——权威 RawStore 二元组查零匹配，与"行不存在"同检测条件
同处理）：

```text
REVERSE_TRACE_NOT_FOUND          零匹配
REVERSE_TRACE_AMBIGUOUS          多行匹配
REVERSE_TRACE_IDENTITY_MISMATCH  唯一 hash 匹配但五字段身份不等
RAW_RECORD_CORRUPTED             raw 行不可解析 / 必备字段缺失
```

输入/输出：`reverse_trace(evidence | bundle_id + evidence_id) → 权威 raw
record | 四类错误之一`。任何实现不得把四类合并为 NOT_FOUND 总类。

## 8. Persistence Contract（P14E-I-019）

已有架构约束（P14-E Design §12 / Production §10 冻结）优先：存储形态为
**append-only canonical JSONL**（`evidence_bundles.jsonl`），不另选
SQLite/PostgreSQL/MongoDB；更换存储形态必须先走 Contract Repair。

```text
What:      冻结后的完整 EvidenceBundle（canonical serialization 一行）
Where:     调用方提供的 JSONL 路径（与 P14-B 审计文件同模式）
Immutable: append-only；禁止就地修改既有行
Version:   bundle.schema_version = "p14e-evidence-bundle-1"（随 Production
           Contract v1.1 绑定）；格式变更 = 契约变更
Hash:      bundle_id = sha256(canonical_json(去除 bundle_id 的全部内容))
Recovery:  reload 逐行重算 bundle_id + 每 Evidence 经 C4 回溯 P14-B 权威行；
           任一失败 fail-fast
```

## 9. Failure Model（P14E-I-020 / P14E-I-021）

六层失败分类，每层必须具备 Detection / Response / Audit record 三元组：

| 层 | Detection | Response | Audit record |
|----|-----------|----------|--------------|
| Input validation failure | CREATE/VALIDATE 期 schema/字段/枚举检查 | 拒绝构造，无产物 | validation-failure 事件 |
| Authority violation | 写 RawStore / 重建历史 / 覆盖 PIT 结果的尝试 | 拒绝并抛出 | authority-violation 事件 |
| PIT violation | as_of >= virgin_start 守卫 / 可见性覆盖尝试 | 入口 fail-fast | boundary-violation 事件 |
| Identity failure | evidence_id/bundle_id 重算不一致；trace 身份不等 | fail-fast | identity-failure 事件 |
| Storage failure | 写/重载错误；重复 append 冲突 | 报告且无部分状态 | storage-failure 事件 |
| Trace failure | 四类错误逐一触发 | 分类错误抛出，无静默默认 | trace-failure 事件 |

禁止把六层归并为单一泛化错误；禁止吞错继续执行。

## 10. API / Interface Semantics（P14E-I-022）

仅语义，无实现：

```text
create_bundle(records, query)
    In:  RawIngestRecord 列表 + ResearchQuery
    Out: CREATE 态 bundle 草稿（含 bundle_id）
    Side effect: 无（内存）
    Authority limitation: 对输入只读；不触发持久化
    Failures: mutation；provenance incomplete（Input validation 层）

freeze_bundle(bundle)
    In:  VALIDATE 态 bundle
    Out: FROZEN 态 bundle（canonical 字节锁定）
    Side effect: 无
    Authority limitation: 不得变更内容
    Failures: 校验失败（VALIDATE 未通过）；identity 重算不一致

store_bundle(frozen, store_path)
    In:  FROZEN 态 bundle + 存储路径
    Out: STORED / DUPLICATE-REJECTED
    Side effect: append-only 一行写入（唯一允许的持久化副作用）
    Authority limitation: reload 校验必须引用 P14-B 权威
    Failures: Storage failure 层

query_evidence(bundle_id | query identity)
    In:  bundle 身份
    Out: STORED bundle（只读视图）
    Side effect: 无
    Authority limitation: 不得跨 as_of 重建；不得改状态
    Failures: not found（报告性）

reverse_trace(evidence)
    In:  Evidence identity 字段
    Out: 权威 raw record
    Side effect: 无
    Authority limitation: P14-B 为唯一解析目标
    Failures: 四类错误（Trace failure 层）

validate_bundle(bundle, result)
    In:  bundle + 对应 P14-D result
    Out: mapping/完整性判定
    Side effect: 无
    Authority limitation: 规则来自 Production Contract 冻结集
    Failures: mapping 闭合违反 / 完整性缺失
```

## 11. Compatibility（P14E-I-023 / P14E-I-024）

```text
P14-A: PASS（is_admissible/visible_revisions/parse_boundary 只读复用）
P14-B: PASS（RawStore/ingestion_id/DUPLICATE/RAW_MUTATION 权威只读复用）
P14-C: PASS（异常分类不合并）
P14-D: PASS（run_query/result_id/exclusion 四字段直接消费）
P14-E Design Contract v1.1: PASS（全部 §4-§16 语义继承）
P14-E Production Contract v1.1（76b352e 验收，144b38f 归档）: PASS（本文为其实现层细化，无语义变更）
P14-E Acceptance Record（144b38f）: PASS
Compatibility: PASS —— DEPENDENCY_CONTRACT_CONFLICT: NONE
```

确定性/反作弊/边界继承：同 (query, as_of, records) → 同双 ID；禁
fixture_mode/expected_result_override/golden_override/test_only/
skip_validation/force_visible/force_hidden/running_under_test；公开 API 面
仅限 §10 六接口；`research_end = 2026-09-22` / `virgin_start = 2026-09-23`
冻结；P13-T STOPPED / P13-U PROTECTED；fixture 仅合成日期。

## 12. Invariant Registry（P14E-I-001..024）

- **P14E-I-001**: Included 边界冻结（§2.1）。
- **P14E-I-002**: Excluded 边界冻结（§2.2，永久出界）。
- **P14E-I-003**: 权威链与三禁止冻结（§3）。
- **P14E-I-004**: CMP-EVIDENCE 七元组冻结。
- **P14E-I-005**: CMP-STORE 七元组冻结。
- **P14E-I-006**: CMP-MANAGER 七元组冻结。
- **P14E-I-007**: CMP-TRACE 七元组冻结。
- **P14E-I-008**: CMP-AUDIT 七元组冻结。
- **P14E-I-009**: CMP-VALIDATION 七元组冻结。
- **P14E-I-010**: Evidence 身份四类继承冻结；ingested_at 不回到身份。
- **P14E-I-011**: CREATE 态规则冻结。
- **P14E-I-012**: VALIDATE 态规则冻结。
- **P14E-I-013**: FREEZE 态规则冻结。
- **P14E-I-014**: STORE 态规则冻结。
- **P14E-I-015**: QUERY 态规则冻结。
- **P14E-I-016**: TRACE 态规则冻结。
- **P14E-I-017**: AUDIT 态规则冻结。
- **P14E-I-018**: FOUR-CLASS 反向追踪冻结；HASH_MISMATCH 第五类永久禁止。
- **P14E-I-019**: 持久化规则冻结（JSONL 已有架构约束优先）。
- **P14E-I-020**: 六层失败分类冻结。
- **P14E-I-021**: Detection/Response/Audit 三元组冻结。
- **P14E-I-022**: 六接口语义冻结。
- **P14E-I-023**: 兼容性结论冻结（§11 全 PASS；冲突即 STOP）。
- **P14E-I-024**: 确定性/反作弊/边界继承冻结。
