import json
from pathlib import Path

from astock_v2.cli import main


def test_cli_legacy_snapshot_keeps_unknown_freshness(monkeypatch, tmp_path, capsys):
    morning = Path(tmp_path) / "morning.json"
    morning.write_text(
        json.dumps({"generated_at": "2026-09-27T08:30:00+08:00"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["astock-v2", "legacy-snapshot", "--morning", str(morning)],
    )
    main()
    result = json.loads(capsys.readouterr().out)
    item = result["outputs"]["morning"]
    assert item["freshness_status"] == "UNKNOWN"
    assert item["realtime_admissible"] is False
    assert item["source"] == "legacy_morning_collector"


def test_cli_legacy_snapshot_accepts_both_legacy_outputs(monkeypatch, tmp_path, capsys):
    morning = Path(tmp_path) / "morning.json"
    pre = Path(tmp_path) / "pre.json"
    for path in (morning, pre):
        path.write_text(json.dumps({"generated_at": "2026-09-27T08:30:00+08:00"}), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["astock-v2", "legacy-snapshot", "--morning", str(morning), "--pre-market", str(pre)],
    )
    main()
    result = json.loads(capsys.readouterr().out)
    assert set(result["outputs"]) == {"morning", "pre_market"}
