"""Scan orchestrator: data → signals → proposal → Telegram alert.

Runs once per invocation. Schedule it however you like (cron, GH Actions,
launchd). It does **not** place orders. Approvals come from
`approval/cli.py`.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

import yaml

from .alerts.telegram import TelegramAlerter
from .approval import store
from .data.alpaca_client import get_crypto_bars
from .data.universe import merged_universe, top_gainers
from .signals.regime import RegimeParams, classify as classify_regime
from .signals.sentiment import NeutralProvider

ROOT = Path(__file__).resolve().parent.parent


def _load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def _resolve_signal(name: str):
    module_name, fn_name = name.rsplit(".", 1)
    mod = importlib.import_module(f"trading_research.src.signals.{module_name}")
    return getattr(mod, fn_name)


def _format_alert(p: store.Proposal) -> str:
    return (
        f"*Proposal `{p.id}`*\n"
        f"`{p.side.upper()}` *{p.symbol}*  qty=`{p.qty}`  "
        f"notional=`${p.notional_usd:.2f}`\n"
        f"score: `{p.score:+.2f}`\n"
        f"reason: {p.reason}\n\n"
        f"To act:\n"
        f"  `python -m trading_research.src.approval.cli approve {p.id}`\n"
        f"  `python -m trading_research.src.approval.cli reject  {p.id}`"
    )


def _scan_symbol(
    symbol: str,
    *,
    bar_size: str,
    bars: int,
    signals_cfg: list[dict],
    sentiment,
) -> tuple[int, str, float] | None:
    """Returns (side, reason, score) if a proposal should fire, else None.

    side: +1 long / -1 short / 0 no-op
    """
    bars_obj = get_crypto_bars(symbol, bars=bars, bar_size=bar_size)
    if bars_obj.df.empty:
        return None
    close = bars_obj.df["close"].astype(float)

    regime = classify_regime(close, RegimeParams())
    last_regime = str(regime.iloc[-1]) if len(regime) else "MID"

    score = 0
    reasons: list[str] = []
    for entry in signals_cfg:
        if entry["name"].startswith("regime."):
            continue
        fn = _resolve_signal(entry["name"])
        params = entry.get("params") or {}
        # Build params dataclass if the signal exposes one; otherwise pass kwargs.
        try:
            sig_series = fn(close, **params) if params else fn(close)
        except TypeError:
            sig_series = fn(close)
        last = int(sig_series.iloc[-1]) if len(sig_series) else 0
        if last != 0:
            score += last
            reasons.append(f"{entry['name']}={last:+d}")

    sent = sentiment.score(symbol)
    if sent != 0:
        score += int(round(sent))
        reasons.append(f"sentiment={sent:+.2f}")

    if score == 0:
        return None
    side = 1 if score > 0 else -1
    reason = f"regime={last_regime}; " + ", ".join(reasons)
    return side, reason, float(score)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="scan")
    p.add_argument("--config", type=Path, default=ROOT / "config" / "default.yml")
    args = p.parse_args(argv)

    cfg = _load_config(args.config)
    sentiment = NeutralProvider()
    alerter = TelegramAlerter() if cfg["alerts"].get("telegram_enabled") else None

    store.expire_stale()
    if len(store.list_open()) >= cfg.get("max_open_proposals", 10):
        print("max_open_proposals reached; skipping scan", file=sys.stderr)
        return 0

    watchlist = cfg["universe"]["watchlist"]
    try:
        gainers = top_gainers(
            watchlist,
            lookback_days=cfg["universe"]["top_gainers_lookback_days"],
            n=cfg["universe"]["top_gainers_n"],
        )
    except Exception as e:
        print(f"top_gainers failed: {e}; falling back to watchlist only", file=sys.stderr)
        gainers = []
    universe = merged_universe(watchlist, gainers)

    n_proposals = 0
    for symbol in universe:
        try:
            res = _scan_symbol(
                symbol,
                bar_size=cfg["backtest"]["bar_size"],
                bars=cfg["backtest"]["bars"],
                signals_cfg=cfg["signals"],
                sentiment=sentiment,
            )
        except Exception as e:
            print(f"scan {symbol} failed: {e}", file=sys.stderr)
            continue
        if not res:
            continue
        side, reason, score = res
        proposal = store.create_proposal(
            symbol=symbol,
            side="buy" if side > 0 else "sell",
            qty=0,  # filled in at approval time by sizing rule
            notional_usd=cfg.get("default_position_usd", 100),
            reason=reason,
            score=score,
            ttl_minutes=cfg.get("proposal_ttl_minutes", 30),
        )
        msg = _format_alert(proposal)
        if alerter:
            alerter.send(msg)
        else:
            print(msg)
        n_proposals += 1

    print(f"scan complete: {n_proposals} proposals, {len(universe)} symbols")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
