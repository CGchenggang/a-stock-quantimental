# P14-D → P14-E Selection State Integration Contract

> 状态：**ACCEPTED — INDEPENDENTLY ACCEPTED**（Contract Acceptance，
> 记录提交 `006780705fd93579b89141109de7353593608711`，2026-10-04，
> 验收对象 = 本契约 v2 `51a769f0a50632c5b8d71f4247d5a60ee2847012`）
>
> 生命周期（四阶段分离，不得合并）：
>
> Contract Acceptance — PASS / INDEPENDENTLY ACCEPTED（`0067807`）
>   → Human Authorization — GRANTED（`3ec2b86`，2026-10-04）
>   → Implementation — DELIVERED（`69cfe2a86d23352e9f74cf7454aad6cf59135e7b`，
>     2026-10-04）
>   → Independent Acceptance of the implementation — **PASS**
>     （2026-10-08，ZCODE V8 控制面验收；owner 同日 Human
>     Authorization 再确认——"P14 主线，对集成契约 v2 授权"）
>
> 本文档源于 3b8f8ae 判定 Required narrow repair #1 "preferred
> approach" 所要求的**单独授权请求**；"未获独立验收前不得实施"的
> 前置约束已由上述授权链依序满足并解除。
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
> 独立可行性依据（2026-10-04）：P14-E Production Implementation
> REPAIR-003 以 BLOCKED 终结（PROJECT_STATUS "REPAIR-003 BLOCKED
> Record"，提交 `3d401bf1b09d4afe1afc2ec3bbf585cdff0f445b` +
> `91836f74a1e8895c85b354e2fe27429a87aa92e9`）：两条替代路线——
> 直接消费现有 P14-D state（冻结输出无标签源）与 P14-E 本地适配层
> （必然重应用被 286f3a9 判定的比较语义）——均经代码级核查不可行；
> 该 BLOCKED 判定已由独立验收确认原因成立。本契约因此是判定
> preferred approach 的授权请求，也是当前唯一自洽路径。
>
> 修订历史：
> v1: 初稿（P14-E Production Implementation REPAIR-003 提交）
> v2: 独立验收准备修订（2026-10-04）——§2 补包面导出行
>     （`__init__.py`）；§4 显式枚举 P14-E 恢复面两文件；
>     §5.1 文件口径与 authority terminology 对齐；§6 强化
>     未验收不实施与四阶段分离。§1/§3 语义面零变化；
>     STATUS 仍为 DRAFT。
> v3: 状态生命周期同步（2026-10-04，docs-only，最小 Repair）——
>     STATUS 由 DRAFT 更新为 ACCEPTED — INDEPENDENTLY ACCEPTED
>     （Contract Acceptance `0067807`）；记录 Human Authorization
>     （`3ec2b86`）与 Implementation（`69cfe2a`）生命周期事实；
>     §6 状态引用同步。§1-§5 语义零变化；四阶段分离保留；
>     `0067807` / `3ec2b86` / `69cfe2a` 历史事实原样引用，无任何改写。
> v4: Independent Acceptance 记录（2026-10-08，docs-only）——实施的
>     Independent Acceptance 判定 **PASS**，生命周期四阶段全部闭合。
>     验收证据：实施 `69cfe2a` delta 与 §2/§3/§4 授权面精确一致
>     （7 文件）；全量 pytest 733 passed；三合同审计 exit 0（P14-E
>     failures 空）；P13-M 回归 3 passed；§5 不变量抽查通过
>     （additive-only / PIT 边界 / 词表 P14E-P-007 / P14-E 纯消费
>     静态扫描无第二 selection authority）。owner 于 2026-10-08 明示
>     "P14 主线，对集成契约 v2 授权"，构成本契约 Human Authorization
>     的再确认与验收授权。§1-§6 语义零变化。

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
| `src/astock_v2/information/__init__.py` | `from .pit import (...)` 增加 `resolve_selection`；`__all__` 增加同名导出（REPAIR-002 已验证 hunk，逐字恢复） | additive 包面导出：仅新增一个 re-export，不新增模块、不改既有导出语义 |

