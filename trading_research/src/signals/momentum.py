"""Momentum signals: MA crossover and RSI extremes.

Each signal returns a Series in {-1, 0, 1}:
  -1 = short / sell
   0 = no position / no edge
  +1 = long / buy

These are starter templates, not curated alpha.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class MaCrossParams:
    fast: int = 10
    slow: int = 30


def ma_crossover(close: pd.Series, params: MaCrossParams | None = None) -> pd.Series:
    p = params or MaCrossParams()
    fast = close.rolling(p.fast).mean()
    slow = close.rolling(p.slow).mean()
    sig = pd.Series(0, index=close.index, dtype=int)
    sig[fast > slow] = 1
    sig[fast < slow] = -1
    return sig


@dataclass
class RsiParams:
    window: int = 14
    lower: float = 30.0
    upper: float = 70.0


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def rsi_extremes(close: pd.Series, params: RsiParams | None = None) -> pd.Series:
    p = params or RsiParams()
    r = rsi(close, p.window)
    sig = pd.Series(0, index=close.index, dtype=int)
    sig[r < p.lower] = 1   # oversold → mean-revert long
    sig[r > p.upper] = -1  # overbought → mean-revert short
    return sig
