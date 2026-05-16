"""Sentiment provider interface.

Returns a float in [-1, 1] for a given symbol, where:
  -1 = strongly negative
   0 = neutral / unknown
  +1 = strongly positive

The default provider returns 0 (neutral). Plug in your own provider by
implementing `Provider.score(symbol)` and registering it in
`scan.py` if you want sentiment to influence proposal scoring.

This module **does not** scrape Twitter/X/Grok/Telegram. If you choose
to use such a feed, do it through a curated, rate-limited source you
control. Raw social-feed sentiment is generally lower-quality than no
sentiment at all.
"""

from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    def score(self, symbol: str) -> float: ...


class NeutralProvider:
    """Default — no opinion."""

    def score(self, symbol: str) -> float:  # noqa: ARG002 - protocol method
        return 0.0


def clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))
