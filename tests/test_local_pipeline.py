from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows


def rec(day, close, revision=0, available_hour="16:00:00"):
    return HistoricalRecord(
        symbol="300308",
        event_time=f"{day}T15:00:00+08:00",
        available_time=f"{day}T{available_hour}+08:00",
        source="test",
        source_type="historical",
        value={
            "date": day,
            "open": close,
            "close": close,
            "high": close,
            "low": close,
            "volume": 1000,
            "amount": 100000,
        },
        revision=revision,
    )


def test_local_factor_rows_use_only_pit_admissible_revision(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    records = []
    for day, close in [
        ("2026-01-01", 10), ("2026-01-02", 11), ("2026-01-03", 12),
        ("2026-01-04", 11), ("2026-01-05", 13), ("2026-01-06", 14),
        ("2026-01-07", 15), ("2026-01-08", 14), ("2026-01-09", 16),
        ("2026-01-10", 17), ("2026-01-11", 18), ("2026-01-12", 17),
        ("2026-01-13", 19), ("2026-01-14", 20), ("2026-01-15", 19),
        ("2026-01-16", 21), ("2026-01-17", 22), ("2026-01-18", 21),
        ("2026-01-19", 23), ("2026-01-20", 24), ("2026-01-21", 25),
        ("2026-01-22", 26), ("2026-01-23", 27),
    ]:
        records.append(rec(day, close))
    # A later revision for 2026-01-20 is unavailable at that day's 16:00
    # decision, so the original revision must remain visible to the factor.
    records.append(rec("2026-01-20", 99, revision=1, available_hour="18:00:00"))
    store.append_records("cn_stock_daily", records)

    rows = build_local_factor_rows(store, "300308", lookback=20)

    assert rows
    first = rows[0]
    assert first.source_event_time == "2026-01-21T15:00:00+08:00"
    assert first.label == 1
    assert first.next_return > 0


def test_local_factor_rows_reject_invalid_lookback(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    try:
        build_local_factor_rows(store, "300308", lookback=0)
    except ValueError as exc:
        assert "lookback" in str(exc)
    else:
        assert False
