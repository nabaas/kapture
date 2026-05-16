"""Stage 1: turn a markdown brief into a per-slide script.

Output is JSON of the shape:

    {
      "title": "...",
      "slides": [
        {"index": 1, "heading": "...", "voiceover": "..."},
        ...
      ]
    }

Heuristics, not LLM-driven, so this stage is deterministic and free.
Override by hand-editing the JSON before stage 2.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse(md: str) -> dict:
    title = "Untitled"
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    slides: list[dict] = []
    for i, line in enumerate(md.splitlines()):
        s = line.strip()
        if s.startswith(("- ", "* ")):
            heading = s[2:].split(".")[0][:80]
            slides.append(
                {
                    "index": len(slides) + 1,
                    "heading": heading,
                    "voiceover": s[2:].strip(),
                }
            )
        if len(slides) >= 6:
            break

    if not slides:
        body = re.sub(r"#.*", "", md)
        chunk = body.strip().split("\n\n")[0][:240]
        slides.append({"index": 1, "heading": title, "voiceover": chunk or title})

    return {"title": title, "slides": slides}


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="script")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    payload = parse(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
