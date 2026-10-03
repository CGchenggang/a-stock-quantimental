"""P14-E: EvidenceStore — durable append-only JSONL persistence.

Implements the accepted P14-E-004 Production Contract §10 and P14-E-005
Implementation Contract P14E-I-019 (persistence semantics):

- append-only: never modifies existing lines
- idempotent:  same bundle_id → rejected (returns False)
- reload:      recomputes bundle_id AND resolves every Evidence's
               (ingestion_id, raw_payload_hash) against the P14-B
               RawStore authority
- atomic:      single-line writes (newline-terminated)
"""
from __future__ import annotations

import json
from pathlib import Path

from .evidence import (
    TRACE_RAW_CORRUPTED,
    ReverseTraceError,
    _sha,
    canonical_json,
    reverse_trace_resolve,
)


class EvidenceStore:
    """Durable evidence bundle store."""

    def __init__(self, path: Path, raw_store_path: Path | None = None):
        self.path = Path(path)
        self._raw_store_path = raw_store_path

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

    def reload(self) -> list[dict]:
        """Load all bundles and verify integrity + authority."""
        out = []
        if not self.path.exists():
            return out
        raw_rows = None
        if self._raw_store_path and self._raw_store_path.exists():
            raw_rows = [json.loads(l) for l in
                        self._raw_store_path.read_text(encoding="utf-8").splitlines()
                        if l.strip()]
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
            if raw_rows is not None:
                for ev in bundle["evidence"]:
                    try:
                        reverse_trace_resolve(ev, raw_rows)
                    except ReverseTraceError:
                        raise ReverseTraceError(
                            TRACE_RAW_CORRUPTED,
                            f"reload authority failure for "
                            f"evidence {ev.get('evidence_id', '?')}")
            bundle["bundle_id"] = stored_id
            out.append(bundle)
        return out
