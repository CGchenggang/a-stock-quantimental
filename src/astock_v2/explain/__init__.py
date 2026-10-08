"""Read-only LLM research explanation layer (see research_explainer).

Architecture guarantee (pinned by tests/test_explain_layer.py): this
package imports ONLY the ledger read API and recommendation primitives.
It has no write path into any quant authority and never appends to the
ledger.
"""
from .research_explainer import (
    explain_ledger_record,
    explain_run,
    render_report_markdown,
)

__all__ = ["explain_run", "explain_ledger_record", "render_report_markdown"]
