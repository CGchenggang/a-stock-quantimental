from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.relative_context import build_stock_relative_context


def _record(symbol: str, day: int, close: float, available: str | None = None):
    date = f"2020-01-{day:02d}"
    return HistoricalRecord(
        symbol=symbol,
        event_time=f"{date}T15:00:00+08:00",
        available_time=available or f"{date}T16:00:00+08:00",
        source="test",
        source_type="test",
        value={
            "date": date,
            "open": close,
            "close": close,
            "high": close,
            "low": close,
            "volume": 1.0,
        },
    )


def test_relative_returns_use_same_common_dates(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    stock = [_record("300308", day, 100.0 + 2.0 * day) for day in range(1, 23)]
    index = [_record("sh000300", day, 100.0 + day) for day in range(1, 23)]
    store.append_records("cn_stock_daily", stock)
    store.append_records("cn_index_daily", index)

    rows = build_stock_relative_context(store, "300308", "sh000300")
    assert rows
    latest = rows[-1]
    stock_closes = [100.0 + 2.0 * day for day in range(1, 23)]
    index_closes = [100.0 + day for day in range(1, 23)]
    expected_5 = (
        stock_closes[-1] / stock_closes[-6] - 1.0
        - (index_closes[-1] / index_closes[-6] - 1.0)
    )
    expected_20 = (
        stock_closes[-1] / stock_closes[-21] - 1.0
        - (index_closes[-1] / index_closes[-21] - 1.0)
    )

    assert latest.factors["relative_sh000300_return_5"] == expected_5
    assert latest.factors["relative_sh000300_return_20"] == expected_20


def test_relative_context_requires_current_index_admissibility(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    stock = [_record("300308", day, 100.0 + day) for day in range(1, 23)]
    index = [
        _record(
            "sh000300",
            day,
            100.0 + day,
            available=f"2020-01-{day:02d}T17:00:00+08:00",
        )
        for day in range(1, 23)
    ]
    store.append_records("cn_stock_daily", stock)
    store.append_records("cn_index_daily", index)

    assert build_stock_relative_context(store, "300308", "sh000300") == ()


def test_relative_context_is_deterministic(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    stock = [_record("300308", day, 100.0 + 2.0 * day) for day in range(1, 23)]
    index = [_record("sh000300", day, 100.0 + day) for day in range(1, 23)]
    store.append_records("cn_stock_daily", stock)
    store.append_records("cn_index_daily", index)

    first = build_stock_relative_context(store, "300308", "sh000300")
    second = build_stock_relative_context(store, "300308", "sh000300")
    assert first == second
