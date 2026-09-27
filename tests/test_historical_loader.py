from datetime import datetime, timezone

from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.historical_loader import load_daily_provider_result
from astock_v2.data.local_store import LocalHistoricalStore


def make_record(event, available, revision=0, close=10.0):
    return HistoricalRecord(
        symbol="300308",
        event_time=event,
        available_time=available,
        source="test",
        source_type="historical",
        value={
            "date": event[:10],
            "open": close - 1,
            "close": close,
            "high": close + 1,
            "low": close - 2,
            "volume": 1000,
            "amount": 100000,
        },
        revision=revision,
        raw_ref=f"raw-{revision}",
    )


def test_loader_excludes_future_rows_and_selects_latest_revision(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    store.append_records(
        "cn_stock_daily",
        [
            make_record("2026-01-05T15:00:00+08:00", "2026-01-05T16:00:00+08:00", 0, 10),
            make_record("2026-01-06T15:00:00+08:00", "2026-01-06T16:00:00+08:00", 0, 11),
            make_record("2026-01-06T15:00:00+08:00", "2026-01-06T18:00:00+08:00", 1, 12),
            make_record("2026-01-07T15:00:00+08:00", "2026-01-07T16:00:00+08:00", 0, 13),
        ],
    )

    result = load_daily_provider_result(
        store,
        "300308",
        decision_time="2026-01-06T17:00:00+08:00",
    )

    assert [row["close"] for row in result.data] == [10.0, 11.0]
    assert [row["_revision"] for row in result.data] == [0, 0]
    assert result.available_time == "2026-01-06T16:00:00+08:00"


def test_loader_uses_revision_when_revision_is_admissible(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    store.append_records(
        "cn_stock_daily",
        [
            make_record("2026-01-06T15:00:00+08:00", "2026-01-06T16:00:00+08:00", 0, 11),
            make_record("2026-01-06T15:00:00+08:00", "2026-01-06T16:30:00+08:00", 1, 12),
        ],
    )

    result = load_daily_provider_result(
        store,
        "300308",
        decision_time="2026-01-06T17:00:00+08:00",
    )

    assert len(result.data) == 1
    assert result.data[0]["close"] == 12.0
    assert result.data[0]["_revision"] == 1


def test_loader_rejects_naive_decision_time(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    store.append_records(
        "cn_stock_daily",
        [make_record("2026-01-06T15:00:00+08:00", "2026-01-06T16:00:00+08:00")],
    )

    try:
        load_daily_provider_result(
            store,
            "300308",
            decision_time="2026-01-06T17:00:00",
        )
    except ValueError as exc:
        assert "timezone" in str(exc)
    else:
        assert False
