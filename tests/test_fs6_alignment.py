"""FS6 alignment tests: the research packet carries the calibrated 6-factor
set (R4D-005) so the R4-D resolver can honestly reach CALIBRATED by REUSING
the canonical PIT industry-relative context builder.

Matrix (pre-check §6):

T1 CALIBRATED flip — synthesized membership CSV + LocalHistoricalStore with
   000001 (in frozen scope) + one same-industry peer + ≥21 trading days +
   as_of in [split_date, research_end] with the builder's exact decision_time
   format -> probability_status == "CALIBRATED", both new factor entries
   present, finite values.
T2 default-args INELIGIBLE — without membership_path/universe_symbols the
   packet is the honest 4-factor set -> feature_set_mismatch.
T3 superset INELIGIBLE — monkeypatching _FACTOR_FUNCS with one extra fake
   factor yields feature_set_mismatch (E4 treats superset as mismatch).
T4 entry shape — each new factor entry carries the RV6-5 shape:
   {value, admissible, observation_count, method}.
T5 honest absence — as_of not in context_map -> value None -> INELIGIBLE.
T6 existing — pytest tests/test_r4a_research_run.py tests/test_r4d_apply_path.py
   all green (covered as a separate TEST_COMMAND in the packet).
T7 full suite green.

Fixtures are ONLY tmp_path-synthesized. The tests NEVER read
data/industry/*.csv or validation_universe_76.txt (gitignored; CI has no
data/) — the project's most-frequent CI trap.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from astock_v2.agent import research_run as research_run_module
from astock_v2.agent.research_run import run_research
from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.information.raw_store import RawStore

INGESTED_AT = "2025-07-10T00:00:00+08:00"

# 25 business days in the [split_date, research_end] window — enough for
# lookback=20 to emit decision_times while the resolver's temporal check
# (E3) stays CALIBRATED-eligible.
_DAYS = [
    "2025-06-02", "2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06",
    "2025-06-09", "2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13",
    "2025-06-16", "2025-06-17", "2025-06-18", "2025-06-19", "2025-06-20",
    "2025-06-23", "2025-06-24", "2025-06-25", "2025-06-26", "2025-06-27",
    "2025-06-30", "2025-07-01", "2025-07-02", "2025-07-03", "2025-07-07",
]


def _daily_rows(symbol: str, base: float, step: float = 0.05) -> list:
    """25 cn_stock_daily records for ``symbol`` with PIT-compliant
    available_time (event 15:00 -> available 16:00 same day)."""
    return [
        HistoricalRecord(
            symbol=symbol,
            event_time=f"{day}T15:00:00+08:00",
            available_time=f"{day}T16:00:00+08:00",
            source="akshare:stock_zh_a_hist_tx",
            source_type="historical_vendor",
            value={"date": day, "open": base + i * step - 0.05,
                   "close": base + i * step, "high": base + i * step + 0.1,
                   "low": base + i * step - 0.1, "volume": 1_000_000.0 + i,
                   "amount": None, "adjust": ""},
            layer=DataLayer.CLEAN,
            asset_scope=AssetScope.CN_STOCK,
            revision=0,
            raw_ref="b" * 64,
            quality="SOURCE_RETURNED",
        )
        for i, day in enumerate(_DAYS)
    ]


def _write_membership_csv(path: Path) -> Path:
    """Synthesize a PIT-compliant membership CSV. Two symbols sharing one
    SW1 industry code; effective_from well before the trading window so
    every decision_time has an admissible assignment; available_time
    monotone (effective_from + 1 day) — the importer's convention."""
    csv_path = path / "membership.csv"
    header = (
        "symbol,industry_code,industry_name,level,"
        "effective_from,effective_to,available_time,"
        "source,source_type,raw_ref"
    )
    rows = [
        # 000001 -> industry "801010" from 2020-01-01 (available next day)
        "000001,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,cninfo,official,rrrr",
        # 000002 -> same industry — qualifies as a same-industry peer
        "000002,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,cninfo,official,rrrr",
    ]
    csv_path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return csv_path


def _build_store(tmp_path: Path) -> LocalHistoricalStore:
    store = LocalHistoricalStore(root=tmp_path / "data")
    store.append_records("cn_stock_daily", _daily_rows("000001", base=16.0))
    store.append_records("cn_stock_daily", _daily_rows("000002", base=11.0))
    return store


# The builder emits decision_time = "{day}T16:00:00+08:00". The LAST day in
# _DAYS is therefore the as_of that hits the context map for the full run.
AS_OF_LAST = f"{_DAYS[-1]}T16:00:00+08:00"


# ------------------------------------------------------------------- T1

