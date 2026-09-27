"""Read legacy V1 cache envelopes without losing their persisted timestamp."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def legacy_cache_path(cache_dir: str | Path, key: str) -> Path:
    safe = str(key).replace("/", "_").replace("\\", "_").replace(":", "_")
    return Path(cache_dir) / f"{safe}.json"


def read_legacy_cache(
    cache_dir: str | Path,
    key: str,
    *,
    now: float | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any] | None:
    """Return cached data plus its persisted timestamp."""
    path = legacy_cache_path(cache_dir, key)
    if not path.exists():
        return None
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        ts = float(envelope["ts"])
        data = envelope["data"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    age = max(0.0, (float(now) if now is not None else time.time()) - ts)
    if ttl_seconds is not None and age > ttl_seconds:
        return None

    return {
        "data": data,
        "saved_at_unix": ts,
        "age_seconds": age,
        "cache_key": key,
        "path": str(path),
    }
