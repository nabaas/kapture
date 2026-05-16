# Trading Research Skeleton

Standalone project. **Research and alerting**, not auto-trading.

The end-to-end shape:

```
data ── signals ── backtest
                       │
                       ▼
                  proposal ──► Telegram alert
                       │
                       ▼
            (you run approve.py from a trusted shell)
                       │
                       ▼
                  Alpaca broker
                  (paper by default)
```

No order is ever submitted to Alpaca without a human approving it from a
trusted shell. The Telegram bot is **send-only** — even someone with the
bot token cannot place trades.

## What this is

- A starter set of well-known signals (volatility regime, MA crossover,
  RSI, return z-score, vol-spike breakout) wired through a small
  bar-by-bar backtester.
- An Alpaca data + paper-order client (`alpaca-py` SDK).
- A Telegram alert sender for "here's a candidate trade" notifications.
- An approval store + CLI: every candidate writes a proposal file with a
  TTL; you run `python -m src.approval.cli approve <id>` (or `reject`)
  to act on it.
- A backtester so you can sanity-check a signal's historical behavior
  before letting it generate live alerts.

## What this is **not**

- It is not a "best signals" library. The included signals are starter
  templates — they are not curated for performance, and past performance
  does not predict future returns. Treat the defaults as a smoke test.
- It does not auto-scrape X/Twitter/Grok/Telegram for sentiment. A
  sentiment value is supplied by whatever provider you choose to plug
  into `signals/sentiment.py`.
- It is not financial advice. The output is suggestions, scored, with
  reasons. You decide.

## Defaults — read before configuring

- `mode: paper` — orders go to Alpaca's paper-trading endpoint.
- `live_mode_acknowledged: false` — to flip to live, both
  `mode: live` *and* the env var
  `TRADING_RESEARCH_I_UNDERSTAND_THE_RISK=yes` must be set.
- `require_per_trade_approval: true` — cannot be disabled.
- `proposal_ttl_minutes: 30` — proposals expire if you don't act.

## Layout

```
trading_research/
├─ README.md
├─ requirements.txt
├─ config/default.yml
├─ src/
│  ├─ data/alpaca_client.py
│  ├─ data/universe.py
│  ├─ signals/regime.py
│  ├─ signals/momentum.py
│  ├─ signals/anomaly.py
│  ├─ signals/sentiment.py
│  ├─ backtest/engine.py
│  ├─ backtest/metrics.py
│  ├─ alerts/telegram.py
│  ├─ approval/store.py
│  ├─ approval/cli.py
│  ├─ broker/alpaca_orders.py
│  └─ scan.py
├─ proposals/   # JSON files written by scan.py, consumed by approve.py
├─ fills/       # JSON files written when a proposal is approved + filled
└─ tests/
```

## Setup

```bash
cd trading_research
pip install -r requirements.txt

# Required for any data fetch or order:
export ALPACA_API_KEY=...
export ALPACA_API_SECRET=...

# Optional — Telegram alerts. If unset, scan.py prints the alert instead.
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
```

## Daily flow

```bash
# 1. Run the scan
python -m src.scan --config config/default.yml

#   → for each symbol with a triggered signal:
#     - writes proposals/<id>.json
#     - sends a Telegram alert (or stdout) with the proposal id

# 2. List open proposals
python -m src.approval.cli list

# 3. Act on one
python -m src.approval.cli approve <id>     # routes to broker (paper by default)
python -m src.approval.cli reject  <id>     # marks it dead
```

## Backtesting before trusting a signal

```bash
python -m src.backtest.engine \
  --symbol BTC/USD \
  --signal momentum.ma_crossover \
  --bars 500
```

Reports Sharpe, max drawdown, hit rate, and number of trades. **A good
backtest is not a guarantee.** It's a filter that catches obviously bad
signals.

## On "top trending" inputs

The `signals/sentiment.py` interface returns a number in [-1, 1]. The
default provider returns 0 (neutral) — replace it with whatever data
source you trust. Pulling raw Twitter/X chatter as a buy signal is
generally worse than no signal at all; if you do go that route, do it
through a curated, rate-limited feed under your control.
