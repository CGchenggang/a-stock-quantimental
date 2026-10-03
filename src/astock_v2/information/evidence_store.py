"""P14-E: EvidenceStore — durable append-only JSONL persistence.

Implements the accepted P14-E-004 Production Contract §10 and P14-E-005
Implementation Contract P14E-I-019 (persistence semantics):

- append-only: never modifies existing lines
- idempotent:  same bundle_id → rejected (returns False)
- reload:      recomputes bundle_id AND resolves every Evidence's
               (ingestion_id, raw_payload_hash) against the P14-B
               RawStore authority — MANDATORY. The authority store path
               is a required constructor argument; a reload without a
               resolvable P14-B authority fails fast. Bundle-hash
               integrity alone never re-authorizes evidence.
- atomic:      single-line writes (newline-terminated)

Authority failures preserve the FOUR-CLASS taxonomy: a missing
authoritative row raises REVERSE_TRACE_NOT_FOUND, an unreadable raw row
raises RAW_RECORD_CORRUPTED — reload never re-labels them.
"""
from __future__ import annotations

import json
from pathlib import Path

from .evidence import (
    TRACE_NOT_FOUND,
    TRACE_RAW_CORRUPTED,
    ReverseTraceError,
    _sha,
    canonical_json,
    reverse_trace_resolve,
)


class EvidenceStore:
    """Durable evidence bundle store with mandatory P14-B authority."""

    def __init__(self, path: Path, raw_store_path: Path):
        self.path = Path(path)
        self._raw_store_path = Path(raw_store_path)

    def append(self, bundle: dict) -> bool:
        """Append one bundle; returns True if written, False if duplicate."""
        bid = bundle["bundle_id"]
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip() and json.loads(line)["bundle_id"] == bid:
                    return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(canonical_json(bundle) + "\n")
        return True

    def _load_raw_rows(self) -> list[dict]:
        """Load the P14-B raw authority rows; missing/unreadable authority
        is a reload failure, never a silent skip."""
        if not self._raw_store_path.exists():
            raise ReverseTraceError(
                TRACE_NOT_FOUND,
                f"reload authority failure: P14-B raw authority store "
                f"missing at {self._raw_store_path}")
        rows = []
        for line in self._raw_store_path.read_text(
                encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ReverseTraceError(
                    TRACE_RAW_CORRUPTED,
                    f"P14-B raw authority row unreadable: {exc}") from None
        return rows

    def reload(self) -> list[dict]:
        """Load all bundles and verify integrity + P14-B authority."""
        out = []
        if not self.path.exists():
            return out
        raw_rows = self._load_raw_rows()
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            bundle = json.loads(line)
            stored_id = bundle.pop("bundle_id")
            recomputed = _sha(canonical_json(bundle))
            if recomputed != stored_id:
                raise ReverseTraceError(
                    TRACE_RAW_CORRUPTED,
                    f"reload integrity failure: bundle_id mismatch "
                    f"(stored={stored_id}, recomputed={recomputed})")
            for ev in bundle["evidence"]:
                try:
                    reverse_trace_resolve(ev, raw_rows)
                except ReverseTraceError as exc:
                    raise ReverseTraceError(
                        exc.cls,
                        f"reload authority failure for evidence "
                        f"{ev.get('evidence_id', '?')}: {exc}") from None
            bundle["bundle_id"] = stored_id
            out.append(bundle)
        return out
