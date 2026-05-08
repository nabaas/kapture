"""Bar-by-bar backtester for a single signal on a single instrument.

The strategy:
  - Take the signal's value at bar t, hold position from t to t+1.
  - Strategy return at t+1 = position_t * arithmetic_return_{t→t+1}.
  - Apply a flat per-trade cost (bps) when position changes.

Not vectorized for speed — clarity over throughput. Good enough to
sanity-check a signal before letting it produce live alerts.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .metrics import Metrics, summarize


@dataclass
class BacktestResult:
    metrics: Metrics
    equity: pd.Series
    returns: pd.Series
    positions: pd.Series


def run(
    close: pd.Series,
    signal: pd.Series,
    *,
    cost_bps: float = 10.0,
) -> BacktestResult:
    aligned = pd.concat([close.rename("close"), signal.rename("signal")], axis=1)
    aligned = aligned.dropna()

    arith = aligned["close"].pct_change().fillna(0.0)
    positions = aligned["signal"].shift(1).fillna(0).astype(float)

    trades = positions.diff().abs().fillna(positions.abs())
    cost = trades * (cost_bps / 1e4)

    rets = positions * arith - cost
    equity = (1.0 + rets).cumprod()
    metrics = summarize(rets, trade_marks=trades)
    return BacktestResult(metrics=metrics, equity=equity, returns=rets, positions=positions)


def _resolve_signal(signal_name: str):
    """signal_name like "momentum.ma_crossover" → callable on a close Series."""
    if "." not in signal_name:
        raise ValueError(f"signal must be 'module.fn', got {signal_name!r}")
    module_name, fn_name = signal_name.rsplit(".", 1)
    mod = importlib.import_module(f"trading_research.src.signals.{module_name}")
    return getattr(mod, fn_name)


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="backtest")
    p.add_argument("--symbol", default="BTC/USD")
    p.add_argument("--signal", default="momentum.ma_crossover")
    p.add_argument("--bars", type=int, default=500)
    p.add_argument("--cost-bps", type=float, default=10.0)
    args = p.parse_args(argv)

    from ..data.alpaca_client import get_crypto_bars

    bars = get_crypto_bars(args.symbol, bars=args.bars)
    if bars.df.empty:
        print(f"no bars for {args.symbol}", file=sys.stderr)
        return 2
    close = bars.df["close"].astype(float)

    signal_fn = _resolve_signal(args.signal)
    sig = signal_fn(close)

    res = run(close, sig, cost_bps=args.cost_bps)
    print(json.dumps({"symbol": args.symbol, "signal": args.signal, **res.metrics.as_dict()}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
