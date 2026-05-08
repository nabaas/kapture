"""Universe construction: watchlist + rolling top-N gainers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .alpaca_client import get_crypto_bars


@dataclass
class GainerRow:
    symbol: str
    pct_change: float


def top_gainers(
    candidates: list[str],
    *,
    lookback_days: int = 7,
    n: int = 5,
) -> list[GainerRow]:
    """Rank `candidates` by total return over the last `lookback_days` daily bars.

    Returns the top `n` by percent change descending. Symbols whose data
    can't be fetched are silently excluded.
    """
    rows: list[GainerRow] = []
    for sym in candidates:
        try:
            bars = get_crypto_bars(sym, bars=lookback_days + 1, bar_size="1Day")
        except Exception:
            continue
        df = bars.df
        if df.empty or len(df) < 2:
            continue
        first = float(df["close"].iloc[0])
        last = float(df["close"].iloc[-1])
        if first <= 0:
            continue
        rows.append(GainerRow(symbol=sym, pct_change=(last - first) / first))
    rows.sort(key=lambda r: r.pct_change, reverse=True)
    return rows[:n]


def merged_universe(watchlist: list[str], gainers: list[GainerRow]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in watchlist + [g.symbol for g in gainers]:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
