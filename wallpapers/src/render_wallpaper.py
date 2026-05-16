"""Render a desktop wallpaper image from a markdown research brief.

Reads a markdown file (default: latest report under
claude_research_stack/reports/), extracts a title, the date, a few bullet
points, and the first paragraph of the synthesis, and renders them to a
PNG that can be set as a desktop wallpaper.

Pure local rendering with Pillow. No network calls.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORTS_DIR = ROOT.parent / "claude_research_stack" / "reports"
DEFAULT_OUTPUT_DIR = ROOT / "output"

BG = (18, 18, 22)
FG = (235, 235, 240)
ACCENT = (120, 170, 255)
MUTED = (140, 140, 150)


@dataclass
class Brief:
    title: str
    date: str
    bullets: list[str]
    paragraph: str


def latest_report(reports_dir: Path) -> Path | None:
    if not reports_dir.exists():
        return None
    candidates = sorted(reports_dir.glob("*.md"))
    return candidates[-1] if candidates else None


def parse_brief(md: str) -> Brief:
    lines = md.splitlines()
    title = "Daily research brief"
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    date = ""
    m = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", md)
    if m:
        date = m.group(1)

    bullets: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith(("- ", "* ")):
            bullets.append(s[2:].strip())
        if len(bullets) >= 3:
            break

    paragraph = ""
    in_synth = False
    buf: list[str] = []
    for line in lines:
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
    paragraph = " ".join(buf)[:400]

    return Brief(title=title, date=date, bullets=bullets, paragraph=paragraph)


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    out: list[str] = []
    line = ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def render(brief: Brief, width: int, height: int, output: Path) -> Path:
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    margin = int(width * 0.08)
    inner = width - 2 * margin

    title_font = _load_font(int(height * 0.06))
    bullet_font = _load_font(int(height * 0.028))
    para_font = _load_font(int(height * 0.022))
    meta_font = _load_font(int(height * 0.02))

    y = margin

    if brief.date:
        draw.text((margin, y), brief.date, font=meta_font, fill=ACCENT)
        y += int(height * 0.04)

    for line in _wrap(draw, brief.title, title_font, inner):
        draw.text((margin, y), line, font=title_font, fill=FG)
        y += int(height * 0.075)

    y += int(height * 0.02)

    for b in brief.bullets:
        prefix = "•  "
        for i, line in enumerate(_wrap(draw, b, bullet_font, inner - 60)):
            text = (prefix if i == 0 else "    ") + line
            draw.text((margin, y), text, font=bullet_font, fill=FG)
            y += int(height * 0.038)
        y += int(height * 0.008)

    if brief.paragraph:
        y += int(height * 0.02)
        for line in _wrap(draw, brief.paragraph, para_font, inner):
            draw.text((margin, y), line, font=para_font, fill=MUTED)
            y += int(height * 0.03)

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, format="PNG")
    return output


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="render_wallpaper")
    p.add_argument("--input", type=Path, default=None)
    p.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--width", type=int, default=2560)
    p.add_argument("--height", type=int, default=1440)
    args = p.parse_args(argv)

    src = args.input or latest_report(args.reports_dir)
    if src is None or not src.exists():
        print(
            f"error: no input markdown found (looked in {args.reports_dir}). "
            "Pass --input.",
            file=sys.stderr,
        )
        return 2

    md = src.read_text(encoding="utf-8")
    brief = parse_brief(md)

    out = args.output or (DEFAULT_OUTPUT_DIR / f"{src.stem}.png")
    written = render(brief, args.width, args.height, out)
    print(written)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
