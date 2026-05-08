"""Tests for the backtester."""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_research.src.backtest.engine import run
from trading_research.src.backtest.metrics import summarize


def _series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2025-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


def test_perfect_signal_makes_money() -> None:
    # Price oscillates predictably; signal knows the next bar's direction.
    closes = _series([100, 101, 100, 101, 100, 101, 100, 101, 100, 101])
    rets = closes.pct_change().fillna(0)
    perfect = pd.Series(np.sign(rets.shift(-1)).fillna(0), index=closes.index)
    res = run(closes, perfect, cost_bps=0)
    assert res.metrics.total_return > 0


def test_zero_signal_zero_return() -> None:
    closes = _series([100, 101, 99, 102, 98, 103])
    flat = pd.Series(0, index=closes.index)
    res = run(closes, flat)
    assert abs(res.metrics.total_return) < 1e-12


def test_summarize_smoke() -> None:
    rng = np.random.default_rng(0)
    rets = pd.Series(rng.normal(0.0005, 0.01, 250))
    m = summarize(rets)
    assert m.n_bars == 250
    assert -1.0 <= m.max_drawdown <= 0.0
    assert m.sharpe == m.sharpe  # not NaN
