from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore


def record(symbol="000001", event="2026-01-05T15:00:00+08:00", available="2026-01-05T16:00:00+08:00", revision=0):
    return HistoricalRecord(
        symbol=symbol,
        event_time=event,
        available_time=available,
        source="test",
        source_type="historical",
        value={"close": 10.0},
        revision=revision,
    )


def test_local_store_round_trip_and_dedup(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    store.append_records("cn_stock_daily", [record(), record(revision=1)])
    store.append_records("cn_stock_daily", [record()])
    rows = store.read_records("cn_stock_daily", "000001")
    assert len(rows) == 2
    assert rows[0].revision == 0
    assert rows[1].revision == 1


def test_local_store_rejects_naive_timestamp(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    bad = record(event="2026-01-05T15:00:00")
    try:
        store.append_records("cn_stock_daily", [bad])
    except ValueError as exc:
        assert "timezone" in str(exc)
    else:
        assert False


def test_local_store_rejects_availability_before_event(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    bad = record(available="2026-01-05T14:00:00+08:00")
    try:
        store.append_records("cn_stock_daily", [bad])
    except ValueError:
        return
    assert False