def test_t1_calibrated_flip_with_full_capability_tuple(tmp_path):
    """With the 6-factor packet, the R4-D resolver flips to CALIBRATED."""
    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    # the new factors are present with finite numeric values
    for name in ("industry_relative_return_5", "industry_relative_return_20"):
        entry = result["factors"][name]
        assert entry["value"] is not None
        assert math.isfinite(entry["value"])
    # all 6 frozen feature names are present in factor_values
    factor_values = {n: info["value"] for n, info in result["factors"].items()
                     if info["value"] is not None}
    from astock_v2.model.forward_model import FROZEN_FEATURE_NAMES
    assert set(factor_values) == set(FROZEN_FEATURE_NAMES)
    # R4-D flips to CALIBRATED (no longer feature_set_mismatch)
    assert result["probability"]["probability_status"] == "CALIBRATED"
    assert isinstance(result["probability"]["probability"], float)
    assert 0.0 < result["probability"]["probability"] < 1.0
    # packet-level calibration_status mirrors the R4-D block
    assert result["research_state"]["model_output"]["calibration_status"] == "CALIBRATED"


# ------------------------------------------------------------------- T2

def test_t2_default_args_ineligible(tmp_path):
    """Without membership_path/universe_symbols the packet stays at the
    honest 4-factor set -> feature_set_mismatch."""
    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
    )
    assert result["probability"]["probability_status"] == "INELIGIBLE"
    assert result["probability"]["eligibility_reason"] == "feature_set_mismatch"
    # the new factor names are NOT present in the factors dict
    for name in ("industry_relative_return_5", "industry_relative_return_20"):
        assert name not in result["factors"]


# ------------------------------------------------------------------- T3

def test_t3_superset_ineligible(tmp_path, monkeypatch):
    """A superset of the frozen feature set is also a feature_set_mismatch
    (E4 treats superset == subset == mismatch)."""
    # add one extra fake factor to the existing 4 -> 5 base factors. With
    # the full capability tuple the run adds the 2 industry factors too,
    # producing 7 entries: a superset of the 6-name frozen feature set.
    from astock_v2.factor_contracts import FactorOutput
    from astock_v2.data_quality import DataQualitySummary

    def _fake_factor(provider_result, *, symbol, decision_time, lookback):
        return FactorOutput(
            name="fake_extra_factor", symbol=symbol, value=0.123,
            decision_time=decision_time,
            input_quality=DataQualitySummary(
                total=1, admissible=1, status_counts={},
                admissible_ratio=1.0, pit_admissible=True),
            metadata={"method": "fake", "observation_count": 20},
        )

    original = research_run_module._FACTOR_FUNCS
    patched = original + (("fake_extra_factor", _fake_factor),)
    monkeypatch.setattr(research_run_module, "_FACTOR_FUNCS", patched)

    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    assert result["probability"]["probability_status"] == "INELIGIBLE"
    assert result["probability"]["eligibility_reason"] == "feature_set_mismatch"


# ------------------------------------------------------------------- T4

def test_t4_new_factor_entry_shape(tmp_path):
    """Each industry-relative entry carries the RV6-5 shape:
    {value, admissible, observation_count, method}."""
    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    for name in ("industry_relative_return_5", "industry_relative_return_20"):
        entry = result["factors"][name]
        assert set(entry.keys()) == {
            "value", "admissible", "observation_count", "method"}
        # method is the lineage marker — the SAME module the calibration
        # used, not a reimplementation
        assert entry["method"] == "industry_relative_p13m_lineage"
        # observation_count is a non-negative integer when value is finite
        assert isinstance(entry["observation_count"], int)
        assert entry["observation_count"] >= 0
        # admissible agrees with value presence
        assert entry["admissible"] is (entry["value"] is not None)


# ------------------------------------------------------------------- T5

def test_t5_honest_absence_when_as_of_not_in_context_map(tmp_path):
    """An as_of that does not match any builder-emitted decision_time
    yields value=None for the new factors -> INELIGIBLE/feature_set_mismatch.
    No date normalization is applied (C2)."""
    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    # The builder emits decision_times at positions [20..24] of _DAYS.
    # An as_of at position 10 is inside the research window but never
    # reaches the context map's key set.
    as_of_absent = f"{_DAYS[10]}T16:00:00+08:00"
    result = run_research(
        "000001", as_of_absent,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    # the new factors ARE present in the packet (capability tuple is full)
    for name in ("industry_relative_return_5", "industry_relative_return_20"):
        entry = result["factors"][name]
        assert entry["value"] is None
        assert entry["admissible"] is False
    # resolver therefore sees fewer than 6 features -> mismatch
    assert result["probability"]["probability_status"] == "INELIGIBLE"
    assert result["probability"]["eligibility_reason"] == "feature_set_mismatch"
