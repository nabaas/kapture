"""Backtest summary metrics.

Inputs are bar-aligned Series of strategy returns (e.g. daily). All
metrics are computed assuming returns are simple arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Metrics:
    n_bars: int
    n_trades: int
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    hit_rate: float

    def as_dict(self) -> dict:
        return {
            "n_bars": self.n_bars,
            "n_trades": self.n_trades,
            "total_return": round(self.total_return, 4),
            "cagr": round(self.cagr, 4),
            "sharpe": round(self.sharpe, 3),
            "max_drawdown": round(self.max_drawdown, 4),
            "hit_rate": round(self.hit_rate, 3),
        }


def _max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min()) if len(dd) else 0.0


def summarize(
    returns: pd.Series,
    *,
    bars_per_year: int = 365,
    trade_marks: pd.Series | None = None,
) -> Metrics:
    """Compute summary metrics from a Series of strategy returns."""
    rets = returns.dropna().astype(float)
    n_bars = int(len(rets))
    if n_bars == 0:
        return Metrics(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    equity = (1.0 + rets).cumprod()
    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (bars_per_year / n_bars) - 1.0)

    sd = float(rets.std())
    sharpe = float(rets.mean() / sd * np.sqrt(bars_per_year)) if sd > 0 else 0.0
    max_dd = _max_drawdown(equity)

    n_trades = int(trade_marks.fillna(0).abs().sum()) if trade_marks is not None else 0
    nonzero = rets[rets != 0]
    hit_rate = float((nonzero > 0).mean()) if len(nonzero) else 0.0

    return Metrics(
        n_bars=n_bars,
        n_trades=n_trades,
        total_return=total_return,
        cagr=cagr,
        sharpe=sharpe,
        max_drawdown=max_dd,
        hit_rate=hit_rate,
    )
