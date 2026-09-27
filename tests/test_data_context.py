from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord, DEFAULT_DATASETS
from astock_v2.data.events import PolicyEvent
from astock_v2.data.market_context import MarketContext


def record(available: str | None, scope=AssetScope.CN_STOCK):
    return HistoricalRecord(
        symbol="000001",
        event_time="2026-09-25T15:00:00+08:00",
        available_time=available,
        source="test",
        source_type="historical",
        value={"close": 10.0},
        layer=DataLayer.CLEAN,
        asset_scope=scope,
    )


def test_historical_record_requires_available_time_for_pit():
    assert record(None).pit_ready is False
    assert record("2026-09-25T18:00:00+08:00").admissible_at("2026-09-26T09:30:00+08:00")
    assert not record("2026-09-26T10:00:00+08:00").admissible_at("2026-09-26T09:30:00+08:00")


def test_market_context_excludes_future_or_missing_records():
    ctx = MarketContext(
        decision_time="2026-09-26T09:30:00+08:00",
        cn=(record("2026-09-25T18:00:00+08:00"),),
        overseas=(record("2026-09-26T10:00:00+08:00", AssetScope.GLOBAL_INDEX),),
        macro=(record(None, AssetScope.RATE),),
    )
    assert len(ctx.admissible_records()) == 1
    assert len(ctx.excluded_records()) == 2
    assert ctx.pit_admissible is False


def test_policy_event_does_not_provide_subjective_direction():
    event = PolicyEvent(
        "evt-1", "2026-09-25T12:00:00+08:00", "2026-09-25T12:05:00+08:00",
        "official", "industry_policy", "Example policy",
        affected_sectors=("technology",), evidence_level="PRIMARY_SOURCE",
    )
    assert event.quantitative_direction is None


def test_default_datasets_cover_cn_global_macro_policy():
    scopes = {item.asset_scope for item in DEFAULT_DATASETS}
    assert AssetScope.CN_STOCK in scopes
    assert AssetScope.GLOBAL_INDEX in scopes
    assert AssetScope.RATE in scopes
    assert AssetScope.POLICY_EVENT in scopes
