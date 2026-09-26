from dataclasses import asdict
from pathlib import Path
import json

HORIZONS=(1,3,5,10)

class RecommendationLedger:
    """Append-only decision snapshots with separate outcome backfill."""

    def __init__(self, path="workspace/recommendations.jsonl"):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, packet, feature_version="unknown", input_snapshot=None):
        row=asdict(packet)
        row["feature_version"]=feature_version
        row["input_snapshot"]=input_snapshot
        row["outcomes"]={}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False)+"\n")
        return row

    def load(self):
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x]

    def backfill_returns(self, symbol, decision_time, prices):
        rows=self.load()
        changed=False
        for row in rows:
            if row.get("symbol") != symbol or row.get("decision_time") != decision_time:
                continue
            base=float(prices["decision"])
            outcomes=row.setdefault("outcomes", {})
            for horizon in HORIZONS:
                if horizon in prices:
                    outcomes[f"T+{horizon}"]=float(prices[horizon])/base-1.0
            changed=True
        if changed:
            self.path.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)+"\n",
                encoding="utf-8",
            )
        return changed
