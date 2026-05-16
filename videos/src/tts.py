"""Stage 2: render each slide's voiceover to an audio file.

The default `synthesize` writes a 1-second silent WAV so downstream
stages are runnable without a TTS provider. Replace the body to plug
in ElevenLabs / OpenAI / Coqui / Piper / etc.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import wave
from pathlib import Path


def synthesize(text: str, out_path: Path, *, sample_rate: int = 22050) -> Path:
    """Default stub: write a 1-second silent mono WAV.

    Replace with a real TTS call. Keep the signature so callers don't change.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = sample_rate
    silent_frame = struct.pack("<h", 0)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(silent_frame * n_frames)
    return out_path


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="tts")
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True, help="Output directory.")
    args = p.parse_args(argv)

    if not args.script.exists():
        print(f"error: script not found: {args.script}", file=sys.stderr)
        return 2

    payload = json.loads(args.script.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)

    for slide in payload["slides"]:
        out = args.output / f"{slide['index']:02d}.wav"
        synthesize(slide["voiceover"], out)
        print(out)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
