"""Tests for the read-only LLM research explanation layer.

T1 mock LLM produces a valid report
T2 schema validation (missing sections/metadata rejected)
T3 no evidence -> refuse to explain (no fabrication)
T4 LLM numbers must exist in the source data (fabrication -> fallback)
T5 LLM explanation never writes the ledger
T6 explain/ imports only ledger/recommendation + stdlib (architecture)
T7 no broker/order/trade path in explain/
T8 a historical (persisted) run_id can be explained from the ledger

Fixtures are tmp_path-synthesized only (no data/ reads) — the same
strategy as tests/test_fs6_alignment.py.
"""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from astock_v2.agent.research_run import append_to_ledger, run_research
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.explain import (
    explain_ledger_record,
    explain_run,
    render_report_markdown,
)
from astock_v2.explain import report_schema
from astock_v2.explain.llm_adapter import (
    MockExplanationLLM,
    create_adapter,
)
from astock_v2.information.raw_store import RawStore
from astock_v2.ledger import RecommendationLedger

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPLAIN_DIR = REPO_ROOT / "src" / "astock_v2" / "explain"

AS_OF = "2025-07-07T16:00:00+08:00"  # inside [split_date, research_end]
INGESTED_AT = "2026-10-08T20:00:00+08:00"


def _synthetic_environment(tmp_path: Path):
    """Synthesize store + membership for one full R4-A run:
    000001/000002 in the same industry, ~30 trading days, PIT-compliant
    available_time, all values deterministic."""
    from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord

    store = LocalHistoricalStore(tmp_path / "data")
    raw = RawStore(tmp_path / "raw_records.jsonl")

    days: list[str] = []
    day = datetime(2025, 6, 2, tzinfo=timezone.utc)
    while len(days) < 30:
        if day.weekday() < 5:
            days.append(day.strftime("%Y-%m-%d"))
        day += timedelta(days=1)

    def records_for(symbol: str, base: float):
        return [
            HistoricalRecord(
                symbol=symbol,
                event_time=f"{day}T15:00:00+08:00",
                available_time=f"{day}T16:00:00+08:00",
                source="test:fixture", source_type="historical_vendor",
                value={"date": day, "open": base + index * 0.01 - 0.01,
                       "close": base + index * 0.01,
                       "high": base + index * 0.01 + 0.05,
                       "low": base + index * 0.01 - 0.05,
                       "volume": 1_000_000.0 + index, "amount": None,
                       "adjust": ""},
                layer=DataLayer.CLEAN, asset_scope=AssetScope.CN_STOCK,
                revision=0, raw_ref=f"{symbol}-{index}".ljust(64, "0"),
                quality="SOURCE_RETURNED",
            )
            for index, day in enumerate(days)
        ]

    store.append_records("cn_stock_daily", records_for("000001", 10.0))
    store.append_records("cn_stock_daily", records_for("000002", 20.0))

    membership = tmp_path / "membership.csv"
    # same PIT-compliant shape as tests/test_fs6_alignment.py:
    # aware timestamps, empty effective_to, industry 801010 shared
    membership_rows = [
        "000001,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,test:fixture,official,m-000001",
        "000002,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,test:fixture,official,m-000002",
    ]
    header = ("symbol,industry_code,industry_name,level,"
              "effective_from,effective_to,available_time,"
              "source,source_type,raw_ref")
    membership.write_text("\n".join([header, *membership_rows]) + "\n",
                          encoding="utf-8")
    return store, raw, membership


def _full_run(tmp_path: Path):
    """One real R4-A run + ledger append (the R4-A write path)."""
    store, raw, membership = _synthetic_environment(tmp_path)
    run = run_research(
        "000001", AS_OF, historical_store=store, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership,
        universe_symbols=("000001", "000002"))
    ledger = RecommendationLedger(tmp_path / "ledger.jsonl")
    append_to_ledger(run, ledger, INGESTED_AT)
    return run, ledger


# ------------------------------------------------------------ T1

def test_t1_mock_llm_produces_valid_report(tmp_path):
    run, ledger = _full_run(tmp_path)
    report = explain_run(run, ledger=ledger, llm=MockExplanationLLM(),
                         generated_at="2026-10-09T12:00:00+00:00")
    assert report["metadata"]["run_id"] == run["run_id"]
    assert report["metadata"]["prompt_version"] == "explain-v1"
    assert report["metadata"]["llm_model"] == "mock-explainer-v1"
    assert report["metadata"]["report_schema_version"] == "1"
    markdown = render_report_markdown(report)
    assert "# Research Explanation Report" in markdown
    assert report["narrative"]["factor_interpretation"]["source"] == "llm"
    # every required section present (11-section contract)
    assert set(report["sections"]) >= set(report_schema.REQUIRED_SECTIONS)
    assert report["provenance"], "provenance entries must exist"


# ------------------------------------------------------------ T2

