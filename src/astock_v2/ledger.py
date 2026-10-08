"""Append-only recommendation ledger with immutable event history."""
from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path


def _record_to_dict(record):
    if hasattr(record, "as_dict"):
        return record.as_dict()
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(f"unsupported ledger record: {type(record)!r}")


def _dedup_key(row) -> str:
    """Deterministic idempotency key built ONLY from existing identity
    fields: record_id + the run identity already carried in
    input_snapshot (run_id/result_id/bundle_id — the R4-A/R4-B
    provenance authority). Plain/legacy appends without a run identity
    fall back to (record_id, symbol, decision_time). No new authority is
    introduced; identical keys mean the same logical recommendation."""
    snapshot = row.get("input_snapshot")
    if isinstance(snapshot, dict):
        identity = (row.get("record_id"), snapshot.get("run_id"),
                    snapshot.get("result_id"), snapshot.get("bundle_id"))
        if any(value is not None for value in identity[1:]):
            return json.dumps(identity, sort_keys=True)
    return json.dumps([row.get("record_id"), row.get("symbol"),
                       row.get("decision_time")])


def _parse_ts(value):
    """UTC-normalized ISO timestamp (naive strings are treated as UTC);
    returns None for anything unparseable."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _in_range(value, start, end) -> bool:
    parsed = _parse_ts(value)
    if parsed is None:
        return False
    start_ts = _parse_ts(start) if start is not None else None
    end_ts = _parse_ts(end) if end is not None else None
    return ((start_ts is None or parsed >= start_ts)
            and (end_ts is None or parsed <= end_ts))


class RecommendationLedger:
    def __init__(self, path="workspace/recommendations.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, payload):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def append(self, record, feature_version="unknown", *, input_snapshot=None):
        """Idempotent append: a recommendation whose dedup key already
        exists is NOT written again — the stored event is returned as a
        no-op. Use :meth:`append_with_status` when the caller needs to
        distinguish created from already-exists."""
        event, _created = self._append_idempotent(
            record, feature_version, input_snapshot)
        return event

    def append_with_status(self, record, feature_version="unknown", *,
                           input_snapshot=None):
        """Idempotent append returning {"status": "created"|"already_exists",
        "event": <stored event>}."""
        event, created = self._append_idempotent(
            record, feature_version, input_snapshot)
        return {"status": "created" if created else "already_exists",
                "event": event}

    def _append_idempotent(self, record, feature_version, input_snapshot):
        row = _record_to_dict(record)
        event = {
            "type": "recommendation",
            **row,
            "feature_version": feature_version,
            "input_snapshot": input_snapshot,
            "outcomes": {},
        }
        key = _dedup_key(event)
        existing = self._stored_recommendations()
        if key in existing:
            return existing[key], False
        self._append(event)
        return event, True

    def _stored_recommendations(self):
        """Stored recommendation events keyed by dedup key (file order;
        legacy duplicates collapse to their latest occurrence)."""
        stored = {}
        if not self.path.exists():
            return stored
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("type") == "recommendation":
                stored[_dedup_key(row)] = row
        return stored

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
        reviews = {}
        for row in rows:
            if row.get("type") == "outcome" and row.get("horizon") is not None:
                key = (row.get("symbol"), row.get("decision_time"))
                outcomes.setdefault(key, {})[f"T+{row['horizon']}"] = row["realized_return"]
            elif row.get("type") == "review":
                payload = row.get("review") or {}
                record_key = payload.get("record_id")
                if record_key:
                    # File order is event order: the LAST review for a
                    # record_id is the latest effective review state.
                    reviews[record_key] = dict(payload)
        merged = []
        for row in rows:
            if row.get("type") == "recommendation":
                known = outcomes.get((row.get("symbol"), row.get("decision_time")))
                if known:
                    row = {**row, "outcomes": {**row.get("outcomes", {}), **known}}
                review = reviews.get(row.get("record_id"))
                if review:
                    row = {**row,
                           "review_status": review.get("outcome", row.get("review_status", "OPEN")),
                           "review": review}
            merged.append(row)
        return merged

    def records(self):
        return tuple(self.load())

    def query(self, symbol=None, action=None, status=None, date_range=None):
        """Deterministic filtered read view over recommendation rows
        (post review/outcome join; file order preserved). date_range is a
        (start, end) pair of ISO timestamps compared in UTC — naive
        strings are treated as UTC. Read-only: never touches events."""
        rows = [row for row in self.load()
                if row.get("type") == "recommendation"]
        if symbol is not None:
            rows = [row for row in rows if row.get("symbol") == symbol]
        if action is not None:
            rows = [row for row in rows if row.get("action") == action]
        if status is not None:
            rows = [row for row in rows if row.get("review_status") == status]
        if date_range is not None:
            start, end = date_range
            rows = [row for row in rows
                    if _in_range(row.get("decision_time"), start, end)]
        return rows

    def outcome_stats(self):
        """Basic ledger-level outcome statistics per horizon (T+1/3/5/10).

        Correctness follows the same rule as review.make_review: a
        positive realized return is CORRECT for BUY/HOLD, a negative one
        is CORRECT for SELL, and NO_ACTION (or an exactly-zero return) is
        UNRESOLVED. avg_realized_return averages the realized returns of
        the sampled rows. Pure read view — no event is written."""
        rows = [row for row in self.load()
                if row.get("type") == "recommendation"]
        stats = {}
        for horizon in (1, 3, 5, 10):
            key = f"T+{horizon}"
            samples = []
            for row in rows:
                outcomes = row.get("outcomes") or {}
                if key in outcomes and outcomes[key] is not None:
                    samples.append((row.get("action"), float(outcomes[key])))
            correct = incorrect = unresolved = 0
            returns = []
            for action, realized in samples:
                returns.append(realized)
                if action == "NO_ACTION" or realized == 0:
                    unresolved += 1
                elif (realized > 0) if action != "SELL" else (realized < 0):
                    correct += 1
                else:
                    incorrect += 1
            decisive = correct + incorrect
            stats[key] = {
                "samples": len(samples),
                "correct": correct,
                "incorrect": incorrect,
                "unresolved": unresolved,
                "hit_rate": (correct / decisive) if decisive else None,
                "avg_realized_return": (sum(returns) / len(returns)) if returns else None,
            }
        return stats

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
