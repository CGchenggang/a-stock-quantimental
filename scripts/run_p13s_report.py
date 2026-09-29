"""P13-S: research report generation layer over P13-R recommendation packets.

Explanation/reporting layer only: P13-R decides, P13-S explains. Every value
in a report is passed through verbatim from the packet; this module never
re-predicts, re-selects, re-calibrates or modifies any decision field.

Pipeline: packet -> validate_packet() -> build_report() (deterministic
object, report_id = sha256 of the canonical packet) -> render_markdown()
(fixed template; an LLM renderer interface is reserved but CI only uses the
deterministic renderer). Runtime metadata (generation time) is kept out of
the deterministic artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "p13s-report-1"

REQUIRED_FIELDS = (
    "symbol", "decision_time", "policy_id", "calibration_method",
    "raw_probability", "calibrated_probability", "expected_return",
    "risk_score", "cost_scenario", "cost_adjusted_expected_return",
    "market_regime", "selection_reason", "risk_flags", "data_available_time",
)

KNOWN_POLICIES = (
    "hold_all", "threshold_raw_p50", "threshold_platt_p50",
    "threshold_iso_p50", "topk_platt_k3", "percentile_platt_p80",
    "er_platt_0", "er_platt_pos_risk",
)

KNOWN_CALIBRATIONS = ("raw", "platt", "isotonic", "none")

# claim -> (report field, packet field, upstream stage): fixed traceability map
EVIDENCE_MAP = {
    "raw_probability": ("raw_probability", "raw_probability", "p13q_calibration"),
    "calibrated_probability": ("calibrated_probability", "calibrated_probability", "p13q_calibration"),
    "expected_return": ("expected_return", "expected_return", "p13r_expected_return_model"),
    "cost_adjusted_expected_return": ("cost_adjusted_expected_return", "cost_adjusted_expected_return", "p13r_expected_return_model"),
    "risk_score": ("risk_score", "risk_score", "p13r_risk_features"),
    "risk_flags": ("risk_flags", "risk_flags", "p13r_risk_features"),
    "market_regime": ("market_regime", "market_regime", "p13o_regime_labeler"),
    "selection_reason": ("selection_reason", "selection_reason", "p13r_policy_registry"),
    "data_available_time": ("data_available_time", "data_available_time", "p13r_pit_audit"),
}

UNCERTAINTY_VOCABULARY = (
    "missing_data", "stale_data", "low_confidence",
    "contradictory_evidence", "unknown_policy",
)

THRESHOLD = 0.5  # fixed direction boundary used only for the contradiction flag


def _parse_boundary(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def freshness_of(packet: dict) -> str:
    """fresh/stale/missing/unknown on the conservative-cutoff semantics.

    P13-R sets data_available_time = decision_time (the decision boundary is
    the data cutoff), so a present, parseable pair with available <= decision
    is fresh by construction. Nothing finer is claimed.
    """
    available = packet.get("data_available_time")
    decision = packet.get("decision_time")
    if available is None or decision is None:
        return "missing"
    a, d = _parse_boundary(available), _parse_boundary(decision)
    if a is None or d is None:
        return "unknown"
    return "fresh" if a <= d else "stale"


def validate_packet(packet: dict) -> dict:
    """Deterministic validation: missing fields, freshness, uncertainty."""
    missing = [f for f in REQUIRED_FIELDS if packet.get(f) is None]
    freshness = freshness_of(packet)
    uncertainty: list[str] = []
    if missing:
        uncertainty.append("missing_data")
    if freshness == "stale":
        uncertainty.append("stale_data")
    calibration = packet.get("calibration_method")
    if calibration == "none":
        uncertainty.append("low_confidence")
    raw, calibrated = packet.get("raw_probability"), packet.get("calibrated_probability")
    if raw is not None and calibrated is not None:
        raw_up = raw >= THRESHOLD
        cal_up = calibrated >= THRESHOLD
        if raw_up != cal_up:
            uncertainty.append("contradictory_evidence")
    if packet.get("policy_id") not in KNOWN_POLICIES:
        uncertainty.append("unknown_policy")
    return {
        "missing_fields": missing,
        "data_freshness_status": freshness,
        "uncertainty": uncertainty,
        "known_policy": packet.get("policy_id") in KNOWN_POLICIES,
    }


def report_id_for(packet: dict) -> str:
    canonical = json.dumps(packet, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(
        (canonical + SCHEMA_VERSION).encode("utf-8")
    ).hexdigest()[:16]


def build_report(packet: dict) -> dict:
    """Deterministic report object; reads the packet, never writes it.

    Validation flags that need the whole packet (contradiction, policy
    identity) are computed here as well so callers only need this function.
    """
    validation = validate_packet(packet)
    report = {
        "report_id": report_id_for(packet),
        "schema_version": SCHEMA_VERSION,
        "symbol": packet.get("symbol"),
        "decision_time": packet.get("decision_time"),
        "policy_id": packet.get("policy_id"),
        "calibration_method": packet.get("calibration_method"),
        "raw_probability": packet.get("raw_probability"),
        "calibrated_probability": packet.get("calibrated_probability"),
        "expected_return": packet.get("expected_return"),
        "cost_scenario": packet.get("cost_scenario"),
        "cost_adjusted_expected_return": packet.get("cost_adjusted_expected_return"),
        "risk_score": packet.get("risk_score"),
        "risk_flags": list(packet.get("risk_flags") or []),
        "market_regime": packet.get("market_regime"),
        "selection_reason": packet.get("selection_reason"),
        "data_available_time": packet.get("data_available_time"),
        "data_freshness_status": validation["data_freshness_status"],
        "uncertainty": validation["uncertainty"],
        "missing_fields": validation["missing_fields"],
        "known_policy": validation["known_policy"],
        "p13s_validation_flags": list(validation["uncertainty"]),
        "evidence_refs": [
            {
                "claim": claim,
                "report_field": report_field,
                "source_packet_field": packet_field,
                "source_stage": stage,
            }
            for claim, (report_field, packet_field, stage) in EVIDENCE_MAP.items()
        ],
        "research_only": True,
        "artifact_kind": "research_report_not_an_order",
    }
    return report


def render_markdown(report: dict) -> str:
    """Fixed-template renderer; pure function of the report object."""
    def fmt(value, kind="text"):
        if value is None:
            return "MISSING (insufficient_evidence)"
        if kind == "pct":
            return f"{value:.4%}"
        if kind == "num":
            return f"{value:.6f}"
        return str(value)

    lines = [
        "Research Report",
        "===============",
        "",
        f"Report ID: {report['report_id']}",
        f"Schema Version: {report['schema_version']}",
        "",
        "Recommendation Summary",
        "----------------------",
        f"Symbol: {fmt(report['symbol'])}",
        f"Decision Time: {fmt(report['decision_time'])}",
        f"Policy: {fmt(report['policy_id'])}",
        "",
        "Probability / Calibration",
        "-------------------------",
        f"Raw Probability: {fmt(report['raw_probability'], 'pct')}",
        f"Calibrated Probability: {fmt(report['calibrated_probability'], 'pct')}",
        f"Calibration Method: {fmt(report['calibration_method'])}",
        "",
        "Expected Return",
        "---------------",
        f"Expected Return: {fmt(report['expected_return'], 'pct')}",
        f"Cost-adjusted Expected Return: {fmt(report['cost_adjusted_expected_return'], 'pct')}",
        f"Cost Scenario: {fmt(report.get('cost_scenario'))}",
        "",
        "Risk",
        "----",
        f"Risk Score: {fmt(report['risk_score'], 'num')}",
        f"Risk Flags: {', '.join(report['risk_flags']) if report['risk_flags'] else '(none recorded by P13-R)'}",
        "",
        "Market Regime",
        "-------------",
        f"Market Regime: {fmt(report['market_regime'])}",
        "",
        "Selection Reason",
        "----------------",
        f"Selection Reason: {fmt(report['selection_reason'])}",
        "",
        "Data Freshness",
        "--------------",
        f"Decision Time: {fmt(report['decision_time'])}",
        f"Data Available Time: {fmt(report['data_available_time'])}",
        f"Freshness Status: {fmt(report['data_freshness_status'])}",
        "",
        "Uncertainty",
        "-----------",
    ]
    if report["uncertainty"]:
        lines += [f"- {flag}" for flag in report["uncertainty"]]
        if "contradictory_evidence" in report["uncertainty"]:
            lines.append(
                "  note: raw and calibrated probabilities fall on opposite sides "
                "of 0.50; no resolution is applied by P13-S"
            )
        if "unknown_policy" in report["uncertainty"]:
            lines.append(
                "  note: policy is not in the P13-R registry; no confident "
                "recommendation conclusion is drawn"
            )
    else:
        lines.append("(none flagged)")
    lines += [
        "",
        "Evidence",
        "--------",
    ]
    lines += [
        f"- {ref['claim']}: report field '{ref['report_field']}' <- packet field "
        f"'{ref['source_packet_field']}' <- {ref['source_stage']}"
        for ref in report["evidence_refs"]
    ]
    lines += [
        "",
        "Research Status",
        "---------------",
        "research_only = true",
        "This artifact documents a research decision layer for human review; "
        "it is not an order and not an execution instruction.",
        "",
    ]
    return "\n".join(lines)


class LLMRenderer:
    """Reserved interface for a future offline LLM renderer.

    Contract: receives the immutable report object, returns text that only
    reorganizes/explains existing fields. CI never instantiates this; the
    deterministic renderer is the reference implementation.
    """

    def render(self, report: dict) -> str:  # pragma: no cover - interface stub
        raise NotImplementedError(
            "LLM renderer is intentionally not implemented; use render_markdown"
        )


RENDERERS = {"deterministic": render_markdown, "llm": LLMRenderer}


def process_packets(packets: list[dict], out_dir: Path) -> dict:
    reports = [build_report(p) for p in packets]
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    structured = out_dir / "research_reports.json"
    structured.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "reports": reports},
                   sort_keys=True, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    written.append(structured)
    rendered_dir = out_dir / "reports_md"
    rendered_dir.mkdir(exist_ok=True)
    for report in reports:
        path = rendered_dir / f"{report['report_id']}.md"
        path.write_text(
            render_markdown(report), encoding="utf-8", newline="\n"
        )
        written.append(path)
    summary = {
        "packets_in": len(packets),
        "reports_out": len(reports),
        "uncertainty_counts": {
            flag: sum(1 for r in reports if flag in r["uncertainty"])
            for flag in UNCERTAINTY_VOCABULARY
        },
    }
    return {"reports": reports, "summary": summary, "files": written}


def _input_hashes(paths: list[Path]) -> dict:
    out = {}
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            out[path.name] = {"sha256": hashlib.sha256(data).hexdigest(),
                              "size": len(data)}
    return out


def write_manifest(out_dir: Path, input_paths: list[Path],
                   output_paths: list[Path]) -> dict:
    outputs = {}
    for path in sorted(set(output_paths)):
        if path.is_file():
            rel = str(path.relative_to(out_dir)).replace("\\", "/")
            data = path.read_bytes()
            outputs[rel] = {"sha256": hashlib.sha256(data).hexdigest(),
                            "size": len(data)}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "inputs": _input_hashes(input_paths),
        "configuration": {
            "renderer": "deterministic",
            "threshold_for_contradiction": THRESHOLD,
            "known_policies": list(KNOWN_POLICIES),
            "known_calibrations": list(KNOWN_CALIBRATIONS),
            "freshness_rule": "data_available_time <= decision_time -> fresh",
        },
        "outputs": outputs,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8"
    )
    return manifest


TASKS = ("reports", "golden", "manifest", "all")


def _golden_packets() -> dict[str, dict]:
    base = {
        "symbol": "000001",
        "decision_time": "2025-03-18T16:00:00+08:00",
        "policy_id": "threshold_platt_p50",
        "calibration_method": "platt",
        "raw_probability": 0.7397,
        "calibrated_probability": 0.5128,
        "expected_return": 0.0008,
        "risk_score": 0.0086,
        "cost_scenario": "low",
        "cost_adjusted_expected_return": -0.0002,
        "market_regime": "BULL",
        "selection_reason": "platt_probability_ge_0.50",
        "risk_flags": [],
        "data_available_time": "2025-03-18T16:00:00+08:00",
    }
    def variant(name, **overrides):
        packet = dict(base)
        packet.update(overrides)
        return name, packet
    return dict([
        variant("normal"),
        variant("missing_data", risk_score=None, market_regime=None),
        variant("stale_data",
                data_available_time="2025-03-20T16:00:00+08:00"),
        variant("low_confidence",
                policy_id="threshold_raw_p50", calibration_method="none",
                raw_probability=0.52, calibrated_probability=0.52,
                selection_reason="raw_probability_ge_0.50"),
        variant("contradictory_evidence", calibrated_probability=0.42),
        variant("unknown_policy", policy_id="mystery_policy_v9"),
        variant("risk_flags_present", risk_flags=["P13R_HIGH_TURNOVER"]),
        variant("calibration_raw", policy_id="threshold_raw_p50",
                calibration_method="raw", calibrated_probability=0.7397,
                selection_reason="raw_probability_ge_0.50"),
        variant("calibration_none", policy_id="threshold_raw_p50",
                calibration_method="none", calibrated_probability=0.7397,
                selection_reason="raw_probability_ge_0.50"),
        variant("calibration_isotonic", policy_id="threshold_iso_p50",
                calibration_method="isotonic", calibrated_probability=0.7397,
                selection_reason="isotonic_probability_ge_0.50"),
    ])


def run_golden(out_dir: Path) -> dict:
    golden_dir = out_dir / "golden_reports"
    golden_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, packet in _golden_packets().items():
        report = build_report(packet)
        entry = {
            "packet": packet,
            "report": report,
            "rendered": render_markdown(report),
        }
        path = golden_dir / f"{name}.json"
        path.write_text(
            json.dumps(entry, sort_keys=True, indent=1, ensure_ascii=False),
            encoding="utf-8",
        )
        written[name] = path
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", required=True,
                        help="P13-R recommendation_audit.json")
    parser.add_argument("--policy", default="all",
                        help="policy id or 'all'")
    parser.add_argument("--out-dir", default="data/industry/p13s")
    parser.add_argument("--max-reports", type=int, default=50,
                        help="per-policy packet cap for the artifact run")
    parser.add_argument("task", choices=TASKS)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    output_paths: list[Path] = []
    if args.task in ("reports", "all"):
        with open(args.packets, encoding="utf-8") as f:
            audit = json.load(f)
        all_packets = audit["packets"]
        policy_ids = list(all_packets) if args.policy == "all" else [args.policy]
        packets: list[dict] = []
        for pid in policy_ids:
            packets.extend(all_packets[pid][: args.max_reports])
        output_paths.extend(process_packets(packets, out_dir)["files"])
    if args.task in ("golden", "all"):
        output_paths.extend(run_golden(out_dir).values())
    if args.task in ("manifest", "all"):
        input_paths = [Path(args.packets), Path("docs/P13R_PIT_AUDIT.md")]
        write_manifest(out_dir, input_paths, output_paths)
        print(f"manifest_written={out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
