# P14-D Acceptance Matrix

> Design Contract invariant ↔ Acceptance Matrix row ↔ Golden fixture ↔
> Harness test 可追踪。
>
> 状态：FROZEN — P14-D-REPAIR-001 — awaiting independent acceptance
>
> Bidirectional closure mechanically verified (scripts/audit_p14d_contract.py):
> contract_unique_ids = 10, matrix_unique_ids = 10, golden_ids = 11,
> orphans/duplicates/undefined = 0

| Contract ID | Requirement | Golden | Harness Test | Expected Result |
|-------------|------------|--------|--------------|-----------------|
| P14D-001 | 正常 PIT 查询：admissible 记录进入结果 | G-001 | test_p14d_001_normal_pit | 可见记录与手写期望一致 |
| P14D-002 | available_time > as_of 不可见 | G-002 | test_p14d_002_future_hidden | excluded[reason=NOT_YET_AVAILABLE] |
| P14D-003 | event_time 早但 available_time 晚仍不可见 | G-003 | test_p14d_003_event_time_never_grants_visibility | 不出现在 records |
| P14D-004 | 同 lineage 多 admissible 版本确定性选择（同 revision → 最早 available_time 胜出） | G-004, G-011 | test_p14d_004_deterministic_version_selection; test_p14d_011_same_revision_tie_earliest_wins | 仅最大 revision；同 revision 取最早 available_time |
| P14D-005 | restatement as_of < T2 不可见 | G-005 | test_p14d_005_restatement_invisible_before_t2 | 仅 original 版本 |
| P14D-006 | 相同输入重复执行 byte-identical | G-006 | test_p14d_006_deterministic_result | result_id 与 canonical json 一致 |
| P14D-007 | 结果 provenance 完整可追溯 | G-007 | test_p14d_007_provenance_complete | 11 个 provenance 字段齐全 |
| P14D-008 | scope 外信息不泄露 | G-008 | test_p14d_008_out_of_scope_never_leaks | records 空；excluded[reason=OUTSIDE_AS_OF] |
| P14D-009 | virgin-zone as_of 被守卫拒绝；无真实 virgin 数据 | G-009+audit | test_p14d_009_virgin_zone_guard_raises | raise；fixture 输入无 >= 2026-09-23 的真实日期 |
| P14D-010 | 查询层不产生 prediction/recommendation/trading | audit | test_p14d_010_query_layer_is_infrastructure_only | 模块无选股/推荐/交易语义 |

## Golden fixture set（冻结）

| Golden | 场景 | Contract IDs |
|--------|------|--------------|
| G-001 | normal PIT | P14D-001, P14D-007 |
| G-002 | future information | P14D-002 |
| G-003 | event/available time mismatch | P14D-003 |
| G-004 | multiple versions | P14D-004 |
| G-005 | restatement | P14D-005 |
| G-006 | deterministic ordering | P14D-006 |
| G-007 | provenance | P14D-007 |
| G-008 | empty result | P14D-008 |
| G-009 | boundary timestamp（available_time == as_of，含边界可见） | P14D-001 |
| G-010 | same-time records（同 available_time 跨 lineage 确定性排序） | P14D-006 |
| G-011 | same-revision tie（同 revision 不同 available_time → 最早胜出） | P14D-004 |

说明：P14D-009 的 virgin-zone 拒绝行为由 harness 测试直接以合成日期
（2099-01-01）验证；G-009 覆盖的是 as_of 边界（含相等）语义，两者互补。
