from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from ..types import DataPoint

class PITStore:
    """Append-only Point-in-Time store with strict availability filtering."""

    def __init__(self, path: str | Path = "data/pit/events.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, dp: DataPoint) -> None:
        available = datetime.fromisoformat(dp.available_time)
        event = datetime.fromisoformat(dp.event_time)
        if available < event:
            raise ValueError("available_time cannot precede event_time")
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(dp), ensure_ascii=False) + "\n")

    def available_before(self, decision_time: str, symbol: str | None = None) -> list[dict]:
        decision = datetime.fromisoformat(decision_time)
        if not self.path.exists():
            return []
        rows=[]
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            row=json.loads(line)
            if datetime.fromisoformat(row["available_time"]) <= decision and (symbol is None or row["symbol"] == symbol):
                rows.append(row)
        return rows
