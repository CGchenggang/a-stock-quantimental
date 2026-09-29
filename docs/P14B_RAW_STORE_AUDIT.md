# P14-B Raw Store Audit — 逐字段核验

- 日期：2026-09-29
- 范围：`src/astock_v2/information/raw_store.py`、`adapters.py`、`adapters_fixture.py`；产物 `data/industry/p14b/`

## 1. raw_payload

**是什么**：adapter 从 source 实际收到的原始内容的 canonical 表示（`json.dumps(payload, sort_keys=True)` 的 dict）。**不是** normalization 后的结果——normalization 由 P14-A 承担，且其输入始终可以从 raw_payload 重放审计。

测试：`test_raw_payload_preserved_and_hashed`——store 中的 raw_payload 与 fixture payload 逐字段相等。

## 2. raw_payload_hash

canonical payload 的 SHA256。确定性：`test_canonical_payload_hash_detects_difference`（同输入同 hash、异输入异 hash）；`test_adapter_output_and_store_deterministic`（两次完整 ingest 报表与记录 byte-identical）。identity 不使用 random UUID / runtime timestamp。

## 3. source_id / revision / event_time / available_time / ingested_at

- `test_ingest_metadata_preserved_and_never_fabricated`：五字段全部与 source payload 原值一致；adapter_version = `cn_index_daily_adapter@1`。
- available_time 缺失时：**不回填** event_time 或 ingested_at——记录保持 `available_time=None`、`quality_status=UNRESOLVED`、`availability_status=available_time_unresolved`（`test_missing_available_time_stays_unresolved`），且 `to_information_record` 拒绝该记录进入 P14-A contract（`ValueError: ... available_time`）。

## 4. adapter_version

每条 raw record 携带其产生时的 adapter_version（`@1`）；ingestion_id 的 hash 输入包含 adapter_version——未来 parser 升级为 @2 时，新旧 raw record 的身份天然区分（`test_frozen_manifest_hashes...` 类比：hash 覆盖 adapter_version 字段）。metadata（`AdapterMetadata`）记录 timestamp_semantics / revision_semantics / provenance_requirements，可审计。

## 5. Idempotency / Mutation / Revision

| 不变量 | 测试 | 实测 |
|---|---|---|
| 同 key 同 payload 重放 N 次 → 1 条逻辑记录 | `test_same_payload_reingest_is_idempotent` | accepted 2 → replay duplicates 2/accepted 0，records=2 |
| 同 key 不同 payload → RAW_MUTATION_DETECTED，原记录保留 | `test_same_key_different_payload_is_mutation_detected` | mutations=1，records=2（rev0+rev1），99.9 未进入 |
| rev1 不覆盖 rev0 | `test_revision_history_preserved` | revisions=[0,1]，各自 value/available_time 保留 |
| store 文件 byte 级确定性 | `test_store_file_byte_identical_on_replay` | a.jsonl == b.jsonl；同 store 重放不再追加行 |

## 6. Ingestion report（partial failure / source health）

- `test_partial_ingestion_is_audited`：2 attempted（1 good + 1 parse-fail）→ accepted=1 / rejected=1 / status=PARSE_ERROR，error 带 `payload[1]` 索引。
- `test_empty_source_is_empty_success_not_error` / `test_source_error_and_auth_and_timeout_statuses`：EMPTY_SUCCESS / SOURCE_ERROR / AUTH_ERROR / TIMEOUT 四态齐备。

## 7. P14-A 集成

`to_information_record` 投影 + `normalize` 后：research_only=true、content 透传、`metadata.raw_payload_hash` 与 raw store 一致（`test_raw_records_flow_through_p14a_normalization`）；research-zone 决策日的 select_asof 保持 fail-fast、research-zone 日期正常选择（`test_ingested_data_cannot_be_selected_in_virgin_zone`）。

## 8. 无越界

`test_raw_store_module_generates_no_recommendation`：gate/raw_store/adapters 三个模块源码不含 buy_now/place_order/execute_trade/open_position/close_position/broker 任何字样；`test_production_factor_policy_calibration_snapshots`：factor registry 8 因子不变、P13-R policy registry 8 policy 不变、P13-Q calibration registry research_only 不变。
