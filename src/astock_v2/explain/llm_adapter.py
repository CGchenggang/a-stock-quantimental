"""LLM adapter boundary for the read-only explanation layer.

The adapter is the ONLY place that knows an LLM exists. It turns a fully
assembled prompt into free text — nothing more. It can never touch the
quant layer, the ledger write path, or any authority: it has no such
parameters and no such imports.

CI uses :class:`MockExplanationLLM` (deterministic, no network). Real
providers are runtime-optional via :func:`create_adapter` and raise
unless their extra dependency AND credentials are present; no API key is
ever read from the repository.
"""
from __future__ import annotations

from typing import Any, Protocol

MOCK_MODEL_NAME = "mock-explainer-v1"


class ExplanationLLM(Protocol):
    """Anything with a ``model_name`` and a ``generate(prompt) -> str``."""

    model_name: str

    def generate(self, prompt: str) -> str: ...


class MockExplanationLLM:
    """Deterministic CI adapter.

    ``behavior="faithful"`` composes the narrative strictly from the
    numbers contained in the prompt's SOURCE DATA block (so it always
    passes the numeric-consistency guard). ``behavior="fabricating"``
    injects a number that does not exist in the source — used by tests
    to prove the guard rejects fabricated figures and falls back to the
    deterministic narrative."""

    def __init__(self, behavior: str = "faithful",
                 response_override: str | None = None) -> None:
        if behavior not in {"faithful", "fabricating"}:
            raise ValueError("behavior must be 'faithful' or 'fabricating'")
        self.behavior = behavior
        self.response_override = response_override
        self.model_name = MOCK_MODEL_NAME

    def generate(self, prompt: str) -> str:
        if self.response_override is not None:
            return self.response_override
        if self.behavior == "fabricating":
            return ("Interpretation: the fabricated probability 0.123456 "
                    "suggests a fabricated edge of 12.3456 percent.")
        numbers = sorted(set(_numbers_in(prompt)))
        listed = ", ".join(numbers[:8]) if numbers else "no source numbers"
        return (f"Interpretation based strictly on the source data "
                f"({listed}). The packet is internally consistent and the "
                f"figures above fully determine the explanation.")


def _numbers_in(text: str) -> list[str]:
    import re
    source_marker = "SOURCE DATA"
    block = text.split(source_marker, 1)[-1]
    return re.findall(r"-?\d+(?:\.\d+)?", block)


def create_adapter(name: str = "mock", **kwargs: Any) -> ExplanationLLM:
    """Runtime-optional adapter factory. Only 'mock' is available in CI;
    real providers must be installed AND credentialed by the caller at
    runtime. This repository ships no provider integration and no keys."""
    if name == "mock":
        return MockExplanationLLM(**kwargs)
    raise ValueError(
        f"unknown explanation adapter {name!r}; real providers are "
        "runtime-optional and are not shipped with the repository")
