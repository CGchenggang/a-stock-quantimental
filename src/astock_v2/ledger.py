from dataclasses import asdict
from pathlib import Path
import json

class RecommendationLedger:
    def __init__(self, path="workspace/recommendations.jsonl"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def append(self, packet):
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(asdict(packet),ensure_ascii=False)+"\n")
    def load(self):
        if not self.path.exists(): return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x]
