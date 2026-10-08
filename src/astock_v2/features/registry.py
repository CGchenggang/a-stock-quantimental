"""P14-F Research-Only Feature Registry.

Public API:

- :func:`load_registry` — load and integrity-check the committed registry.
- :func:`registry_sha256` — canonical-bytes digest of the registry.
- :func:`resolve_membership` — resolve the frozen MODEL_APPLICATION
  membership against the registry (ordered per the membership authority).
- :func:`feature_set_id` — P14F2-006 derivation (ordered list -> SHA-256).
- :func:`verify_against_frozen` — P14F2-019 closure: derived id == frozen.

Fail-closed: any integrity / binding mismatch raises; the registry is
read-only (no mutation API).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from ..model.forward_model import (
    FROZEN_FEATURE_NAMES,
    FROZEN_FEATURE_SET_ID,
    canonical_json,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = _REPO_ROOT / "docs" / "contracts" / "p14f" / "FEATURE_REGISTRY.json"
EVIDENCE_PATH = _REPO_ROOT / "docs" / "artifacts" / "P14-F-REGISTRY-EVIDENCE.md"


class RegistryIntegrityError(ValueError):
    """Registry bytes / hash mismatch against the committed evidence record."""


class MemberUnresolvedError(KeyError):
    """A frozen-membership name has no current definition in the registry."""


class FeatureSetBindingError(ValueError):
    """Derived feature_set_id does not match the frozen MODEL_APPLICATION
    binding (P14F2-019 closure failure)."""


# ----------------------------------------------------------------- bytes

def _registry_bytes() -> bytes:
    """Read the committed registry bytes exactly as stored on disk."""
    try:
        return REGISTRY_PATH.read_bytes()
    except FileNotFoundError as exc:
        raise RegistryIntegrityError(
            f"registry file missing: {REGISTRY_PATH}") from exc


def _evidence_sha256() -> str:
    """Parse the registry_sha256 out of the committed evidence record
    (machine-readable fenced json block)."""
    try:
        text = EVIDENCE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RegistryIntegrityError(
            f"evidence record missing: {EVIDENCE_PATH}") from exc
    # Match the fenced json block carrying registry_sha256.
    block_match = re.search(
        r"```json\s*(\{[^`]*?\"registry_sha256\"[^`]*?\})\s*```",
        text, re.DOTALL)
    if not block_match:
        raise RegistryIntegrityError(
            "evidence record does not carry a machine-parseable registry "
            "block")
    try:
        block = json.loads(block_match.group(1))
    except json.JSONDecodeError as exc:
        raise RegistryIntegrityError(
            f"evidence block not valid JSON: {exc}") from exc
    sha = block.get("registry_sha256")
    if not isinstance(sha, str) or len(sha) != 64:
        raise RegistryIntegrityError(
            "evidence block missing/invalid registry_sha256")
    return sha


# ----------------------------------------------------------- public API

def registry_sha256() -> str:
    """Canonical-bytes SHA-256 of the committed registry."""
    return hashlib.sha256(_registry_bytes()).hexdigest()


def load_registry() -> dict:
    """Load the registry JSON, verify canonical round-trip, and verify
    the bytes digest against the committed evidence record.

    FAIL CLOSED on: missing file, non-canonical bytes, digest mismatch,
    or schema violation.
    """
    data = _registry_bytes()
    # Canonical-bytes round-trip: re-serialize parsed JSON with the
    # P13O-F-016c recipe and compare byte-for-byte.
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryIntegrityError(f"registry not valid UTF-8 JSON: {exc}") from exc
    re_encoded = canonical_json(parsed).encode("utf-8")
    if re_encoded != data:
        raise RegistryIntegrityError(
            "registry bytes are not in canonical form (P13O-F-016c)")
    # Schema: top-level {definitions, registry_version} with every entry
    # carrying the 9 fields per contract P14F2-002.
    if not isinstance(parsed, dict):
        raise RegistryIntegrityError("registry top-level is not an object")
    if set(parsed.keys()) != {"definitions", "registry_version"}:
        raise RegistryIntegrityError(
            f"registry top-level keys unexpected: {sorted(parsed)}")
    if not isinstance(parsed["registry_version"], int):
        raise RegistryIntegrityError("registry_version is not an int")
    definitions = parsed["definitions"]
    if not isinstance(definitions, dict) or not definitions:
        raise RegistryIntegrityError("definitions is empty or not an object")
    required = {"name", "definition_version", "computation_identity",
                "source_lineage", "semantics", "pit_authority",
                "implementation_identity", "ordering_hint"}
    ci_required = {"source_file", "entry_symbol", "parameters"}
    for name, entry in definitions.items():
        if not isinstance(entry, dict):
            raise RegistryIntegrityError(f"definition {name!r} not an object")
        missing = required - set(entry.keys())
        if missing:
            raise RegistryIntegrityError(
                f"definition {name!r} missing fields: {sorted(missing)}")
        if entry["name"] != name:
            raise RegistryIntegrityError(
                f"definition name mismatch: key={name!r} entry.name={entry['name']!r}")
        ci = entry["computation_identity"]
        if not isinstance(ci, dict) or not ci_required.issubset(ci.keys()):
            raise RegistryIntegrityError(
                f"definition {name!r} computation_identity invalid")
        if not isinstance(entry["source_lineage"], list) or \
                not all(isinstance(s, str) for s in entry["source_lineage"]):
            raise RegistryIntegrityError(
                f"definition {name!r} source_lineage not a list of strings")
        if entry["pit_authority"] != (
                "P14-D (available_time <= as_of) via local_pipeline "
                "decision-time visibility"):
            raise RegistryIntegrityError(
                f"definition {name!r} pit_authority string deviates")
    # Integrity: bytes digest == committed evidence digest.
    actual = hashlib.sha256(data).hexdigest()
    expected = _evidence_sha256()
    if actual != expected:
        raise RegistryIntegrityError(
            f"registry sha256 mismatch: actual={actual} expected={expected}")
    return parsed


def resolve_membership(registry: dict,
                       membership: Iterable[str] = FROZEN_FEATURE_NAMES
                       ) -> list[tuple[str, str]]:
    """Resolve the (ordered) membership against the registry's current
    definitions. Returns ``[(name, definition_version), ...]`` in the
    MEMBERSHIP order (never the registry's storage / ordering_hint).

    Raises :class:`MemberUnresolvedError` on any name absent from the
    registry's current definitions.
    """
    definitions = registry["definitions"]
    resolved: list[tuple[str, str]] = []
    for name in membership:
        entry = definitions.get(name)
        if entry is None:
            raise MemberUnresolvedError(
                f"frozen membership name {name!r} has no current registry "
                f"definition")
        resolved.append((name, entry["definition_version"]))
    return resolved


def feature_set_id(registry: dict,
                   membership: Iterable[str] = FROZEN_FEATURE_NAMES) -> str:
    """P14F2-006 derivation: ``'fs-' + SHA256(canonical_json(resolved))``
    where ``resolved`` is the frozen-membership-ordered list of
    ``[name, definition_version]`` pairs."""
    resolved = resolve_membership(registry, membership)
    payload = canonical_json(resolved).encode("utf-8")
    return "fs-" + hashlib.sha256(payload).hexdigest()


def verify_against_frozen(registry: dict | None = None) -> None:
    """P14F2-019 closure: the derived ``feature_set_id`` MUST equal
    ``FROZEN_FEATURE_SET_ID``. FAIL CLOSED on mismatch (raises)."""
    if registry is None:
        registry = load_registry()
    derived = feature_set_id(registry)
    if derived != FROZEN_FEATURE_SET_ID:
        raise FeatureSetBindingError(
            f"derived feature_set_id {derived} does not match the frozen "
            f"MODEL_APPLICATION binding {FROZEN_FEATURE_SET_ID}")
