from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.market_context import build_index_market_context


def _record(day: int, close: float, available: str | None = None):
    date = f"2020-01-{day:02d}"
    return HistoricalRecord(
        symbol="sh000300",
        event_time=f"{date}T15:00:00+08:00",
        available_time=available or f"{date}T16:00:00+08:00",
        source="test",
        source_type="test",
        value={"date": date, "open": close, "close": close, "high": close, "low": close, "volume": 1.0},
    )


def test_market_context_uses_expected_return_and_sma(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    records = [_record(day, 100.0 + day) for day in range(1, 23)]
    store.append_records("cn_index_daily", records)

    rows = build_index_market_context(store, "sh000300")
    assert rows
    latest = rows[-1]
    closes = [100.0 + day for day in range(1, 23)]
    expected_5 = closes[-1] / closes[-6] - 1.0
    expected_20 = closes[-1] / closes[-21] - 1.0
    expected_sma = sum(closes[-20:]) / 20.0

    assert latest.factors["sh000300_return_5"] == expected_5
    assert latest.factors["sh000300_return_20"] == expected_20
    assert latest.factors["sh000300_close_vs_sma20"] == closes[-1] / expected_sma - 1.0
    assert latest.factors["sh000300_volatility_20"] > 0


def test_market_context_requires_pit_admissibility(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    records = []
    for day in range(1, 23):
        date = f"2020-01-{day:02d}"
        records.append(
            _record(day, 100.0 + day, available=f"{date}T17:00:00+08:00")
        )
    store.append_records("cn_index_daily", records)

    assert build_index_market_context(store, "sh000300") == ()


def test_market_context_is_deterministic(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    records = [_record(day, 100.0 + day) for day in range(1, 23)]
    store.append_records("cn_index_daily", records)

    first = build_index_market_context(store, "sh000300")
    second = build_index_market_context(store, "sh000300")
    assert first == second
