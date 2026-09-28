"""Append-only recommendation ledger with immutable event history."""
from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _record_to_dict(record):
    if hasattr(record, "as_dict"):
        return record.as_dict()
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"unsupported ledger record: {type(record)!r}")


class RecommendationLedger:
    def __init__(self, path="workspace/recommendations.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, payload):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def append(self, record, feature_version="unknown", *, input_snapshot=None):
        row = _record_to_dict(record)
        event = {
            "type": "recommendation",
            **row,
            "feature_version": feature_version,
            "input_snapshot": input_snapshot,
            "outcomes": {},
        }
        self._append(event)
        return event

    def append_review(self, review):
        row = {"record_id": review.record_id, "review_time": review.review_time, "realized_return": review.realized_return, "outcome": review.outcome, "notes": review.notes}
        self._append({"type": "review", "review": row})
        return row

    def load(self):
        if not self.path.exists():
            return []
        rows = [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]
        # Outcomes are separate append-only events; the read view joins them
        # back onto their recommendation rows without rewriting history.
        outcomes = {}
        for row in rows:
            if row.get("type") == "outcome" and row.get("horizon") is not None:
                key = (row.get("symbol"), row.get("decision_time"))
                outcomes.setdefault(key, {})[f"T+{row['horizon']}"] = row["realized_return"]
        merged = []
        for row in rows:
            if row.get("type") == "recommendation":
                known = outcomes.get((row.get("symbol"), row.get("decision_time")))
                if known:
                    row = {**row, "outcomes": {**row.get("outcomes", {}), **known}}
            merged.append(row)
        return merged

    def records(self):
        return tuple(self.load())

    def backfill_returns(self, symbol, decision_time, prices):
        """Compatibility helper; emits outcome events instead of rewriting history."""
        matches = [
            x for x in self.records()
            if x.get("type") == "recommendation"
            and x.get("symbol") == symbol
            and x.get("decision_time") == decision_time
        ]
        if not matches:
            return False
        base = float(prices["decision"])
        for horizon in (1, 3, 5, 10):
            if horizon in prices:
                self._append({"type": "outcome", "symbol": symbol, "decision_time": decision_time, "horizon": horizon, "realized_return": float(prices[horizon]) / base - 1.0})
        return True
