"""P14-D Golden Tests — frozen standard answers exercised through the
production query layer.

The fixtures in fixtures/G-001..G-010.json carry hand-written expected
values (the standard answers). This module feeds each fixture's records
through the PRODUCTION run_query implementation and asserts the fixture's
own expected block — the production code can never define its own
standard answer.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
FIXTURE_DIR = HERE / "fixtures"
sys.path.insert(0, str(REPO_ROOT / "src"))

from astock_v2.information.models import RawInformationRecord  # noqa: E402
from astock_v2.information.research_query import ResearchQuery, run_query  # noqa: E402


def _load_fixtures():
    fixtures = []
    for path in sorted(FIXTURE_DIR.glob("G-*.json")):
        fx = json.loads(path.read_text(encoding="utf-8"))
        assert fx["golden_id"].endswith(path.stem.split("_")[0])
        fixtures.append(fx)
    ids = [f["golden_id"] for f in fixtures]
    assert ids == [f"P14D-G-{i:03d}" for i in range(1, 12)]
    return fixtures


def _record(d: dict) -> RawInformationRecord:
    return RawInformationRecord(
        source=d["source"], source_id=d["source_id"],
        source_category=d["source_category"], entity_id=d["entity_id"],
        entity_type=d["entity_type"], event_time=d["event_time"],
        available_time=d["available_time"], revision=d["revision"],
        ingested_at=d["ingested_at"], value=d.get("value", 1.0),
        quality_status=d.get("quality_status", "OK"),
        freshness_policy_id=d.get("freshness_policy_id"),
        metadata=d.get("metadata", {}))


def _run(fixture: dict) -> dict:
    q = fixture["input"]["query"]
    query = ResearchQuery(entity=q["entity"], information_type=q["information_type"],
                          as_of=q["as_of"], source=q.get("source"))
    records = [_record(r) for r in fixture["input"]["records"]]
    return run_query(records, query)


def _visible_source_ids(result):
    return [r["source_record_id"] for r in result["records"]]


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["golden_id"])
def test_golden_standard_answer(fixture):
    expected = fixture["expected"]
    result = _run(fixture)

    if "visible_order" in expected:
        got = [r["source_record_id"] for r in result["records"]]
        assert got == expected["visible_order"], fixture["golden_id"]
    else:
        got = sorted(_visible_source_ids(result))
        assert got == sorted(expected["visible_source_ids"]), fixture["golden_id"]
    if "revisions" in expected:
        revs = {r["source_record_id"]: r["revision"] for r in result["records"]}
        for source_id, revision in expected["revisions"].items():
            assert revs[source_id] == revision, fixture["golden_id"]
    if "excluded" in expected:
        got_excluded = sorted((e["source_id"], e["reason"])
                              for e in result["excluded"])
        want_excluded = sorted((e["source_id"], e["reason"])
                               for e in expected["excluded"])
        assert got_excluded == want_excluded, fixture["golden_id"]
    else:
        assert result["excluded"] == [], fixture["golden_id"]
    if "provenance_fields" in expected:
        assert tuple(sorted(result["records"][0])) == tuple(sorted(expected["provenance_fields"]))
    if "provenance_values" in expected:
        for key, value in expected["provenance_values"].items():
            assert result["records"][0][key] == value, (fixture["golden_id"], key)


def test_golden_determinism_double_run():
    """P14D-006: same fixture inputs run twice (records reversed on the
    second run) produce identical canonical results."""
    for fixture in _load_fixtures():
        r1 = _run(fixture)
        fixture["input"]["records"] = list(reversed(fixture["input"]["records"]))
        r2 = _run(fixture)
        assert r1 == r2, fixture["golden_id"]
        assert r1["result_id"] == r2["result_id"], fixture["golden_id"]
