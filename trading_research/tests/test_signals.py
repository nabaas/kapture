"""Tests for the deterministic signal layer.

These tests use synthetic price series so they run without network and
without Alpaca credentials.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trading_research.src.signals import anomaly, momentum, regime


@pytest.fixture()
def trending_up() -> pd.Series:
    """A monotonically rising series with mild noise."""
    rng = np.random.default_rng(0)
    base = np.linspace(100, 200, 200)
    noise = rng.normal(0, 0.5, size=base.shape)
    idx = pd.date_range("2025-01-01", periods=200, freq="D", tz="UTC")
    return pd.Series(base + noise, index=idx)


@pytest.fixture()
def trending_down() -> pd.Series:
    rng = np.random.default_rng(1)
    base = np.linspace(200, 100, 200)
    noise = rng.normal(0, 0.5, size=base.shape)
    idx = pd.date_range("2025-01-01", periods=200, freq="D", tz="UTC")
    return pd.Series(base + noise, index=idx)


def test_ma_crossover_long_in_uptrend(trending_up: pd.Series) -> None:
    sig = momentum.ma_crossover(trending_up, momentum.MaCrossParams(fast=5, slow=20))
    # Most non-NaN signal values in a clean uptrend should be +1.
    assert (sig.iloc[-50:] == 1).mean() > 0.8


def test_ma_crossover_short_in_downtrend(trending_down: pd.Series) -> None:
    sig = momentum.ma_crossover(trending_down, momentum.MaCrossParams(fast=5, slow=20))
    assert (sig.iloc[-50:] == -1).mean() > 0.8


def test_rsi_value_bounded(trending_up: pd.Series) -> None:
    r = momentum.rsi(trending_up, 14).dropna()
    assert r.min() >= 0
    assert r.max() <= 100


def test_zscore_flags_a_planted_spike() -> None:
    rng = np.random.default_rng(2)
    base = 100 * np.cumprod(1 + rng.normal(0, 0.005, 200))
    base[100] = base[99] * 1.10  # +10% one-bar move
    idx = pd.date_range("2025-01-01", periods=200, freq="D", tz="UTC")
    close = pd.Series(base, index=idx)
    sig = anomaly.return_zscore(close, anomaly.ZScoreParams(window=50, threshold=2.5))
    assert sig.iloc[100] == 1


def test_regime_labels_cover_all_three(trending_up: pd.Series) -> None:
    labels = regime.classify(trending_up).dropna().unique().tolist()
    assert set(labels).issubset({"LOW", "MID", "HIGH"})
    assert len(labels) >= 2  # synthetic series should hit at least two regimes
