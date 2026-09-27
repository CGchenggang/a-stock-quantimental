from pathlib import Path

import pytest

from astock_v2.industry_loader import load_industry_memberships


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_load_and_validate_industry_membership(tmp_path):
    path = _write(
        tmp_path / "membership.csv",
        """symbol,industry_code,industry_name,level,effective_from,effective_to,available_time,source,source_type,raw_ref
300308,SW1:通信,通信,l1,2021-07-30T00:00:00+08:00,,2021-07-31T16:00:00+08:00,cninfo,test,ref1
""",
    )

    rows = load_industry_memberships(path)

    assert len(rows) == 1
    assert rows[0].industry_name == "通信"
    assert rows[0].available_time.isoformat() == "2021-07-31T16:00:00+08:00"


def test_loader_does_not_accept_overlapping_intervals(tmp_path):
    path = _write(
        tmp_path / "membership.csv",
        """symbol,industry_code,industry_name,level,effective_from,effective_to,available_time,source,source_type,raw_ref
300308,SW1:通信,通信,l1,2021-07-30T00:00:00+08:00,2022-01-01T00:00:00+08:00,2021-07-31T16:00:00+08:00,cninfo,test,ref1
300308,SW1:计算机,计算机,l1,2021-12-01T00:00:00+08:00,,2021-12-02T16:00:00+08:00,cninfo,test,ref2
""",
    )

    with pytest.raises(ValueError, match="overlapping industry intervals"):
        load_industry_memberships(path)
