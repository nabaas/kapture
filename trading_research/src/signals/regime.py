"""Volatility regime classifier.

Classifies each bar into LOW / MID / HIGH volatility regimes by comparing
the rolling realized volatility to its own quantiles over a recent
window. Output is a Series aligned with the input price index.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd


class Regime(str, Enum):
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"


@dataclass
class RegimeParams:
    window: int = 30
    low_quantile: float = 0.25
    high_quantile: float = 0.75


def realized_vol(close: pd.Series, window: int) -> pd.Series:
    rets = np.log(close / close.shift(1))
    return rets.rolling(window).std() * np.sqrt(window)


def classify(close: pd.Series, params: RegimeParams | None = None) -> pd.Series:
    p = params or RegimeParams()
    vol = realized_vol(close, p.window)
    lo = vol.quantile(p.low_quantile)
    hi = vol.quantile(p.high_quantile)
    out = pd.Series(index=close.index, dtype="object")
    out[vol <= lo] = Regime.LOW.value
    out[(vol > lo) & (vol < hi)] = Regime.MID.value
    out[vol >= hi] = Regime.HIGH.value
    return out
