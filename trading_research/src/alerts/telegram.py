"""Send-only Telegram alerter.

This module **only sends** messages via the Telegram Bot API. It does
not poll for incoming updates, does not parse commands, does not accept
trade decisions over Telegram. That keeps a leaked bot token from being
able to place orders — approvals must come from a trusted shell via
`approval/cli.py`.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import requests

TELEGRAM_API = "https://api.telegram.org"


class TelegramAlerter:
    def __init__(
        self,
        *,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send(self, text: str, *, parse_mode: str = "Markdown") -> bool:
        """Send `text` to the configured chat. Returns True on success.

        If not configured, prints to stdout and returns False.
        """
        if not self.configured:
            print(f"[telegram dry-run]\n{text}")
            return False
        url = f"{TELEGRAM_API}/bot{self.bot_token}/sendMessage"
        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            if resp.status_code != 200:
                print(
                    f"[telegram] HTTP {resp.status_code}: {resp.text[:200]}",
                    file=sys.stderr,
                )
                return False
            return True
        except requests.RequestException as e:
            print(f"[telegram] network error: {e}", file=sys.stderr)
            return False
