# P14-B Acceptance Report — Source Adapters & Immutable Raw Information Store

- 日期：2026-09-29
- 基线：`89349da`（P14-A 验收终点）
- 文档：`docs/P14B_RESEARCH_PLAN.md`、`docs/P14B_RAW_STORE_AUDIT.md`
- 产物：`data/industry/p14b/`（raw_records.jsonl、normalized_records.json、ingestion_audit.json、manifest.json；双次运行 byte-identical）
- 状态：**implementation complete; awaiting independent acceptance**——PASS 由外部验收判定。

## 1. Implementation

- `src/astock_v2/information/raw_store.py`（新增）：`RawIngestRecord`（17 字段 raw contract：P14-A 14 字段 + raw_payload/raw_payload_hash/ingestion_id/adapter_version）、`RawStore`（append-only JSONL；幂等 put；RAW_MUTATION_DETECTED 拒绝静默覆盖；revision history 保留）、`canonical_payload_hash`（确定性 SHA256）、`to_information_record`（→ P14-A contract 投影；unresolved availability 显式拒绝）。
- `src/astock_v2/information/adapters.py`（新增）：`SourceAdapter` 契约 + `AdapterMetadata`（source/category/version/timestamp_semantics/revision_semantics/provenance_requirements）+ `IngestionReport`（attempted/accepted/rejected/duplicates/mutations/errors + source health 五态）。
- `src/astock_v2/information/adapters_fixture.py`（新增）：4 个 deterministic fixture adapters（cn_index_daily / company_announcement / macro_pmi_cn / us_index_daily），使用 P14-A source registry，未建第二套 registry。
- `scripts/run_p14b_ingestion_audit.py`（新增）：全链路 audit（raw store → normalize → PIT select_asof）+ manifest。
- `src/astock_v2/information/research_boundary_guard.py` / `__init__.py`（P14-A 微调）：select_asof 的 virgin guard 接线（P14-A 验收后的 wiring 补全，语义不变）。

## 2. Verification Results

| 项 | 结果 |
|---|---|
| 全量 pytest | **302 passed / 0 failed**（281 + 21 P14-B 新增） |
| P14-B dedicated | **21 passed**（覆盖 §26 全部 28 项要求） |
| Reproducibility | adapter 输出、store 文件、ingestion audit、normalized、manifest 双次运行 **全部 byte-identical** |
| Virgin protection | ingested 数据在 virgin 决策日 select_asof → fail-fast（`test_ingested_data_cannot_be_selected_in_virgin_zone`）；P13-Q/P13-R guard 保持激活 |
| Production | factor registry / P13-R policy registry（8）/ P13-Q calibration registry（research_only）快照测试锁定；无 recommendation 生成（源码禁词测试） |

## 3. Key invariants（实测）

- raw_payload verbatim 保留 + SHA256 确定性（同 payload 同 hash，异 payload 可检测）。
- 同 key 同 payload 重放 N 次 → 1 条逻辑记录（DUPLICATE 审计）；同 key 异 payload → RAW_MUTATION_DETECTED，原始记录保留、新 payload 记为被拒。
- rev0/rev1 共存，rev1 永不覆盖 rev0。
- available_time 缺失 → UNRESOLVED，绝不回填 event_time/ingested_at；`to_information_record` 拒绝投影。
- partial ingestion：attempted = accepted + rejected，错误带 payload 索引，status=PARSE_ERROR；empty source = EMPTY_SUCCESS；SOURCE_ERROR/AUTH_ERROR/TIMEOUT 状态齐备。
- adapter_version 与 ingested_at/event_time/available_time 全部原样保留。

## 4-R1. Durable Ingestion Audit Repair（P14-B-R1，验收阻塞修复）

独立验收发现：DUPLICATE / RAW_MUTATION_DETECTED 的 ingestion outcome 仅存于进程内存，重启即失。修复：

1. `RawStore` 现维护两个 append-only 文件——`raw_records.jsonl`（ACCEPTED canonical records）与 `raw_ingestion_audit.jsonl`（**每一次 attempt** 的持久化事件：ACCEPTED/DUPLICATE/RAW_MUTATION_DETECTED/REJECTED/SOURCE_ERROR/AUTH_ERROR/TIMEOUT）。事件含 incoming/stored raw_payload_hash、ingestion_id、adapter_version、错误与 payload 索引。
2. `RawIngestRecord.__post_init__` 构造期派生 availability 语义（available_time=None → UNRESOLVED + available_time_unresolved），移除 adapters.py 的 frozen-object `__dict__` 突变。
3. 测试 A–G 新增（restart 后 duplicate/mutation 审计可恢复、append-only 前缀不变、deterministic replay、replay 不产生重复 canonical records、partial failure 与 source failure 持久可审计）。

实测：双次 deterministic fixture 运行 5 个产物 byte-identical（含 audit 文件）；mutation/duplicate/restart/append-only/partial/source-failure 全部 PASS。

## 4. Known Limitations

- RawStore 为单进程内存+JSONL 实现，无并发锁/压缩（当前单机研究用途足够；多进程写入属后续阶段）。
- available_time 缺失的记录在 P14-A contract 中以空串+UNRESOLVED 表达——下游 PIT 选择天然排除，但聚合报告需单独统计该状态。
- 4 个 fixture adapters 覆盖代表性 source 类型；真实生产 adapter（P14-E）接入时必须注册到同一 registry 并复用本阶段 contract。

## 5. CI

推送后以 GitHub API 核验 run → job → step（pytest / p13m / Full pytest suite），run ID 记录于下方 Git Commits 更新（以 Actions 页面为准）。

## 6. Git Commits

| commit | 内容 |
|---|---|
| feat: add P14-B raw ingestion store and source adapters | raw store + adapter contract + fixture adapters |
| test: add P14-B raw store and adapter tests | 21 项 |
| docs: add P14-B research plan, raw store audit and acceptance report | 三份文档 |
