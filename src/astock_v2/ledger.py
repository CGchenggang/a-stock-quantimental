"""Append-only recommendation ledger with immutable event history."""
from __future__ import annotations
import json
from pathlib import Path

class RecommendationLedger:
    def __init__(self, path="workspace/recommendations.jsonl"):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, payload):
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(payload,ensure_ascii=False,sort_keys=True)+"\\n")

    def append(self, record, *, feature_version="unknown", input_snapshot=None):
        row=record.as_dict() if hasattr(record,"as_dict") else dict(record)
        self._append({"type":"recommendation","record":row,"feature_version":feature_version,"input_snapshot":input_snapshot})
        return row

    def append_review(self, review):
        row={"record_id":review.record_id,"review_time":review.review_time,"realized_return":review.realized_return,"outcome":review.outcome,"notes":review.notes}
        self._append({"type":"review","review":row})
        return row

    def load(self):
        if not self.path.exists(): return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def records(self): return tuple(self.load())

    def backfill_returns(self, symbol, decision_time, prices):
        """Compatibility helper; emits a review event instead of rewriting history."""
        matches=[x for x in self.records() if x.get("type")=="recommendation" and x.get("record",{}).get("symbol")==symbol and x.get("record",{}).get("decision_time")==decision_time]
        if not matches: return False
        base=float(prices["decision"])
        for horizon in (1,3,5,10):
            if horizon in prices:
                self._append({"type":"outcome","symbol":symbol,"decision_time":decision_time,"horizon":horizon,"realized_return":float(prices[horizon])/base-1.0})
        return True
