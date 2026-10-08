"""CLI entry: python -m astock_v2.explain --run-id <id> --ledger <path>

Read-only. Loads the persisted ledger row for a historical run and emits
the explanation report as markdown (and optionally JSON). No quant layer
is imported beyond the ledger read API; no ledger write is possible.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..ledger import RecommendationLedger
from .llm_adapter import MockExplanationLLM, create_adapter
from .research_explainer import explain_ledger_record, render_report_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m astock_v2.explain",
        description="Generate a read-only explanation report for a "
                    "historical research run (ledger-sourced).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", help="run_id of a persisted ledger row")
    group.add_argument("--record-id", help="record_id of a persisted ledger row")
    parser.add_argument("--ledger", default="workspace/recommendations.jsonl",
                        help="path to the recommendation ledger JSONL")
    parser.add_argument("--llm", default="mock",
                        help="explanation adapter (mock ships in CI; real "
                             "providers are runtime-optional)")
    parser.add_argument("--out", default=None,
                        help="optional markdown output path (default: stdout)")
    parser.add_argument("--json-out", default=None,
                        help="optional JSON output path")
    args = parser.parse_args(argv)

    llm = create_adapter(args.llm) if args.llm != "mock" else MockExplanationLLM()
    ledger = RecommendationLedger(args.ledger)
    report = explain_ledger_record(
        ledger=ledger, run_id=args.run_id, record_id=args.record_id, llm=llm)
    markdown = render_report_markdown(report)
    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown + "\n")
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, sort_keys=True, indent=1, ensure_ascii=False,
                       default=str),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
