from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.local_pipeline import build_local_factor_rows


def record(day, close, revision=0, available="16:00:00"):
    return HistoricalRecord(
        symbol="300308",
        event_time=f"{day}T15:00:00+08:00",
        available_time=f"{day}T{available}+08:00",
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


def test_later_revision_does_not_hide_original_at_1600(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    days = [
        ("2026-01-05", 10), ("2026-01-06", 11), ("2026-01-07", 12),
        ("2026-01-08", 11), ("2026-01-09", 13), ("2026-01-12", 14),
        ("2026-01-13", 15), ("2026-01-14", 14), ("2026-01-15", 16),
        ("2026-01-16", 17), ("2026-01-19", 18), ("2026-01-20", 17),
        ("2026-01-21", 19), ("2026-01-22", 20), ("2026-01-23", 19),
        ("2026-01-26", 21), ("2026-01-27", 22), ("2026-01-28", 21),
        ("2026-01-29", 23), ("2026-01-30", 24), ("2026-02-02", 25),
        ("2026-02-03", 26), ("2026-02-04", 27),
    ]
    rows = [record(day, close) for day, close in days]
    rows.append(
        record("2026-01-20", 99, revision=1, available="18:00:00")
    )
    store.append_records("cn_stock_daily", rows)

    result = build_local_factor_rows(store, "300308", lookback=20)

    assert result
    assert result[0].source_event_time == "2026-02-02T15:00:00+08:00"
    assert result[0].label == 1


def test_local_factor_rows_reject_invalid_lookback(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    try:
        build_local_factor_rows(store, "300308", lookback=0)
    except ValueError as exc:
        assert "lookback" in str(exc)
    else:
        assert False


def test_late_revision_is_excluded_until_its_available_time(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    days = [(f"2026-01-{day:02d}", float(day)) for day in range(1, 23)]
    rows = [record(day, close) for day, close in days]
    rows.append(record("2026-01-21", 99.0, revision=1, available="18:00:00"))
    store.append_records("cn_stock_daily", rows)

    result = build_local_factor_rows(store, "300308", lookback=20)

    assert result
    # The first decision is 16:00 on 2026-01-21, so revision=1 is not yet
    # admissible; momentum must use the original close=21 observation.
    assert result[0].factors["momentum"] == 21.0 / 1.0 - 1.0
