import pytest

from astock_v2.compat import LegacyObservation
from astock_v2.data.legacy_adapter import datapoint_from_legacy


def test_legacy_adapter_requires_valid_point_in_time_order():
    obs = LegacyObservation(
        symbol="000001",
        value={"price": 10.0},
        source="daily_close_fallback",
        fetched_at="2026-09-26T10:00:00+00:00",
        fallback=True,
    )
    dp = datapoint_from_legacy(
        obs,
        event_time="2026-09-25T15:00:00+00:00",
        available_time="2026-09-26T10:00:00+00:00",
        quality="C",
    )
    assert dp.source.endswith(":fallback")
    assert dp.source_type == "legacy_adapter"
    assert dp.event_time < dp.available_time


def test_legacy_adapter_rejects_inconsistent_timestamps():
    obs = LegacyObservation(
        symbol="000001",
        value={"price": 10.0},
        source="legacy_unknown",
        fetched_at="2026-09-25T09:00:00+00:00",
    )
    with pytest.raises(ValueError):
        datapoint_from_legacy(
            obs,
            event_time="2026-09-25T10:00:00+00:00",
            available_time="2026-09-25T09:00:00+00:00",
        )
