from dataclasses import replace

from astock_v2.data.catalog import HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.data.providers import ProviderResult
from astock_v2.factors import compute_factor
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


def _reference_factor_rows(records, symbol="300308", lookback=20):
    """Verbatim pre-optimization algorithm: full rescan per decision day.

    Kept as the executable specification that the windowed fast path must
    match bit for bit on every input, healthy or adversarial.
    """
    ordered = sorted(records, key=lambda r: (r.event_time, r.revision))
    event_times = sorted({record.event_time for record in ordered})
    by_event = {}
    for record in ordered:
        by_event.setdefault(record.event_time, []).append(record)
    factor_names = ("momentum", "volatility", "trend", "volume_ratio")
    rows = []
    for index in range(lookback, len(event_times) - 1):
        event_time = event_times[index]
        decision_time = f"{event_time[:10]}T16:00:00+08:00"
        candidates = [r for r in by_event[event_time] if r.admissible_at(decision_time)]
        if not candidates:
            continue
        current = max(candidates, key=lambda r: r.revision)
        admitted = []
        for prior_event in event_times[: index + 1]:
            prior = [r for r in by_event[prior_event] if r.admissible_at(decision_time)]
            if prior:
                admitted.append(max(prior, key=lambda r: r.revision))
        if len(admitted) < lookback + 1:
            continue
        provider = ProviderResult(
            data=[dict(r.value) for r in admitted],
            source="local:cn_stock_daily",
            source_type="local_historical",
            fetched_at="",
            available_time=decision_time,
        )
        factors = {}
        for name in factor_names:
            output = compute_factor(
                name, provider, symbol=symbol, decision_time=decision_time, lookback=lookback
            )
            if not output.admissible or output.value is None:
                break
            factors[name] = float(output.value)
        if len(factors) != len(factor_names):
            continue
        today_close = float(current.value["close"])
        next_record = max(by_event[event_times[index + 1]], key=lambda r: r.revision)
        next_close = float(next_record.value["close"])
        if today_close <= 0:
            continue
        next_return = next_close / today_close - 1.0
        rows.append(
            (decision_time, factors, int(next_return > 0), next_return, current.event_time)
        )
    return rows


def _observed_factor_rows(result):
    return [
        (row.decision_time, row.factors, row.label, row.next_return, row.source_event_time)
        for row in result
    ]


def test_windowed_fast_path_matches_full_rescan_reference(tmp_path):
    """Adversarial coverage: junk in early history, inside the trailing
    window (forces the fallback path), and after it; plus same-day late
    revisions and cross-day delayed availability."""
    store = LocalHistoricalStore(tmp_path)
    rows = [record(f"2026-01-{day:02d}", float(day)) for day in range(1, 30)]
    # early-history junk: exercises the fast path with an unclean prefix
    rows[1] = record("2026-01-02", None)            # close None
    rows[2] = record("2026-01-03", 0.0)             # zero close
    rows[3] = record("2026-01-04", -5.0)            # negative close
    rows[4] = record("2026-01-05", "12.5")          # string close
    rows[5] = record("2026-01-06", 6.0)             # volume None
    rows[5].value["volume"] = None
    # junk inside the trailing window of several decisions: fallback path
    rows[15] = record("2026-01-16", None)
    rows[18] = record("2026-01-19", 0.0)
    # same-day late revisions and a next-day availability
    rows.append(record("2026-01-21", 99.0, revision=1, available="18:00:00"))
    rows.append(replace(record("2026-01-22", 88.0, revision=1),
                        available_time="2026-01-23T16:00:00+08:00"))
    store.append_records("cn_stock_daily", rows)

    records = store.read_records("cn_stock_daily", "300308")
    observed = _observed_factor_rows(build_local_factor_rows(store, "300308", lookback=20))
    reference = _reference_factor_rows(records)

    assert observed, "pipeline produced no rows"
    assert observed == reference
