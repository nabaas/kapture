"""Thin wrapper around alpaca-py for market data + paper-mode orders.

Reads ALPACA_API_KEY / ALPACA_API_SECRET from the environment. Live
orders are gated by an explicit acknowledgement env var; paper is the
default and the safest option.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

LIVE_ACK_ENV = "TRADING_RESEARCH_I_UNDERSTAND_THE_RISK"


@dataclass
class Bars:
    symbol: str
    df: pd.DataFrame  # columns: open, high, low, close, volume; tz-aware index


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"environment variable {name} is required for Alpaca access"
        )
    return val


def _live_ok() -> bool:
    return os.environ.get(LIVE_ACK_ENV, "").lower() == "yes"


def get_crypto_bars(
    symbol: str,
    *,
    bars: int = 500,
    bar_size: str = "1Day",
) -> Bars:
    """Fetch recent crypto bars for `symbol` (e.g. "BTC/USD")."""
    from alpaca.data.historical import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    client = CryptoHistoricalDataClient()  # crypto data does not require keys

    unit = {
        "1Min": TimeFrame.Minute,
        "1Hour": TimeFrame.Hour,
        "1Day": TimeFrame.Day,
    }.get(bar_size)
    if unit is None:
        unit = TimeFrame(amount=1, unit_value=TimeFrameUnit.Day)

    end = datetime.now(timezone.utc)
    # generous lookback so we have at least `bars` bars after weekend/gap loss
    start = end - timedelta(days=bars * 2 + 5)

    req = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=unit,
        start=start,
        end=end,
    )
    raw = client.get_crypto_bars(req).df
    if raw.empty:
        return Bars(symbol=symbol, df=raw)
    # Multi-index (symbol, timestamp). Drop symbol level.
    if isinstance(raw.index, pd.MultiIndex):
        raw = raw.xs(symbol, level=0)
    df = raw.tail(bars).copy()
    return Bars(symbol=symbol, df=df)


def trading_client(*, paper: bool):
    """Return an alpaca-py TradingClient. Refuses live without ack."""
    from alpaca.trading.client import TradingClient

    if not paper and not _live_ok():
        raise PermissionError(
            f"refusing to construct a LIVE TradingClient: set "
            f"{LIVE_ACK_ENV}=yes to opt in"
        )
    key = _require_env("ALPACA_API_KEY")
    secret = _require_env("ALPACA_API_SECRET")
    return TradingClient(api_key=key, secret_key=secret, paper=paper)
