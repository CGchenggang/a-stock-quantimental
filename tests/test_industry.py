from datetime import datetime, timezone

import pytest

from astock_v2.industry import (
    IndustryMembership,
    admissible_industry,
    coverage_start,
    load_industry_membership_csv,
    validate_membership_history,
)

TZ = timezone.utc


def row(code, start, end, available=None):
    start_dt = datetime.fromisoformat(start).replace(tzinfo=TZ)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=TZ) if end else None
    return IndustryMembership(
        symbol="000001",
        industry_code=code,
        industry_name=code,
        level="L1",
        effective_from=start_dt,
        effective_to=end_dt,
        available_time=datetime.fromisoformat(available).replace(tzinfo=TZ) if available else start_dt,
        source="test",
        source_type="vendor_effective_date",
    )


def test_current_interval_is_selected():
    memberships = [row("A", "2020-01-01T00:00:00", "2021-01-01T00:00:00"), row("B", "2021-01-01T00:00:00", None)]
    got = admissible_industry(memberships, "000001", datetime(2021, 6, 1, tzinfo=TZ), datetime(2021, 6, 1, 16, tzinfo=TZ))
    assert got is not None
    assert got.industry_code == "B"


def test_future_membership_is_not_admissible():
    memberships = [row("B", "2021-01-01T00:00:00", None, "2021-01-01T16:00:00")]
    got = admissible_industry(memberships, "000001", datetime(2020, 12, 31, 15, tzinfo=TZ), datetime(2020, 12, 31, 16, tzinfo=TZ))
    assert got is None


def test_overlapping_history_is_rejected():
    memberships = [row("A", "2020-01-01T00:00:00", "2021-06-01T00:00:00"), row("B", "2021-05-01T00:00:00", None)]
    with pytest.raises(ValueError, match="overlapping"):
        validate_membership_history(memberships)


def test_current_day_requires_admissibility():
    memberships = [row("A", "2020-01-01T00:00:00", None, "2020-01-22T16:00:00")]
    got = admissible_industry(memberships, "000001", datetime(2020, 1, 22, 15, tzinfo=TZ), datetime(2020, 1, 22, 15, 59, tzinfo=TZ))
    assert got is None


def test_csv_loader_parses_open_interval_and_coverage(tmp_path):
    csv_path = tmp_path / "membership.csv"
    csv_path.write_text(
        "symbol,industry_code,industry_name,level,effective_from,effective_to,available_time,source,source_type,raw_ref\n"
        "300308,SW1:通信,通信,l1,2021-07-30T00:00:00+08:00,,2021-07-31T16:00:00+08:00,cninfo,cninfo_effective_date_conservative_availability,ref\n",
        encoding="utf-8",
    )
    memberships = load_industry_membership_csv(csv_path)
    assert len(memberships) == 1
    assert memberships[0].effective_to is None
    assert memberships[0].available_time > memberships[0].effective_from
    starts = coverage_start(memberships)
    assert starts["300308"] == datetime(2021, 7, 29, 16, tzinfo=TZ)


def test_csv_loader_rejects_missing_columns(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("symbol,industry_code\n300308,SW1:通信\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_industry_membership_csv(csv_path)
