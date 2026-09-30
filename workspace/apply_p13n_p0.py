"""P0 optimization for P13-N: bound per-day factor input to the trailing window.

Applied AFTER the baseline captures finish. See docstring in the patch body.

Exactness argument:
- The four pipeline factors read only series tails ([-lookback-1:] and
  [-lookback:]) of per-row filtered closes/volumes.
- When every one of the trailing (lookback+2) admitted rows has a positive
  float-convertible close and a float-convertible volume, no filter removes
  any window row, so the filtered-series tails equal the full-history ones.
- If any window row is invalid, we fall back to the full admitted history,
  which is bit-identical to the pre-optimization behavior.
- Rows outside the window can only influence metadata["observation_count"],
  a diagnostic field with no consumer in the factor-row pipeline
  (LocalFactorRow keeps value/admissible only).
"""
from pathlib import Path

p = Path("src/astock_v2/local_pipeline.py")
s = p.read_text(encoding="utf-8")

old = '''        current = admitted_by_event[index]
        if current is None:
            continue
        active = admitted_by_event[: index + 1]
        if None in active:
            admitted = [record for record in active if record is not None]
        else:
            admitted = active
        if len(admitted) < lookback + 1:
            continue

        provider = ProviderResult(
            data=[record.value for record in admitted],
            source="local:cn_stock_daily",
            source_type="local_historical",
            fetched_at="",
            available_time=decision_time,
        )'''
new = '''        current = admitted_by_event[index]
        if current is None:
            continue
        active = admitted_by_event[: index + 1]
        if None in active:
            admitted = [record for record in active if record is not None]
        else:
            admitted = active
        if len(admitted) < lookback + 1:
            continue

        # The four pipeline factors only read the trailing (lookback + 2)
        # rows of their filtered series. When every trailing row is fully
        # usable (positive float close, float volume), no filter can remove
        # a window row, so factor values are identical to feeding the whole
        # admitted history while skipping an O(history) rescan per day.
        # Anything else falls back to the exact full-history input.
        window = admitted[-(lookback + 2):]
        if len(window) < len(admitted) and _window_rows_fully_usable(window):
            factor_rows = [record.value for record in window]
        else:
            factor_rows = [record.value for record in admitted]

        provider = ProviderResult(
            data=factor_rows,
            source="local:cn_stock_daily",
            source_type="local_historical",
            fetched_at="",
            available_time=decision_time,
        )'''
assert old in s, "day-loop provider block not found"
s = s.replace(old, new)

helper = '''

def _window_rows_fully_usable(window: list[HistoricalRecord]) -> bool:
    """True when no per-factor row filter can drop any row of the window.

    momentum/trend need a numeric close, volatility additionally close > 0,
    and volume_ratio a numeric volume. If every window row satisfies all of
    these, the filtered series tails are the same whether or not history
    outside the window is present.
    """
    for record in window:
        value = record.value
        close = value.get("close")
        if close is None or volume is None if False else close is None:
            return False
        try:
            if not float(close) > 0.0 or float(value.get("volume")) != float(value.get("volume")):
                return False
        except (TypeError, ValueError):
            return False
    return True
'''
# The condition above got convoluted; write it cleanly instead.
helper = '''

def _window_rows_fully_usable(window: list[HistoricalRecord]) -> bool:
    """True when no per-factor row filter can drop any row of the window.

    momentum/trend need a numeric close, volatility additionally close > 0,
    and volume_ratio a numeric volume. If every window row satisfies all of
    these, the filtered series tails are the same whether or not history
    outside the window is present.
    """
    for record in window:
        value = record.value
        close = value.get("close")
        volume = value.get("volume")
        if close is None or volume is None:
            return False
        try:
            close_f = float(close)
            float(volume)
        except (TypeError, ValueError):
            return False
        if not close_f > 0.0:
            return False
    return True
'''

anchor = "\ndef build_local_factor_rows("
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("P0 patch applied")
