# P14-B Research Plan — Source Adapters & Immutable Raw Information Store

- 日期：2026-09-29
- 基线：`89349da`（P14-A 验收终点）
- 性质：**raw ingestion boundary（数据完整性/闸门）**。不是 alpha research、不是 factor/recommendation development。P14-A 的 contract/PIT/freshness/revision/dedup/conflict 语义原样沿用，零重设计。

## 1. 架构

```text
External Source
      ↓ SourceAdapter（fetch/parse/to_raw_record, adapter_version）
RawIngestRecord（不可变，17+ 字段，含 raw_payload + raw_payload_hash + ingestion_id）
      ↓ RawStore（append-only JSONL，幂等 put，RAW_MUTATION_DETECTED 拒绝覆盖）
P14-A RawInformationRecord（provenance 投影）
      ↓ normalize()（P14-A 原样：provenance/registry/dedup/conflict/PIT/research_only）
Research Information Record
```

## 2. Raw Record Contract（`raw_store.RawIngestRecord`）

P14-A 14 字段之外新增：`raw_payload`（adapter 实际收到的原始内容 canonical 表示——**不是** normalization 后的结果）、`raw_payload_hash`（canonical payload 的 SHA256，确定性：相同 source/source_id/revision/payload → 相同 hash）、`ingestion_id`（sha256(source|source_id|revision|payload_hash|adapter_version)）、`adapter_version`（如 `company_announcement_adapter@1`——parsing 修改后升 @2，历史 raw record 永不误标）。

时间三分：`event_time`（source 事件时间）、`available_time`（source 发布/可得时间，**可缺失**）、`ingested_at`（本系统入库时间）。ingested_at 绝不替代 available_time；available 缺失时记录保持 `available_time=None` + `quality_status=UNRESOLVED` + `availability_status=available_time_unresolved`，投影到 P14-A contract 时被显式拒绝（`to_information_record` raises）——不能进 PIT-safe research layer。

## 3. Raw Store 不变量（`raw_store.RawStore`）

- **Append-only**：无 update/delete 路径。
- **幂等**：同 (source, source_id, revision) + 同 payload_hash 重复 put → `DUPLICATE`，逻辑记录仍一条。
- **禁止静默覆盖**：同 key 不同 payload_hash → `RAW_MUTATION_DETECTED`，原记录保留，新 payload 记为被拒 attempt。
- **Revision history**：key 含 revision → rev1 永不覆盖 rev0；PIT 可见性归 P14-A 层。
- Research admissibility ≠ raw storage：invalid/unresolved/duplicate/conflicting 都可存于 raw store，进入 research layer 只能经 P14-A `normalize`（本阶段未复制任何 normalization）。

## 4. Adapter Contract（`adapters.SourceAdapter`）

`fetch/parse` + `ingest(store, ingested_at)` 生成诚实报表：`attempted = accepted + rejected(+failed)`、duplicates、mutations、errors（带 payload index）。source health 状态：`OK / EMPTY_SUCCESS / SOURCE_ERROR / PARSE_ERROR / AUTH_ERROR / TIMEOUT`。adapter 不得伪造 availability：source 无可靠 available_time → 记录保持 UNRESOLVED。

## 5. Fixture Adapters（4 个 representative，全部 offline deterministic）

`cn_index_daily` / `company_announcement` / `macro_pmi_cn` / `us_index_daily`（`adapters_fixture.py`）——均使用 P14-A 已注册的 source registry 类别与 freshness policy，未创建第二套 registry。每个 packet 携带 raw_payload（verbatim dict）与显式 available_time。

## 6. Virgin protection

Raw ingestion 可以记录真实 source 数据（含日期 > research_end 的源数据——那是数据，不是研究消费）；但研究层访问仍被 P13-U guard 保护：`select_asof` 对 decision_time ≥ 2026-09-23 继续 fail-fast（P14-B 回归测试锁定 raw→normalize→select_asof 全链路）。RESEARCH_END/VIRGIN_START 常量未改（现从 `research_boundary.py` 单一来源导入）。

## 7. 产物

`scripts/run_p14b_ingestion_audit.py --out-dir data/industry/p14b`：4 source 全 OK，每 source attempted=1/accepted=1，raw_records.jsonl 4 行，normalized 4 条，全部在 research-zone 决策日可见；manifest 记录 SHA256。双次运行全部 byte-identical。