def test_t2_schema_validation_rejects_incomplete_report():
    with pytest.raises(ValueError):
        report_schema.validate_report(
            {"kind": report_schema.REPORT_KIND, "metadata": {}})
    good = {"kind": report_schema.REPORT_KIND,
            "report_schema_version": report_schema.REPORT_SCHEMA_VERSION,
            "run_id": "x",
            "metadata": {key: "v" for key in report_schema.REQUIRED_METADATA},
            "sections": {name: {} for name in report_schema.REQUIRED_SECTIONS},
            "provenance": []}
    report_schema.validate_report(good)  # no raise


# ------------------------------------------------------------ T3

def test_t3_no_evidence_refuses_to_explain():
    run = {"run_id": "run-x", "result_id": "r", "bundle_id": "b",
           "symbol": "000001", "as_of": AS_OF,
           "evidence_ids": [], "probability": {}, "factors": {},
           "risk": {}, "recommendation": {}}
    with pytest.raises(ValueError, match="no evidence"):
        explain_run(run, llm=MockExplanationLLM())


# ------------------------------------------------------------ T4

def test_t4_fabricated_llm_numbers_fall_back_deterministic(tmp_path):
    run, ledger = _full_run(tmp_path)
    fabricator = MockExplanationLLM(behavior="fabricating")
    report = explain_run(run, ledger=ledger, llm=fabricator,
                         generated_at="2026-10-09T12:00:00+00:00")
    narrative = report["narrative"]["factor_interpretation"]
    assert narrative["source"] == "deterministic_fallback"
    assert "0.123456" not in narrative["text"]
    # the structured sections are untouched by the rejected narrative
    assert report["sections"]["factor_interpretation"][
        "momentum"]["value"] == run["factors"]["momentum"]["value"]
    # the faithful adapter still passes the same guard
    faithful = explain_run(run, ledger=ledger, llm=MockExplanationLLM(),
                           generated_at="2026-10-09T12:00:00+00:00")
    assert faithful["narrative"]["factor_interpretation"]["source"] == "llm"


# ------------------------------------------------------------ T5

def test_t5_explanation_never_writes_ledger(tmp_path):
    run, ledger = _full_run(tmp_path)
    before_rows = len(ledger.load())
    before_raw = len(ledger.path.read_text(encoding="utf-8").splitlines())
    explain_run(run, ledger=ledger, llm=MockExplanationLLM())
    explain_ledger_record(ledger=ledger, run_id=run["run_id"],
                          llm=MockExplanationLLM())
    assert len(ledger.load()) == before_rows
    assert len(ledger.path.read_text(encoding="utf-8").splitlines()) == before_raw


# ------------------------------------------------------ T6 architecture

def test_t6_explain_imports_are_read_only():
    allowed = {"astock_v2.ledger", "astock_v2.recommendation",
               "astock_v2.explain"}
    forbidden_fragments = ("forward_model", "apply_path", "registry",
                           "features", "risk", "factors",
                           "research_query", "information", "pit")
    for path in sorted(EXPLAIN_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("astock_v2"), (
                        f"{path.name}: absolute astock_v2 import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level == 0:  # absolute: never the quant package
                    assert not module.startswith("astock_v2"), (
                        f"{path.name}: absolute astock_v2 import {module}")
                    continue
                # relative resolution: level=1 -> astock_v2.explain.*,
                # level=2 -> astock_v2.* (the package's own imports)
                if node.level == 1:
                    resolved = "astock_v2.explain" + (f".{module}" if module else "")
                else:
                    resolved = "astock_v2" + (f".{module}" if module else "")
                assert any(resolved == a or resolved.startswith(a + ".")
                           for a in allowed), (
                        f"{path.name}: forbidden relative import {module}")
                for fragment in forbidden_fragments:
                    assert fragment not in module, (
                        f"{path.name}: forbidden module {module}")
            if isinstance(node, ast.Call):
                assert getattr(node.func, "id", "") != "__import__", (
                    f"{path.name}: dynamic __import__ forbidden")


def test_t7_no_broker_order_trade_path_in_explain():
    for path in sorted(EXPLAIN_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for fragment in ("broker", "place_order", "execute_trade",
                         "real_money", "order_api"):
            assert fragment not in text, f"{path.name} mentions {fragment}"


# ------------------------------------------------------------ T8

def test_t8_historical_run_id_explains_from_ledger(tmp_path):
    run, ledger = _full_run(tmp_path)
    report = explain_ledger_record(ledger=ledger, run_id=run["run_id"],
                                   llm=MockExplanationLLM(),
                                   generated_at="2026-10-09T12:00:00+00:00")
    assert report["metadata"]["run_id"] == run["run_id"]
    assert report["metadata"]["source"] == "ledger"
    # honest limitation: factor values are not persisted in the ledger
    assert report["sections"]["factor_interpretation"]["values"] is None
    assert "not persisted" in report["sections"]["factor_interpretation"]["note"]
    # provenance carries the persisted probability block
    fields = {entry["source_field"] for entry in report["provenance"]}
    assert any("probability_interpretation" in f for f in fields)
    with pytest.raises(ValueError):
        explain_ledger_record(ledger=ledger, run_id="nonexistent")


# ------------------------------------------------ adapter factory guard

def test_adapter_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="runtime-optional"):
        create_adapter("some-real-provider")
    assert create_adapter("mock").model_name == "mock-explainer-v1"
