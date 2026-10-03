# P14-E Production Migration Plan

> STATUS: DRAFT — PRODUCTION IMPLEMENTATION NOT AUTHORIZED
>
> 本文描述从当前状态（P14-E Contract/Golden 已接受，src 无 P14-E runtime）
> 到目标状态（P14-E Production Implementation 已实现并通过验收）的迁移路径。
> 本阶段仅设计，不执行。

---

## 1. Current State（基线）

```text
src/astock_v2/information/     18 个模块（无 evidence/bundle runtime）
tests/contracts/p14e/          19 fixtures + 引擎 + 测试
evidence_bundles.jsonl         不存在（待生产实现创建）
```

## 2. Target State

```text
src/astock_v2/information/     18 + evidence.py + evidence_store.py = 20 模块
evidence_bundles.jsonl         生产持久化文件（调用方提供路径）
```

## 3. Migration Steps

| Step | Action | Files | Reversible |
|------|--------|-------|------------|
| 1 | 创建 `evidence.py`（Evidence dataclass + evidence_id + create_bundle + freeze_bundle + validate_bundle） | evidence.py | 是（删除文件） |
| 2 | 创建 `evidence_store.py`（EvidenceStore append/reload/verify） | evidence_store.py | 是 |
| 3 | `__init__.py` 导出新符号 | __init__.py | 是 |
| 4 | 添加生产测试 | tests/ | 是 |
| 5 | workflow 添加 P14-E production test 步骤 | .github/workflows/ | 是 |

无 data migration：evidence_bundles.jsonl 是新建文件，无旧数据需迁移。

## 4. Rollback

任一步骤失败 → 删除新增文件 + revert __init__.py → 恢复到 P14-E-006 状态。

## 5. Risk

- 风险：create_bundle 误调 run_query → 防回归测试（monkey-patch run_query 为 raise）
- 风险：bundle_id 漂移 → Golden 逐位一致对照测试
- 风险：持久化损坏 → reload 双重校验 fail-fast
