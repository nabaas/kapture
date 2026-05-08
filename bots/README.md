# Bots

Standalone project. **Utility bots only** — notifiers, summarizers, and
schedule helpers. Not a trading bot, not a Telegram pump-signal client,
not an order-placement framework.

If you want trading automation, that's a separate repo with separate
review and is **not** scoped here. Real-money execution requires a
specifically-built brokerage integration, real risk controls, and human
sign-off — none of which lives in this folder.

## What's here

- `notifier.py` — posts the latest research brief headline + bullets to
  a webhook URL (Slack, Discord, generic). No outbound calls without
  `BOT_WEBHOOK_URL` set.
- `summarizer.py` — produces a short summary of a markdown file using
  rule-based extraction (no LLM call by default).

Both are CLIs and intentionally minimal. They don't subscribe to message
streams, don't run as a daemon, don't hold credentials beyond reading
env vars at invocation.

## Layout

```
bots/
├─ README.md
├─ requirements.txt
└─ src/
   ├─ __init__.py
   ├─ notifier.py
   └─ summarizer.py
```

## Run

```bash
cd bots
pip install -r requirements.txt

export BOT_WEBHOOK_URL=https://hooks.slack.com/services/...   # optional
python -m src.notifier --input ../claude_research_stack/reports/2026-05-08T1300.md

python -m src.summarizer --input ../claude_research_stack/reports/2026-05-08T1300.md
```
