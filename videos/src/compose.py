"""Stage 3: render slides as PNGs and compose into an mp4 with ffmpeg.

Uses ffmpeg from PATH if available, otherwise falls back to the binary
bundled with the imageio-ffmpeg package.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (12, 14, 18)
FG = (240, 240, 245)
ACCENT = (120, 170, 255)


def _ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("ffmpeg not found — install it or: pip install imageio-ffmpeg")


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def render_slide(heading: str, body: str, size: tuple[int, int], out: Path) -> Path:
    w, h = size
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)
    margin = int(w * 0.08)
    h_font = _load_font(int(h * 0.07))
    b_font = _load_font(int(h * 0.035))
    y = int(h * 0.18)
    for line in _wrap(draw, heading, h_font, w - 2 * margin):
        draw.text((margin, y), line, font=h_font, fill=ACCENT)
        y += int(h * 0.085)
    y += int(h * 0.04)
    for line in _wrap(draw, body, b_font, w - 2 * margin):
        draw.text((margin, y), line, font=b_font, fill=FG)
        y += int(h * 0.05)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    return out


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def compose(script: dict, audio_dir: Path, out: Path, size: tuple[int, int]) -> Path:
    ffmpeg = _ffmpeg_exe()

    work = out.parent / f".{out.stem}_work"
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []

    for slide in script["slides"]:
        idx = slide["index"]
        png = work / f"{idx:02d}.png"
        render_slide(slide["heading"], slide["voiceover"], size, png)

        wav = audio_dir / f"{idx:02d}.wav"
        if not wav.exists():
            raise FileNotFoundError(f"missing audio for slide {idx}: {wav}")
        dur = max(_wav_duration(wav), 0.5)

        seg = work / f"{idx:02d}.mp4"
        subprocess.run(
            [
                ffmpeg, "-y", "-loop", "1", "-i", str(png),
                "-i", str(wav),
                "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-t", str(dur),
                str(seg),
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        parts.append(seg)

    concat_list = work / "concat.txt"
    concat_list.write_text("\n".join(f"file '{p}'" for p in parts), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(out)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return out


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="compose")
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--audio-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    args = p.parse_args(argv)

    if not args.script.exists():
        print(f"error: script not found: {args.script}", file=sys.stderr)
        return 2
    payload = json.loads(args.script.read_text(encoding="utf-8"))
    out = compose(payload, args.audio_dir, args.output, (args.width, args.height))
    print(out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
