"""Local historical-data contracts and PIT-safe storage metadata.

The catalog deliberately stores provenance separately from the numeric payload.
It does not claim a value is usable merely because it was fetched successfully.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class DataLayer(str, Enum):
    RAW = "raw"
    CLEAN = "clean"
    PIT = "pit"


class AssetScope(str, Enum):
    CN_STOCK = "cn_stock"
    CN_INDEX = "cn_index"
    CN_SECTOR = "cn_sector"
    GLOBAL_INDEX = "global_index"
    FX = "fx"
    COMMODITY = "commodity"
    RATE = "rate"
    POLICY_EVENT = "policy_event"


@dataclass(frozen=True)
class HistoricalRecord:
    symbol: str
    event_time: str
    available_time: str | None
    source: str
    source_type: str
    value: dict
    layer: DataLayer = DataLayer.CLEAN
    asset_scope: AssetScope = AssetScope.CN_STOCK
    revision: int = 0
    raw_ref: str | None = None
    quality: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if not self.event_time:
            raise ValueError("event_time is required")
        if not self.source:
            raise ValueError("source is required")
        if self.revision < 0:
            raise ValueError("revision must be non-negative")

    @property
    def pit_ready(self) -> bool:
        if not self.available_time:
            return False
        try:
            datetime.fromisoformat(self.available_time.replace("Z", "+00:00"))
            datetime.fromisoformat(self.event_time.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True

    def admissible_at(self, decision_time: str) -> bool:
        if not self.pit_ready:
            return False
        available = datetime.fromisoformat(self.available_time.replace("Z", "+00:00"))
        decision = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
        if available.tzinfo is None:
            available = available.replace(tzinfo=timezone.utc)
        if decision.tzinfo is None:
            decision = decision.replace(tzinfo=timezone.utc)
        return available <= decision


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    asset_scope: AssetScope
    frequency: str
    primary_source: str
    local_path: str
    requires_available_time: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.local_path:
            raise ValueError("dataset name and local_path are required")


DEFAULT_DATASETS = (
    DatasetSpec("cn_stock_daily", AssetScope.CN_STOCK, "1d", "akshare", "data/market/cn_stock_daily"),
    DatasetSpec("cn_index_daily", AssetScope.CN_INDEX, "1d", "akshare", "data/market/cn_index_daily"),
    DatasetSpec("global_index_daily", AssetScope.GLOBAL_INDEX, "1d", "provider", "data/market/global_index_daily"),
    DatasetSpec("fx_daily", AssetScope.FX, "1d", "provider", "data/market/fx_daily"),
    DatasetSpec("commodity_daily", AssetScope.COMMODITY, "1d", "provider", "data/market/commodity_daily"),
    DatasetSpec("rate_daily", AssetScope.RATE, "1d", "provider", "data/market/rate_daily"),
    DatasetSpec("policy_events", AssetScope.POLICY_EVENT, "event", "official", "data/events/policy"),
)
