from astock_v2.data.pit_store import PITStore
from astock_v2.types import DataPoint

def test_pit_excludes_late_information(tmp_path):
    store=PITStore(tmp_path/"pit.jsonl")
    store.append(DataPoint("000001","2026-01-01T10:00:00","2026-01-01T10:05:00","test","official",1))
    store.append(DataPoint("000001","2026-01-02T10:00:00","2026-01-03T10:05:00","test","official",2))
    rows=store.available_before("2026-01-02T15:00:00","000001")
    assert len(rows)==1 and rows[0]["value"]==1

def test_pit_rejects_invalid_time(tmp_path):
    store=PITStore(tmp_path/"pit.jsonl")
    try:
        store.append(DataPoint("000001","2026-01-02T10:00:00","2026-01-02T09:00:00","test","official",1))
    except ValueError:
        return
    assert False
