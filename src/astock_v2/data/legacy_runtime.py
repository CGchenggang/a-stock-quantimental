"""Runtime factory that connects V1 data functions to the V2 provider boundary."""
from __future__ import annotations

from typing import Any, Callable

from .legacy_market_provider_impl import LegacyMarketProvider
from .providers import MarketProvider


def build_legacy_market_provider(
    *,
    realtime_fetcher: Callable[[], dict[str, Any]] | None = None,
    daily_fetcher: Callable[[str, int], dict[str, Any]] | None = None,
    intraday_fetcher: Callable[[str, int, int], dict[str, Any]] | None = None,
) -> MarketProvider:
    """Build a V2 provider backed by V1 functions.

    Imports of scripts.data_layer stay inside this compatibility factory so
    the V2 core does not depend directly on legacy implementation details.
    """
    if realtime_fetcher is None or daily_fetcher is None or intraday_fetcher is None:
        from scripts.data_layer import (\n            get_realtime_quotes, get_stock_hist, get_minute_kline,\n            get_sector_board, get_index_daily,\n        )\n\n        realtime_fetcher = realtime_fetcher or get_realtime_quotes\n        daily_fetcher = daily_fetcher or get_stock_hist\n        intraday_fetcher = intraday_fetcher or get_minute_kline\n        sector_fetcher = get_sector_board\n        index_fetcher = get_index_daily

    return LegacyMarketProvider(
        realtime_fetcher=realtime_fetcher,
        daily_fetcher=daily_fetcher,
        intraday_fetcher=intraday_fetcher,
    )
