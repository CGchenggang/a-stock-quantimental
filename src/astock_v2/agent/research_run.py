"""R4-A: the first evidence-backed Research Agent Loop.

One function — :func:`run_research` — executes one complete, deterministic,
auditable research run for a single ``symbol + as_of``:

    historical source
      -> P14-B RawStore (R3-A adapter, idempotent ingestion)
      -> P14-D run_query(as_of)          [accepted PIT/selection authority]
      -> P14-E create_bundle             [accepted evidence/provenance]
      -> factor inputs = the VISIBLE records only
      -> existing factors / risk engine / regime (honest UNKNOWN)
      -> ResearchPacket (existing dataclass, reused)
      -> research_state + RecommendationRecord (existing orchestrator)
      -> RecommendationLedger (existing append-only ledger)

Integration rules honored (R4-A):

- PIT is the accepted P14-D authority: only records with
  ``available_time <= as_of`` enter any computation, and every excluded
  record is carried in the result as an explicit exclusion. The run reads
  no store row directly for research purposes and adds no second PIT rule.
  The virgin-zone guard rides on ``ResearchQuery`` (assert_research_zone).
- Evidence genuinely participates: the factor input rows ARE the visible
  evidence records (joined by the P14-E identity key), and the run result
  carries the bundle so every conclusion traces to
  source/source_id/event_time/available_time/raw_payload_hash/ingestion_id.
- Missing upstream capability is labeled, never fabricated: the probability
  section is NOT_AVAILABLE (no trained model artifact exists in the
  accepted src surface), the regime section reuses the existing classifier
  which honestly returns UNKNOWN without model-grade inputs, and the
  decision action can only be RESEARCH / NO_ACTION / HOLD — never a
  fabricated BUY/SELL.
- Determinism: no wall-clock anywhere. ``ingested_at`` is caller-supplied
  and only ingestion metadata; identical (symbol, as_of, store content)
  produce byte-identical runs.
"""
from __future__ import annotations

import hashlib
from math import log, sqrt
from statistics import mean
from typing import Any

from ..data.local_store import LocalHistoricalStore
from ..factor_contracts import FactorOutput
from ..factors import (
    momentum_factor,
    trend_factor,
    volatility_factor,
    volume_ratio_factor,
)
from ..data.providers import ProviderResult
from ..regime import classify_regime
from ..recommendation import RecommendationRecord
from ..risk.engine import RiskEngine
from .orchestrator import ResearchOrchestrator
from ..information.adapters import CNStockQuoteHistoricalAdapter
from ..information.evidence import create_bundle
from ..information.raw_store import RawStore, to_information_record
from ..information.research_query import ResearchQuery, run_query

MODEL_VERSION = "r4a-minimal@1"

