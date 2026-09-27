"""Atomic local storage for reproducible historical research data.

The store is intentionally dependency-light and uses JSON Lines.  Raw provider
snapshots and normalized HistoricalRecord rows are kept separately so a clean
dataset can be rebuilt without another network request.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

from .catalog import DataLayer, HistoricalRecord


def _parse_aware(value: str) -> datetime:
    if not value:
        raise ValueError("timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an explicit timezone")
    return parsed


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"not JSON serializable: {type(value)!r}")


class LocalHistoricalStore:
    """Store raw snapshots and PIT-auditable normalized records locally."""

    def __init__(self, root: str | Path = "data") -> None:
        self.root = Path(root)

    def raw_path(self, dataset: str, snapshot_id: str) -> Path:
        return self.root / "raw" / dataset / f"{snapshot_id}.json"

    def record_path(self, dataset: str, symbol: str) -> Path:
        safe = symbol.replace("/", "_").replace("\\", "_")
        return self.root / "clean" / dataset / f"{safe}.jsonl"

    def write_raw_snapshot(self, dataset: str, snapshot_id: str, payload: object) -> tuple[Path, str]:
        path = self.raw_path(dataset, snapshot_id)
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default, indent=2)
        self._atomic_text(path, content + "\n")
        return path, hashlib.sha256(content.encode("utf-8")).hexdigest()

    def append_records(self, dataset: str, records: Iterable[HistoricalRecord]) -> int:
        rows = list(records)
        if not rows:
            return 0
        for record in rows:
            self._validate_record(record)

        by_symbol: dict[str, list[HistoricalRecord]] = {}
        for record in rows:
            by_symbol.setdefault(record.symbol, []).append(record)

        written = 0
        for symbol, incoming in by_symbol.items():
            path = self.record_path(dataset, symbol)
            existing: dict[tuple[str, int], HistoricalRecord] = {}
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    raw = json.loads(line)
                    record = HistoricalRecord(
                        symbol=raw["symbol"],
                        event_time=raw["event_time"],
                        available_time=raw.get("available_time"),
                        source=raw["source"],
                        source_type=raw["source_type"],
                        value=raw["value"],
                        layer=DataLayer(raw.get("layer", "clean")),
                        asset_scope=raw.get("asset_scope", "cn_stock"),
                        revision=int(raw.get("revision", 0)),
                        raw_ref=raw.get("raw_ref"),
                        quality=raw.get("quality", "UNKNOWN"),
                    )
                    existing[(record.event_time, record.revision)] = record
            for record in incoming:
                existing[(record.event_time, record.revision)] = record
            ordered = sorted(existing.values(), key=lambda x: (x.event_time, x.revision))
            payload = "".join(json.dumps(asdict(r), ensure_ascii=False, default=_json_default, sort_keys=True) + "\n" for r in ordered)
            self._atomic_text(path, payload)
            written += len(incoming)
        return written

    def read_records(self, dataset: str, symbol: str) -> tuple[HistoricalRecord, ...]:
        path = self.record_path(dataset, symbol)
        if not path.exists():
            return ()
        result = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            result.append(HistoricalRecord(
                symbol=raw["symbol"],
                event_time=raw["event_time"],
                available_time=raw.get("available_time"),
                source=raw["source"],
                source_type=raw["source_type"],
                value=raw["value"],
                layer=DataLayer(raw.get("layer", "clean")),
                asset_scope=raw.get("asset_scope", "cn_stock"),
                revision=int(raw.get("revision", 0)),
                raw_ref=raw.get("raw_ref"),
                quality=raw.get("quality", "UNKNOWN"),
            ))
        return tuple(result)

    @staticmethod
    def _validate_record(record: HistoricalRecord) -> None:
        _parse_aware(record.event_time)
        if not record.available_time:
            raise ValueError("local historical records require explicit available_time")
        _parse_aware(record.available_time)
        if _parse_aware(record.available_time) < _parse_aware(record.event_time):
            raise ValueError("available_time cannot precede event_time")

    @staticmethod
    def _atomic_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
