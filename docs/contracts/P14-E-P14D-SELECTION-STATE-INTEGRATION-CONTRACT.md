# P14-D → P14-E Selection State Integration Contract

> 状态：**DRAFT — AWAITING INDEPENDENT ACCEPTANCE**
> 本契约未获独立验收前**不得实施**：不修改任何 P14-D/P14-A 实现、契约、
> 测试或 authority。本文档仅是 3b8f8ae 判定 Required narrow repair #1
> "preferred approach" 所要求的**单独授权请求**。
>
> 授权依据链：
> P14-E Production Implementation REPAIR-002 Independent Acceptance —
> 2026-10-04, Decision: FAIL / REPAIR REQUIRED（状态记录提交
> `3b8f8aebc9526bc55065da012023d748230351f2`）：
>
> "Resolve the authority/scope issue without weakening the frozen P14-D
> boundary. Preferred approach: expose the already-required resolved
> selection/rejection state through an explicitly authorized P14-E/P14-D
> integration surface **only if that surface is first separately
> authorized and frozen**; otherwise redesign the P14-E handoff so it
> consumes existing accepted P14-D state without modifying P14-D."
>
> 修订历史：
> v1: 初稿（P14-E Production Implementation REPAIR-003 提交）

---

## 1. 为什么需要这个面

三方约束的交汇（每一条都已独立冻结/判定）：

1. **P14-E Contract §6.1/§6.2（冻结，禁改）**：evidence 携带
   `selection_reason`、candidate_trace 携带 `rejection_reason`，
   词表为冻结枚举（P14E-P-007）。bundle 必须携带 verbatim 标签。
2. **REPAIR-002 验收 FAIL（286f3a9）**：P14-E 不得通过比较
   revision / available_time / canonical_json 自行推导标签——那是
   "P14-D version-selection semantics 的第二实现"。标签必须
   verbatim 来自 P14-D resolved output。
3. **已接受的 P14-D 输出面（冻结）**：`run_query` 返回
   `{query, records, excluded, counts, result_id}`，其中不含任何
   selection/rejection 标签。

结论：在"不修改 P14-D"的前提下，标签没有合法来源；约束 2 排除了
P14-E 自行比较，约束 1 排除了省略标签。因此唯一的自洽架构是判定
指定的 preferred approach：**给 P14-D 增加一个 additive 的
selection-state 发射面，该面先单独授权并冻结，P14-E 纯消费**。

## 2. 授权范围（本契约被接受后允许改动的全部内容）

| 文件 | 允许的改动 | 性质 |
|------|-----------|------|
| `src/astock_v2/information/pit.py` | 新增 6 个标签常量 + `resolve_selection()` | 纯新增，不动现有函数 |
| `src/astock_v2/information/research_query.py` | `run_query` 输出新增顶层 `selection` 键 | additive，现有键语义/排序键零改动 |
| `docs/contracts/P14-D-DESIGN-CONTRACT.md` | §9 增补 `selection` 说明 + 修订历史 v1.2 | 文档增补，状态行不动 |
| `tests/contracts/p14d/test_p14d_harness.py` | 顶层键集断言扩展 + `test_p14d_011` | additive 断言 |

**明确不在授权范围内**（即使本契约被接受）：PIT 可见性规则、版本
选择规则、排除分类、`records`/`excluded`/`counts`/`result_id` 的
语义或排序键、P14-D Golden fixtures、P14-C、P13-T/U、data、
factors/alpha、calibration、policy、recommendation/portfolio/trading、
P14-F。

## 3. 面规格（v1，冻结候选）

### 3.1 pit.py（P14-A 选择权威，标签与规则同源）

