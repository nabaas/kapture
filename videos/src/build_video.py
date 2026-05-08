"""Orchestrate stages 1→2→3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import compose, script, tts

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="build_video")
    p.add_argument("--input", type=Path, required=True, help="Markdown brief.")
    p.add_argument("--slug", default="brief")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    args = p.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    OUTPUT.mkdir(parents=True, exist_ok=True)
    script_path = OUTPUT / f"{args.slug}.script.json"
    audio_dir = OUTPUT / f"{args.slug}.audio"
    video_path = OUTPUT / f"{args.slug}.mp4"

    payload = script.parse(args.input.read_text(encoding="utf-8"))
    script_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    audio_dir.mkdir(parents=True, exist_ok=True)
    for slide in payload["slides"]:
        tts.synthesize(slide["voiceover"], audio_dir / f"{slide['index']:02d}.wav")

    compose.compose(payload, audio_dir, video_path, (args.width, args.height))
    print(video_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
