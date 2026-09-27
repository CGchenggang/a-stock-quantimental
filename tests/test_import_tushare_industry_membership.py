import pandas as pd
import pytest

from scripts.import_tushare_industry_membership import _build_intervals, _ts_code


def _raw(rows):
    return pd.DataFrame(
        rows,
        columns=["symbol", "in_date", "out_date", "l1_code", "l1_name"],
    )


def test_ts_code_preserves_six_digit_symbol():
    assert _ts_code("000333") == "000333.SZ"
    assert _ts_code("601318") == "601318.SH"


def test_builds_pit_intervals_from_historical_membership():
    df = _raw(
        [
            ("000333", pd.Timestamp("2020-01-02"), pd.Timestamp("2021-07-01"), "801760", "家用电器"),
            ("000333", pd.Timestamp("2020-01-02"), pd.Timestamp("2021-07-01"), "801760", "家用电器"),
            ("000333", pd.Timestamp("2021-07-01"), pd.NaT, "801760", "家用电器"),
        ]
    )
    out = _build_intervals(df)
    assert len(out) == 2
    assert out.iloc[0]["effective_from"] == "2020-01-02T00:00:00+08:00"
    assert out.iloc[0]["effective_to"] == "2021-07-01T00:00:00+08:00"
    assert out.iloc[0]["available_time"] == "2020-01-03T16:00:00+08:00"
    assert out.iloc[1]["effective_to"] != out.iloc[1]["effective_to"]
    assert out.iloc[0]["source_type"] == "tushare_index_member_all_conservative_availability"


def test_conflicting_l1_same_interval_is_rejected():
    df = _raw(
        [
            ("000333", pd.Timestamp("2020-01-02"), pd.Timestamp("2021-07-01"), "801760", "家用电器"),
            ("000333", pd.Timestamp("2020-01-02"), pd.Timestamp("2021-07-01"), "801080", "电子"),
        ]
    )
    with pytest.raises(RuntimeError, match="Conflicting"):
        _build_intervals(df)
