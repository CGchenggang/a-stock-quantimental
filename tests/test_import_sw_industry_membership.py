import pandas as pd
import pytest

from scripts.import_sw_industry_membership import _build_intervals


def _raw(rows):
    return pd.DataFrame(
        rows,
        columns=["symbol", "start_date", "industry_code", "update_time"],
    )


def test_builds_l1_intervals_from_sw_code_prefix():
    out = _build_intervals(
        _raw(
            [
                ("000333", pd.Timestamp("2019-01-02"), "270101", pd.NaT),
                ("000333", pd.Timestamp("2021-07-30"), "270201", pd.NaT),
            ]
        )
    )
    assert len(out) == 2
    assert out.iloc[0]["industry_code"] == "SW1:270000"
    assert out.iloc[0]["effective_from"] == "2019-01-02T00:00:00+08:00"
    assert out.iloc[0]["effective_to"] == "2021-07-30T00:00:00+08:00"
    assert out.iloc[0]["available_time"] == "2019-01-03T16:00:00+08:00"


def test_same_date_duplicate_l1_is_deduplicated():
    out = _build_intervals(
        _raw(
            [
                ("000333", pd.Timestamp("2021-07-30"), "270101", pd.NaT),
                ("000333", pd.Timestamp("2021-07-30"), "270102", pd.NaT),
            ]
        )
    )
    assert len(out) == 1
    assert out.iloc[0]["industry_code"] == "SW1:270000"


def test_same_date_conflicting_l1_is_rejected():
    out = _raw(
        [
            ("000333", pd.Timestamp("2021-07-30"), "270101", pd.NaT),
            ("000333", pd.Timestamp("2021-07-30"), "280101", pd.NaT),
        ]
    )
    with pytest.raises(RuntimeError, match="Conflicting"):
        _build_intervals(out)
