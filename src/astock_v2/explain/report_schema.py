"""P14-F-era report schema for the read-only LLM explanation layer.

The explanation layer is READ-ONLY by construction: it consumes already
computed research results (run_result dicts) and ledger read views, and
emits a structured report. It defines NO quant semantics of its own —
every number in a report must come from the structured input payload
(see ``numeric_universe`` / ``narrative_numbers_allowed``).
"""
from __future__ import annotations

import json
import re
from typing import Any

REPORT_SCHEMA_VERSION = "1"
REPORT_KIND = "research_explanation_report"

REQUIRED_METADATA = ("run_id", "llm_model", "prompt_version",
                     "report_schema_version", "generated_at", "source")

REQUIRED_SECTIONS = (
    "evidence_summary",
    "factor_interpretation",
    "probability_interpretation",
    "risk_interpretation",
    "recommendation_interpretation",
    "historical_ledger_context",
    "uncertainty_limitations",
)

_NUMERIC_TOKEN = re.compile(r"-?\d+(?:\.\d+)?")


def collect_numeric_universe(payload: Any) -> set[str]:
    """Every number/format that LLM narrative may legitimately reference:
    all ints/floats in the structured payload (plus common str(round(x, k))
    renderings) and every numeric-looking substring of payload strings
    (dates, ids, thresholds). String containment is the fallback so that
    identifiers such as run ids never fail the check."""
    allowed: set[str] = set()

    def _add_number(value: float) -> None:
        allowed.add(repr(value))
        allowed.add(str(value))
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            allowed.add(str(int(value)))
        for digits in (2, 4, 6):
            allowed.add(f"{value:.{digits}f}")
            allowed.add(f"{value:.{digits}e}")

    def _walk(node: Any) -> None:
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            _add_number(float(node))
        elif isinstance(node, str):
            allowed.update(_NUMERIC_TOKEN.findall(node))
            allowed.add(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                allowed.add(str(key))
                _walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    _walk(payload)
    return allowed


def narrative_numbers_consistent(narrative: str, allowed: set[str]) -> bool:
    """True when every numeric token in the LLM narrative exists in the
    source numeric universe. One fabricated number fails the whole
    narrative (fail-closed → deterministic fallback prose)."""
    for token in _NUMERIC_TOKEN.findall(narrative or ""):
        if token not in allowed:
            return False
    return True


def validate_report(report: dict) -> None:
    """Structural validation. Raises ValueError on any missing element —
    the report is only valid when every required section is present and
    the metadata is complete."""
    if report.get("kind") != REPORT_KIND:
        raise ValueError(f"report kind must be {REPORT_KIND!r}")
    if report.get("report_schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError("report_schema_version mismatch")
    metadata = report.get("metadata") or {}
    for key in REQUIRED_METADATA:
        if not metadata.get(key):
            raise ValueError(f"report metadata missing: {key}")
    sections = report.get("sections") or {}
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            raise ValueError(f"report section missing: {name}")
    if not isinstance(report.get("provenance"), list):
        raise ValueError("report provenance must be a list")
    if not report.get("run_id"):
        raise ValueError("report run_id missing — reports must reference a real research run")


def render_markdown(report: dict) -> str:
    """Deterministic markdown rendering of a validated report."""
    lines = ["# Research Explanation Report", ""]
    metadata = report["metadata"]
    lines.append(f"- report_schema_version: {metadata['report_schema_version']}")
    lines.append(f"- generated_at: {metadata['generated_at']}")
    lines.append(f"- llm_model: {metadata['llm_model']}")
    lines.append(f"- prompt_version: {metadata['prompt_version']}")
    lines.append(f"- run_id: {metadata['run_id']}")
    lines.append("")
    identity = report.get("run_identity") or {}
    lines.append("## Run identity")
    for key in ("run_id", "result_id", "bundle_id", "symbol", "as_of"):
        lines.append(f"- {key}: {identity.get(key)}")
    lines.append("")
    for name in REQUIRED_SECTIONS:
        section = report["sections"][name]
        lines.append(f"## {name}")
        lines.append("```json")
        lines.append(json.dumps(section, sort_keys=True, indent=1,
                                ensure_ascii=False, default=str))
        lines.append("```")
        narrative = (report.get("narrative") or {}).get(name)
        if narrative:
            lines.append("")
            lines.append(f"({narrative['source']}) {narrative['text']}")
        lines.append("")
    lines.append("## Provenance references")
    for entry in report.get("provenance", []):
        lines.append(f"- `{entry['source_field']}` = {entry['source_value']!r}")
    lines.append("")
    return "\n".join(lines)
