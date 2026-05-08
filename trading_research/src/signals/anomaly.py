"""Anomaly / breakout detectors.

Two flavors:
- return_zscore: |log-return| over the last bar exceeds N rolling std devs.
- vol_spike: realized vol over a short window jumps relative to a long window.

Both return a Series in {-1, 0, 1} where the sign is the direction of the
move (positive = up move, negative = down move) on the bar that breached
the threshold.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ZScoreParams:
    window: int = 50
    threshold: float = 2.5


def return_zscore(close: pd.Series, params: ZScoreParams | None = None) -> pd.Series:
    p = params or ZScoreParams()
    rets = np.log(close / close.shift(1))
    mu = rets.rolling(p.window).mean()
    sd = rets.rolling(p.window).std()
    z = (rets - mu) / sd
    sig = pd.Series(0, index=close.index, dtype=int)
    sig[z >= p.threshold] = 1
    sig[z <= -p.threshold] = -1
    return sig


@dataclass
class VolSpikeParams:
    short: int = 5
    long: int = 30
    ratio: float = 1.75


def vol_spike(close: pd.Series, params: VolSpikeParams | None = None) -> pd.Series:
    p = params or VolSpikeParams()
    rets = np.log(close / close.shift(1))
    short_vol = rets.rolling(p.short).std()
    long_vol = rets.rolling(p.long).std()
    spike = (short_vol / long_vol) >= p.ratio
    direction = np.sign(rets)
    sig = pd.Series(0, index=close.index, dtype=int)
    sig[spike] = direction[spike].astype(int)
    return sig