包面说明：`__init__.py` 的改动仅是 P14-A 选择权威新函数的包级
re-export（公开 API 完整性），不含任何逻辑；集成面的全部
selection 语义仍只存在于 `pit.py`（规则旁）与 `research_query.py`
（发射点）两处，且二者同属 P14-A/P14-D 权威面。

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

恢复面文件集（Implementation 阶段执行，精确两文件、逐字恢复
REPAIR-002 对应 delta，无其他）：

- `src/astock_v2/information/evidence.py` —— 纯消费 create_bundle
  （删除 lineage 扫描 / 补集推断 / `_selection_reason` /
  `_rejection_reason` / `_check_candidate_consistent` 全部重推导
  机器）。
- `tests/test_p14e_production_impl.py` —— 上列 verbatim 回归组
  逐字恢复。

本文件集是 §4 承诺的完整实施面；除 §2 所列五处与本节两文件外，
实施不得触碰任何其他文件。

## 5. 不变量（验收检查单）

1. additive-only：除 §2 所列 P14-D 集成面五处（`pit.py` /
   `research_query.py` / P14-D 契约 / P14-D harness / 包
   `__init__.py` 导出）与 §4 所列 P14-E 恢复面两文件
   （`evidence.py` / `test_p14e_production_impl.py`）外，
   无任何文件变动。authority ownership 全程不变：
   P14-A/P14-D = selection/version authority（唯一），
   P14-E = evidence consumer，P14-B = raw evidence authority，
   P14-C = source reconciliation authority；本契约不产生、
   不允许任何第二套 selection authority。
2. PIT 语义零变化：visible ⇔ available_time <= as_of（含边界）。
3. 选择规则零变化：visible_revisions 行为逐字节不变（回归证明）。
4. 词表零变化：6 个标签字面值 = P14E-P-007 逐字。
5. 确定性：含 selection 的 result 仍满足 P14D-006（双跑一致）。
6. P14-E 纯消费：无任何比较逻辑（monkeypatch + 静态扫描证明）；
   实施后系统内 selection 分类逻辑唯一存在于 P14-A/P14-D 权威
   （`pit.resolve_selection`，与规则同文件同源）——P14-E 侧不存在
   `_selection_reason()` / `_rejection_reason()` 等任何第二套
   selection authority，`selection_reason` / `rejection_reason`
   一律从 resolved state 逐字消费。
7. 既有 P14-D harness/golden 全绿（除 §2 明示的 additive 断言）。

## 6. 实施门（四阶段分离，不得合并）

- 本契约 STATUS：**ACCEPTED — INDEPENDENTLY ACCEPTED**（`0067807`）。
  历史约束记录：在获得独立 Acceptance 记录之前**绝对不得实施**
  （不得修改任何生产代码、测试、P14-D 冻结面或 P14-E 运行时）——
  该前置条件已由 `0067807`（Contract Acceptance）与 `3ec2b86`
  （Human Authorization）依序满足；实施 `69cfe2a` 系在授权链完成后
  进行，其 Independent Acceptance 已于 2026-10-08 判定 **PASS**
  （见修订历史 v4）——生命周期四阶段全部闭合。
- 阶段分离：本契约获得独立 Contract Acceptance 后，仍须由验收方
  显式作出 **Human Authorization**，之后才进入 **Implementation**
  （内容 = §2 + §3 + §4 的精确 delta，即已验证的 REPAIR-002 改动
  逐字恢复；P14-D 契约 v1.2 修订历史的授权依据行届时改引本契约），
  最后由 **Independent Acceptance** 验收实施结果。本契约文本自身的
  接受不构成实施授权。
- 独立验收判 FAIL 则本面作废，P14-E handoff 保持 REPAIR-001 形态
  （处于 286f3a9 FAIL 判定下），架构修复另议。
