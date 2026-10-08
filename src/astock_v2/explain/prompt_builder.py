"""Prompt assembly for the read-only explanation layer.

PROMPT_VERSION pins the prompt contract: the LLM receives the structured
SOURCE DATA block (authoritative numbers) plus interpretation rules, and
returns prose ONLY. The prompt explicitly forbids inventing numbers —
and the numeric-consistency guard in research_explainer enforces it
regardless of whether the model obeys.
"""
from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "explain-v1"

_INSTRUCTIONS = """You are a READ-ONLY research explanation assistant.

TASK: explain, compare and attribute the research run described in the
SOURCE DATA block below. You may summarize, interpret and contextualize.

HARD RULES:
1. Every number you write MUST come from the SOURCE DATA block. Do not
   compute, convert, round into new figures, or invent any number.
2. Do not make trading recommendations. The decision authority is the
   deterministic quant pipeline, not you.
3. If something is not in the source data, say it is not available.

OUTPUT: one or two short paragraphs of plain prose.
"""


def build_prompt(payload: dict[str, Any]) -> str:
    """Assemble the explanation prompt from the structured payload.

    The payload is the single source of truth for every number the LLM
    may reference; the same payload feeds the numeric-consistency guard.
    """
    source = json.dumps(payload, sort_keys=True, indent=1,
                        ensure_ascii=False, default=str)
    return f"{_INSTRUCTIONS}\nSOURCE DATA (authoritative numbers):\n{source}\n"