_FACTOR_FUNCS = (
    ("momentum", momentum_factor),
    ("volatility", volatility_factor),
    ("trend", trend_factor),
    ("volume_ratio", volume_ratio_factor),
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _visible_raw_records(raw_store: RawStore, query_result: dict) -> list:
    """Join the P14-D resolved winners back to the P14-B authoritative
    records by the frozen P14-E identity key. The join set comes from the
    query result alone — the run never re-decides visibility."""
    visible_keys = {
        (r["source"], r["source_record_id"], r["revision"], r["ingested_at"])
        for r in query_result["records"]
    }
    rows = [rec for rec in raw_store.records()
            if (rec.source, rec.source_id, rec.revision, rec.ingested_at)
            in visible_keys]
    rows.sort(key=lambda r: (r.event_time, r.source_id))
    return rows


def _factor_inputs(visible: list, as_of: str, ingested_at: str) -> ProviderResult:
    """Build the provider-shaped factor input from the VISIBLE evidence
    rows only. ``available_time`` is the latest availability among the
    used rows (<= as_of by construction), so the existing factor PIT gate
    admits it; with no visible rows the gate honestly reports MISSING_TIME
    and every factor is None."""
    rows = []
    for rec in visible:
        ohlcv = dict(rec.raw_payload.get("value") or {})
        ohlcv["event_time"] = rec.event_time
        ohlcv["source_id"] = rec.source_id
        rows.append(ohlcv)
    latest_available = max(
        (rec.available_time for rec in visible if rec.available_time),
        default=None)
    return ProviderResult(
        data={"rows": rows},
        source="cn_stock_quote",
        source_type="p14_information_layer",
        fetched_at=ingested_at,
        available_time=latest_available,
    )


def _max_drawdown(closes: list[float]) -> float:
    peak = None
    mdd = 0.0
    for close in closes:
        peak = close if peak is None else max(peak, close)
        if peak > 0:
            mdd = min(mdd, close / peak - 1.0)
    return mdd


def run_research(symbol: str, as_of: str, *,
                 historical_store: LocalHistoricalStore | None = None,
                 raw_store: RawStore,
                 ingested_at: str | None = None,
                 lookback: int = 20) -> dict:
    """Run one complete evidence-backed research loop.

    ``historical_store`` (optional) triggers an idempotent R3-A ingestion
    into ``raw_store`` first; omit it to run against an already-ingested
    store. Everything downstream is the accepted P14-D/P14-E authority
    chain plus the existing factor/risk/regime/orchestrator/ledger
    components — nothing here re-decides visibility or selection.
    """
    if historical_store is not None:
        if not ingested_at:
            raise ValueError(
                "ingested_at is required when ingesting from a historical "
                "store (deterministic runs pin the ingestion timestamp)")
        adapter = CNStockQuoteHistoricalAdapter(
            historical_store, symbols=[symbol], ingested_at=ingested_at)
        adapter.ingest(raw_store, ingested_at)

    authoritative = raw_store.records()
    info = [to_information_record(r) for r in authoritative]
    # ResearchQuery fails fast on virgin-zone as_of (assert_research_zone).
    query_result = run_query(info, ResearchQuery(
        entity=symbol, information_type="STOCK", as_of=as_of))

    bundle = create_bundle(query_result, authoritative)

    visible = _visible_raw_records(raw_store, query_result)
    provider_result = _factor_inputs(visible, as_of, ingested_at or "")

    factors: dict[str, Any] = {}
    for name, func in _FACTOR_FUNCS:
        out: FactorOutput = func(
            provider_result, symbol=symbol, decision_time=as_of,
            lookback=lookback)
        factors[name] = {
            "value": out.value,
            "admissible": out.admissible,
            "observation_count": (out.metadata or {}).get("observation_count"),
            "method": (out.metadata or {}).get("method"),
        }

    closes = [rec.value for rec in visible
              if isinstance(rec.value, (int, float)) and rec.value > 0]
    realized_drawdown = _max_drawdown(closes) if len(closes) >= 2 else None
    volatility = factors["volatility"]["value"]
    quality_complete = sum(
        1 for e in bundle["evidence"] if e.get("evidence_id"))
    quality_score = (quality_complete / len(bundle["evidence"])
                     if bundle["evidence"] else 0.0)

    risk = RiskEngine().evaluate(
        data_quality=quality_score,
        expected_volatility=volatility if volatility is not None else 0.0,
        expected_drawdown=realized_drawdown if realized_drawdown is not None else 0.0,
        liquidity_ok=bool(closes) and all(
            (rec.raw_payload.get("value") or {}).get("volume") not in (None, 0)
            for rec in visible),
    )
    regime = classify_regime({})  # honest UNKNOWN: no model-grade market inputs
    probability = {
        "status": "NOT_AVAILABLE",
        "reason": "no trained model artifact exists in the accepted src "
                  "surface; P13-Q calibrators are research-only artifacts",
    }

    evidence_ids = tuple(e["evidence_id"] for e in bundle["evidence"])
    packet = ResearchOrchestrator().build(
        symbol=symbol,
        decision_time=as_of,
        market={"regime": regime},
        stock={
            "supporting_evidence": [
                f"{e['source_id']}@{e['available_time']}"
                for e in bundle["evidence"]],
            "contradictory_evidence": [],
            "missing_evidence": [
                f"excluded:{x['source_id']}:{x['reason']}"
                for x in bundle["exclusions"]],
        },
        factors=factors,
        events=[],
        model={
            "status": probability["status"],
            "reason": probability["reason"],
            "calibration_status": "NOT_CALIBRATED",
            "p_up": {},
            "confidence": None,
            "provenance": (
                f"result_id:{query_result['result_id']}",
                f"bundle_id:{bundle['bundle_id']}",
            ),
        },
        risk={"flags": list(risk.flags), "allowed": risk.allowed,
              "max_loss_proxy": risk.max_loss_proxy},
        data_quality={
            "score": quality_score,
            "basis": "p14e_provenance_completeness",
            "visible": query_result["counts"]["visible"],
            "excluded": query_result["counts"]["excluded"],
            "examined": query_result["counts"]["examined"],
        },
    )
    orchestrator = ResearchOrchestrator()
    state = orchestrator.research_state(packet)
    run_id = _sha("|".join([
        symbol, as_of, query_result["result_id"], bundle["bundle_id"]]))[:16]
    record = orchestrator.recommendation_record(
        packet, record_id=f"r4a-{run_id}", model_version=MODEL_VERSION)

    return {
        "run_id": run_id,
        "symbol": symbol,
        "as_of": as_of,
        "result_id": query_result["result_id"],
        "bundle_id": bundle["bundle_id"],
        "evidence": bundle["evidence"],
        "exclusions": bundle["exclusions"],
        "counts": query_result["counts"],
        "factors": factors,
        "regime": regime,
        "probability": probability,
        "risk": {"flags": list(risk.flags), "allowed": risk.allowed,
                 "max_loss_proxy": risk.max_loss_proxy,
                 "realized_drawdown": realized_drawdown},
        "data_quality": packet.data_quality,
        "research_state": state,
        "recommendation": record.as_dict(),
        "factor_input_source_ids": [rec.source_id for rec in visible],
        "evidence_ids": list(evidence_ids),
    }


def append_to_ledger(run_result: dict, ledger, ingested_at: str) -> dict:
    """Append the run's recommendation to the existing ledger, carrying the
    research/evidence identity in ``input_snapshot`` for later replay."""
    record = RecommendationRecord(**{
        **run_result["recommendation"],
        "provenance": tuple(run_result["recommendation"]["provenance"]),
    })
    event = ledger.append(
        record,
        feature_version=MODEL_VERSION,
        input_snapshot={
            "run_id": run_result["run_id"],
            "result_id": run_result["result_id"],
            "bundle_id": run_result["bundle_id"],
            "as_of": run_result["as_of"],
            "ingested_at": ingested_at,
            "evidence_ids": run_result["evidence_ids"],
            "factor_input_source_ids": run_result["factor_input_source_ids"],
        },
    )
    return event
