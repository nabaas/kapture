"""Post a short summary of a markdown brief to a webhook URL.

Reads BOT_WEBHOOK_URL from the environment. If unset, prints what would
have been posted and exits 0 (dry-run friendly). Uses only the standard
library — no third-party HTTP client.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def build_message(md: str, *, max_bullets: int = 5) -> dict:
    title = "Daily research brief"
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    bullets: list[str] = []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:].strip())
        if len(bullets) >= max_bullets:
            break

    text_lines = [f"*{title}*"]
    text_lines.extend(f"• {b}" for b in bullets)
    return {"text": "\n".join(text_lines)}


def post(url: str, payload: dict, *, timeout: float = 10.0) -> int:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="notifier")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument(
        "--url",
        default=os.environ.get("BOT_WEBHOOK_URL"),
        help="Webhook URL. Defaults to $BOT_WEBHOOK_URL.",
    )
    p.add_argument("--max-bullets", type=int, default=5)
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    md = args.input.read_text(encoding="utf-8")
    msg = build_message(md, max_bullets=args.max_bullets)

    if not args.url:
        print("dry-run (no BOT_WEBHOOK_URL):")
        print(msg["text"])
        return 0

    code = post(args.url, msg)
    print(f"posted status={code}")
    return 0 if 200 <= code < 300 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
