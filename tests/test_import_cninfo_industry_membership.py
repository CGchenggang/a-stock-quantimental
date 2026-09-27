from datetime import datetime, timezone

import pandas as pd
import pytest

from scripts.import_cninfo_industry_membership import _build_intervals


def _raw(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "symbol", "change_date", "industry_l1_name",
        ],
    )


def test_builds_non_overlapping_intervals():
    df = _raw(
        [
            ("300308", pd.Timestamp("2021-01-05"), "电子"),
            ("300308", pd.Timestamp("2022-03-01"), "计算机"),
        ]
    )
    out = _build_intervals(df)
    assert len(out) == 2
    assert out.iloc[0]["effective_from"] == "2021-01-05T00:00:00+08:00"
    assert out.iloc[0]["effective_to"] == "2022-03-01T00:00:00+08:00"
    assert out.iloc[0]["available_time"] == "2021-01-06T16:00:00+08:00"
    assert out.iloc[1]["effective_to"] != out.iloc[1]["effective_to"]


def test_same_date_duplicate_same_l1_is_deduplicated():
    df = _raw(
        [
            ("300308", pd.Timestamp("2021-01-05"), "电子"),
            ("300308", pd.Timestamp("2021-01-05"), "电子"),
        ]
    )
    out = _build_intervals(df)
    assert len(out) == 1


def test_same_date_conflicting_l1_is_rejected():
    df = _raw(
        [
            ("300308", pd.Timestamp("2021-01-05"), "电子"),
            ("300308", pd.Timestamp("2021-01-05"), "计算机"),
        ]
    )
    with pytest.raises(RuntimeError, match="Conflicting"):
        _build_intervals(df)
