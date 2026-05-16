"""Rule-based summarizer for markdown briefs.

Extracts the title, date, top bullets, and the first paragraph of any
"## Synthesis" section. No LLM call — deterministic, free, offline.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Summary:
    title: str
    date: str
    bullets: list[str]
    synthesis: str


def summarize(md: str, *, max_bullets: int = 5) -> Summary:
    title = "Untitled"
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    date = ""
    m = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", md)
    if m:
        date = m.group(1)

    bullets: list[str] = []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:].strip())
        if len(bullets) >= max_bullets:
            break

    synthesis = ""
    in_synth = False
    buf: list[str] = []
    for line in md.splitlines():
        if line.strip().lower().startswith("## synthesis"):
            in_synth = True
            continue
        if in_synth:
            if line.startswith("## "):
                break
            if line.strip():
                buf.append(line.strip())
            elif buf:
                break
    synthesis = " ".join(buf)[:500]

    return Summary(title=title, date=date, bullets=bullets, synthesis=synthesis)


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="summarizer")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--max-bullets", type=int, default=5)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    s = summarize(args.input.read_text(encoding="utf-8"), max_bullets=args.max_bullets)
    if args.format == "json":
        import json as _json
        print(_json.dumps(asdict(s), indent=2))
    else:
        print(f"{s.title}")
        if s.date:
            print(f"date: {s.date}")
        for b in s.bullets:
            print(f"- {b}")
        if s.synthesis:
            print()
            print(s.synthesis)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
