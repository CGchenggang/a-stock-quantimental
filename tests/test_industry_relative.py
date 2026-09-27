from datetime import datetime, timedelta, timezone

from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.industry_relative import build_stock_industry_relative_context


TZ = timezone(timedelta(hours=8))


def _record(symbol: str, day: int, close: float) -> HistoricalRecord:
    date = f"2020-01-{day:02d}"
    return HistoricalRecord(
        symbol=symbol,
        event_time=f"{date}T15:00:00+08:00",
        available_time=f"{date}T16:00:00+08:00",
        source="test",
        source_type="test",
        value={"close": close},
    )


def _membership_csv(tmp_path):
    path = tmp_path / "membership.csv"
    path.write_text(
        "symbol,industry_code,industry_name,level,effective_from,effective_to,available_time,source,source_type,raw_ref\n"
        "000001,SW1:A,A,l1,2020-01-01T00:00:00+08:00,2020-01-23T00:00:00+08:00,2020-01-02T16:00:00+08:00,test,test,r1\n"
        "000001,SW1:A,A,l1,2020-01-23T00:00:00+08:00,,2020-01-24T16:00:00+08:00,test,test,r2\n"
        "000333,SW1:A,A,l1,2020-01-01T00:00:00+08:00,2020-01-22T00:00:00+08:00,2020-01-02T16:00:00+08:00,test,test,r3\n"
        "000333,SW1:B,B,l1,2020-01-22T00:00:00+08:00,,2020-01-23T16:00:00+08:00,test,test,r4\n"
        "000651,SW1:B,B,l1,2020-01-01T00:00:00+08:00,,2020-01-02T16:00:00+08:00,test,test,r5\n",
        encoding="utf-8",
    )
    return path


def test_industry_relative_context_uses_pit_membership(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    target = [_record("000001", day, 100.0 + day) for day in range(1, 25)]
    peer = [_record("000333", day, 100.0 + 2.0 * day) for day in range(1, 25)]
    outsider = [_record("000651", day, 100.0 + 10.0 * day) for day in range(1, 25)]
    store.append_records("cn_stock_daily", target + peer + outsider)

    rows = build_stock_industry_relative_context(
        store,
        _membership_csv(tmp_path),
        "000001",
        ("000001", "000333", "000651"),
    )

    assert rows
    by_day = {row.decision_time[:10]: row for row in rows}
    # On 2020-01-22 the peer's new membership is effective but not yet
    # available, so the old SW1:A assignment remains admissible.
    assert by_day["2020-01-22"].industry_code == "SW1:A"
    # On 2020-01-23 the peer's new assignment is available, so it leaves the
    # target's benchmark. The target itself remains SW1:A until 2020-01-24.
    assert by_day["2020-01-23"].industry_code == "SW1:A"


def test_industry_relative_context_excludes_other_industries(tmp_path):
    store = LocalHistoricalStore(tmp_path)
    target = [_record("000001", day, 100.0 + day) for day in range(1, 23)]
    peer = [_record("000333", day, 100.0 + 2.0 * day) for day in range(1, 23)]
    outsider = [_record("000651", day, 1000.0 + 50.0 * day) for day in range(1, 23)]
    store.append_records("cn_stock_daily", target + peer + outsider)

    rows = build_stock_industry_relative_context(
        store,
        _membership_csv(tmp_path),
        "000001",
        ("000001", "000333", "000651"),
    )

    assert rows
    latest = rows[-1]
    # The factor is finite and the extreme outsider series cannot dominate it.
    assert latest.factors["industry_relative_return_5"] < 0.0
    assert latest.factors["industry_relative_return_20"] < 0.0