```text
SELECTED_HIGHEST_REVISION           = "SELECTED_HIGHEST_REVISION"
SELECTED_EARLIEST_ON_REVISION_TIE   = "SELECTED_EARLIEST_ON_REVISION_TIE"
SELECTED_CANONICAL_TIEBREAK         = "SELECTED_CANONICAL_TIEBREAK"
REJECTED_LOWER_REVISION             = "REJECTED_LOWER_REVISION"
REJECTED_REVISION_TIE_NOT_EARLIEST  = "REJECTED_REVISION_TIE_NOT_EARLIEST"
REJECTED_CANONICAL_TIEBREAK         = "REJECTED_CANONICAL_TIEBREAK"
```

字面值 = P14E-P-007 冻结词表，逐字相同。标签定义在规则旁——
`resolve_selection(records, winners)` 对一个**已由
`visible_revisions` 算出的映射**做分类：每个 lineage winner 的选择
标签 + 每个可见未胜出记录的落选标签，复述 `visible_revisions`
应用的完全相同的比较。规则与词表单一来源；不存在第二处选择语义。
与 winner 逐字节相同的记录（同 canonical 内容）就是 winner 本身，
不产生落选条目。

### 3.2 research_query.py（P14-D 发射 resolved state）

```text
result["selection"] = {
  "selected": [ {…完整 provenance 投影…, "selection_reason": <label>} ],
  "rejected": [ {…完整 provenance 投影…, "rejection_reason": <label>} ],
}
```

- `selected` 与 `result.records` 一一对应（同一集合，附加标签）。
- `rejected` 仅为**可见但未胜出**的记录；PIT 排除/越界/未解析记录
  不进 `rejected`（仍走 `excluded`）。
- 排序键冻结：selected 按 P14-D records 排序键；
  rejected 按 `(source, source_record_id, revision, available_time,
  canonical_json)`。
- 确定性：result_id 覆盖 selection state（相同输入 → byte-identical）。
- 现有四键（records/excluded/counts/result_id）语义与排序键零改动。

## 4. 消费面（P14-E，本契约被接受后解锁）

REPAIR-002（提交 `5dbc9c453df7d51c636a1cd07994c4ac85eb3ac0`）中的
P14-E 消费实现已通过独立验收的 verified positive 审查
（"conceptually sound and preserves the existing selection semantics"），
本契约被接受后按原样恢复：

- `create_bundle` 纯消费：无 lineage 扫描、无比较、无重分类；
  `selection_reason` 按 identity-key 从 resolved state 逐字查找；
  `candidate_trace` 是 `selection.rejected` 的逐字字段投影（保序）。
- authority_violation：result 缺 `selection`、条目无标签、
  selected 未被 resolved state 覆盖。
- identity_failure：selected/rejected 引用 P14-B 权威集中不存在的记录。
- 回归测试组：逐字消费证明（改写 resolved 标签 → bundle 跟随）、
  欠解析 result 拒绝、未覆盖记录拒绝、trace 权威锚定、
  PIT 泄漏禁令、monkeypatch PIT/selection 入口、静态无调用扫描。

## 5. 不变量（验收检查单）

1. additive-only：除 §2 所列四处，无任何文件变动。
2. PIT 语义零变化：visible ⇔ available_time <= as_of（含边界）。
3. 选择规则零变化：visible_revisions 行为逐字节不变（回归证明）。
4. 词表零变化：6 个标签字面值 = P14E-P-007 逐字。
5. 确定性：含 selection 的 result 仍满足 P14D-006（双跑一致）。
6. P14-E 纯消费：无任何比较逻辑（monkeypatch + 静态扫描证明）。
7. 既有 P14-D harness/golden 全绿（除 §2 明示的 additive 断言）。

## 6. 实施门

- 本契约 STATUS: DRAFT —— **未验收，不实施**。
- 验收 PASS 后的实施内容 = §2 + §3 + §4 的精确 delta
  （即已验证的 REPAIR-002 改动，逐字恢复，仅更新文档内 SHA 引用）。
- 验收 FAIL 则本面作废，P14-E handoff 保持 REPAIR-001 已接受形态，
  架构修复另议。
