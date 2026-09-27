from pathlib import Path
import json
from astock_v2.data.legacy_cache import read_legacy_cache

def test_legacy_cache_preserves_saved_timestamp(tmp_path):
    path=Path(tmp_path)/"hist_000001_120.json"
    path.write_text(json.dumps({"ts":1000.0,"data":{"code":"000001","latest_date":"2026-09-25"}}),encoding="utf-8")
    result=read_legacy_cache(tmp_path,"hist_000001_120",now=1120.0,ttl_seconds=3600)
    assert result["data"]["latest_date"]=="2026-09-25"
    assert result["saved_at_unix"]==1000.0
    assert result["age_seconds"]==120.0

def test_expired_legacy_cache_is_not_fresh(tmp_path):
    path=Path(tmp_path)/"realtime_all.json"
    path.write_text(json.dumps({"ts":1000.0,"data":{"ok":True}}),encoding="utf-8")
    assert read_legacy_cache(tmp_path,"realtime_all",now=1401.0,ttl_seconds=300) is None

def test_malformed_legacy_cache_is_rejected(tmp_path):
    (Path(tmp_path)/"broken.json").write_text("{bad",encoding="utf-8")
    assert read_legacy_cache(tmp_path,"broken") is None
