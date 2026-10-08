"""Read-only LLM research explanation layer.

Single-direction data flow, enforced by construction:

    ResearchPacket / Evidence / Probability / Factors / Risk /
    Recommendation / Ledger read view
        ↓  (structured payload — the only number source)
    LLM (narrative prose only, numeric-consistency guarded)
        ↓
    Research Explanation Report (markdown/JSON)

The layer has NO decision authority and NO write path: it never appends
to the ledger, never produces a RecommendationRecord, and never imports
any quant mutation surface (the architecture test pins the import graph
to astock_v2.ledger/astock_v2.recommendation + this package only).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..ledger import RecommendationLedger
from .llm_adapter import ExplanationLLM, MockExplanationLLM
from .prompt_builder import PROMPT_VERSION, build_prompt
from . import report_schema
from .report_schema import (
    REPORT_KIND,
    REPORT_SCHEMA_VERSION,
    collect_numeric_universe,
    narrative_numbers_consistent,
    render_markdown,
    validate_report,
)

__all__ = [
    "explain_run",
    "explain_ledger_record",
    "explain_payload",
    "render_report_markdown",
]


def explain_run(run_result: dict, *, ledger: RecommendationLedger | None = None,
                llm: ExplanationLLM | None = None,
                generated_at: str | None = None,
                ledger_context_limit: int = 20) -> dict:
    """Explain one research run from its in-memory result.

    All numbers come from ``run_result`` (and, when supplied, the
    ledger read view for that run). A missing/empty evidence set refuses
    generation (no evidence → no honest explanation). LLM prose that
    references a number absent from the source payload is REJECTED and
    replaced by deterministic prose (fail-closed, T3/T4).
    """
    evidence_ids = list(run_result.get("evidence_ids") or [])
    if not evidence_ids:
        raise ValueError(
            "refusing to explain: the run carries no evidence; an "
            "explanation without evidence would be fabricated")
    payload, narrative_sections = _payload_from_run(run_result, ledger)
    payload["evidence_summary"]["evidence_ids"] = evidence_ids
    return _assemble(payload, narrative_sections, run_result, ledger=ledger,
                     llm=llm, generated_at=generated_at,
                     ledger_context_limit=ledger_context_limit)


def explain_ledger_record(*, ledger: RecommendationLedger,
                          run_id: str | None = None,
                          record_id: str | None = None,
                          llm: ExplanationLLM | None = None,
                          generated_at: str | None = None,
                          ledger_context_limit: int = 20) -> dict:
    """Explain a historical run from its persisted ledger row.

    Honest limitation: the ledger persists the recommendation, the R4-D
    probability block, evidence ids and the P14-F registry identity —
    but not the full factor/risk tables. Those sections are reported as
    NOT PERSISTED IN LEDGER rather than approximated."""
    rows = ledger.query()
    row = None
    for candidate in rows:
        snapshot = candidate.get("input_snapshot") or {}
        if (run_id and snapshot.get("run_id") == run_id) or \
           (record_id and candidate.get("record_id") == record_id):
            row = candidate
            break
    if row is None:
        raise ValueError(
            f"no ledger recommendation matches run_id={run_id!r} "
            f"record_id={record_id!r}")
    probability = (row.get("input_snapshot") or {}).get("r4d_probability") or {}
    payload = {
        "run_identity": {
            "run_id": (row.get("input_snapshot") or {}).get("run_id"),
            "result_id": (row.get("input_snapshot") or {}).get("result_id"),
            "bundle_id": (row.get("input_snapshot") or {}).get("bundle_id"),
            "symbol": row.get("symbol"),
            "as_of": row.get("decision_time"),
        },
        "evidence_summary": {
            "evidence_ids": (row.get("input_snapshot") or {}).get("evidence_ids", []),
            "factor_input_source_ids": (row.get("input_snapshot") or {}).get(
                "factor_input_source_ids", []),
            "note": "ledger persists evidence ids only",
        },
        "factor_interpretation": {
            "values": None,
            "note": "factor values are not persisted in the ledger; "
                    "explain from the run_result for the full table",
        },
        "probability_interpretation": dict(probability),
        "risk_interpretation": {
            "flags": None,
            "note": "risk detail is not persisted in the ledger",
        },
        "recommendation_interpretation": {
            key: row.get(key) for key in
            ("record_id", "action", "review_status") if key in row
        },
        "registry_identity": {
            "p14f_registry_sha256": (row.get("input_snapshot") or {}).get(
                "p14f_registry_sha256"),
            "p14f_feature_set_id": (row.get("input_snapshot") or {}).get(
                "p14f_feature_set_id"),
        },
    }
    narrative_sections = tuple(payload)
    return _assemble(payload, narrative_sections, row, ledger=ledger,
                     llm=llm, generated_at=generated_at,
                     ledger_context_limit=ledger_context_limit,
                     source="ledger")


def _payload_from_run(run_result: dict,
                      ledger: RecommendationLedger | None) -> tuple[dict, tuple]:
    probability = run_result.get("probability") or {}
    factors = run_result.get("factors") or {}
    risk = run_result.get("risk") or {}
    payload = {
        "run_identity": {
            "run_id": run_result.get("run_id"),
            "result_id": run_result.get("result_id"),
            "bundle_id": run_result.get("bundle_id"),
            "symbol": run_result.get("symbol"),
            "as_of": run_result.get("as_of"),
        },
        "evidence_summary": {
            "evidence_count": len(run_result.get("evidence_ids") or []),
            "counts": run_result.get("counts"),
            "exclusions": run_result.get("exclusions"),
        },
        "factor_interpretation": {
            name: {
                "value": info.get("value"),
                "admissible": info.get("admissible"),
                "observation_count": info.get("observation_count"),
                "method": info.get("method"),
            }
            for name, info in sorted(factors.items())
        },
        "probability_interpretation": dict(probability),
        "risk_interpretation": {
            "flags": list(risk.get("flags") or []),
            "allowed": risk.get("allowed"),
            "max_loss_proxy": risk.get("max_loss_proxy"),
            "realized_drawdown": risk.get("realized_drawdown"),
        },
        "recommendation_interpretation": dict(run_result.get("recommendation") or {}),
        "research_state": {
            "decision_class": (run_result.get("research_state") or {}).get("decision_class"),
            "data_quality": run_result.get("data_quality"),
        },
        "registry_identity": {
            "p14f_feature_set_id": probability.get("feature_set_id"),
        },
    }
    return payload, tuple(payload)


def _assemble(payload: dict, narrative_sections: tuple, source_row: Any, *,
              ledger: RecommendationLedger | None, llm: ExplanationLLM | None,
              generated_at: str | None, ledger_context_limit: int,
              source: str = "run_result") -> dict:
    llm = llm or MockExplanationLLM()
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    run_id = payload["run_identity"].get("run_id")
    if not run_id:
        raise ValueError("run_id missing — explanation reports must reference a real research run")

    # Historical ledger context: READ-ONLY (query + outcome_stats only).
    ledger_context: dict[str, Any] = {"available": ledger is not None}
    if ledger is not None:
        symbol = payload["run_identity"].get("symbol")
        ledger_context["same_symbol_history"] = ledger.query(symbol=symbol)[
            :ledger_context_limit]
        ledger_context["outcome_stats"] = ledger.outcome_stats()
        payload["historical_ledger_context"] = ledger_context
        payload = _sync_ledger_keys(payload, source_row)
        narrative_sections = tuple(payload)

    prompt = build_prompt(payload)
    narrative_raw = llm.generate(prompt)
    allowed = collect_numeric_universe(payload)
    if narrative_numbers_consistent(narrative_raw, allowed):
        narrative_text, narrative_source = narrative_raw, "llm"
    else:
        narrative_text = (
            "LLM narrative rejected: it referenced numbers absent from the "
            "structured source data (fail-closed numeric guard). The "
            "deterministic sections above carry the authoritative figures.")
        narrative_source = "deterministic_fallback"

    sections = {name: payload[name] for name in narrative_sections
                if name in payload}
    sections["uncertainty_limitations"] = _limitations(payload, source)
    sections.setdefault("evidence_summary", payload.get("evidence_summary", {}))

    report = {
        "kind": REPORT_KIND,
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "metadata": {
            "run_id": run_id,
            "llm_model": getattr(llm, "model_name", "unknown"),
            "prompt_version": PROMPT_VERSION,
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "generated_at": generated_at,
            "source": source,
        },
        "run_identity": payload["run_identity"],
        "sections": sections,
        "narrative": {name: {"source": narrative_source, "text": narrative_text}
                      for name in narrative_sections},
        "provenance": _provenance(payload),
        "limitations": sections["uncertainty_limitations"],
    }
    validate_report(report)
    return report


def _sync_ledger_keys(payload: dict, source_row: Any) -> dict:
    """Carry the persisted registry identity into the payload when the
    ledger row provides it (ledger-sourced reports)."""
    row = source_row if isinstance(source_row, dict) else {}
    snapshot = row.get("input_snapshot") or {}
    registry = payload.setdefault("registry_identity", {})
    for key in ("p14f_registry_sha256", "p14f_feature_set_id"):
        if snapshot.get(key):
            registry[key] = snapshot[key]
    return payload


def _limitations(payload: dict, source: str) -> list[str]:
    limitations = [
        "This report is a read-only explanation. It has no decision "
        "authority: the deterministic quant pipeline owns every figure.",
        "The LLM narrative is guarded: every number it references must "
        "exist in the source data, otherwise deterministic prose is used.",
    ]
    probability = payload.get("probability_interpretation") or {}
    if probability.get("probability_status") not in (None, "CALIBRATED"):
        limitations.append(
            f"probability_status={probability.get('probability_status')!r}: "
            "the resolver did not produce a calibrated probability for this run.")
    if source == "ledger":
        limitations.append(
            "Ledger-sourced report: factor/risk tables are not persisted "
            "in the ledger; those sections are intentionally empty.")
    factors = payload.get("factor_interpretation") or {}
    if isinstance(factors, dict):
        missing = [name for name, info in factors.items()
                   if isinstance(info, dict) and info.get("value") is None]
        if missing:
            limitations.append(
                "factor values missing for: " + ", ".join(sorted(missing)))
    return limitations


def _provenance(payload: dict) -> list[dict]:
    """Every numeric leaf in the payload, as (source_field, source_value)."""
    entries: list[dict] = []

    def _walk(node: Any, path: str) -> None:
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            entries.append({"source_field": path, "source_value": node})
        elif isinstance(node, dict):
            for key, value in node.items():
                _walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, (list, tuple)):
            for index, item in enumerate(node):
                _walk(item, f"{path}[{index}]" if path else f"[{index}]")

    _walk(payload, "")
    return entries


def render_report_markdown(report: dict) -> str:
    return render_markdown(report)
