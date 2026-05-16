"""Render the abilities map as a PNG wallpaper.

Reads a JSON manifest of columns (agents, skills, extensions) and draws
them in a clean three-column layout on a dark background.

CLI:
    python -m src.render
    python -m src.render --width 3840 --height 2160 --output output/4k.png
    python -m src.render --config path/to/manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "abilities.json"
DEFAULT_OUTPUT = ROOT / "output" / "abilities.png"

# Palette
BG = (14, 16, 22)
PANEL = (22, 25, 33)
PANEL_BORDER = (38, 44, 56)
FG = (235, 236, 240)
DIM = (150, 154, 165)
ACCENT = (120, 170, 255)
OK = (115, 220, 155)
SOFT = (200, 165, 255)

COLORS = {"accent": ACCENT, "ok": OK, "soft": SOFT, "fg": FG}


@dataclass
class Item:
    name: str
    note: str


@dataclass
class Column:
    heading: str
    color: tuple[int, int, int]
    items: list[Item]


@dataclass
class Manifest:
    title: str
    subtitle: str
    columns: list[Column]


def load_manifest(path: Path) -> Manifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cols = []
    for c in raw.get("columns", []):
        items = [Item(name=i["name"], note=i.get("note", "")) for i in c.get("items", [])]
        cols.append(
            Column(
                heading=c["heading"],
                color=COLORS.get(c.get("color", "fg"), FG),
                items=items,
            )
        )
    return Manifest(
        title=raw.get("title", "Abilities"),
        subtitle=raw.get("subtitle", ""),
        columns=cols,
    )


def _load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    candidates_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in (candidates_bold if bold else candidates_regular):
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
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


def render(manifest: Manifest, *, width: int, height: int, output: Path) -> Path:
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    margin_x = int(width * 0.05)
    margin_y = int(height * 0.07)

    title_font = _load_font(int(height * 0.055), bold=True)
    sub_font = _load_font(int(height * 0.022))
    heading_font = _load_font(int(height * 0.028), bold=True)
    item_font = _load_font(int(height * 0.020), bold=True)
    note_font = _load_font(int(height * 0.016))
    foot_font = _load_font(int(height * 0.015))

    # Title + subtitle
    draw.text((margin_x, margin_y), manifest.title, font=title_font, fill=FG)
    draw.text(
        (margin_x, margin_y + int(height * 0.07)),
        manifest.subtitle,
        font=sub_font,
        fill=DIM,
    )

    # Columns
    n_cols = max(1, len(manifest.columns))
    gutter = int(width * 0.025)
    col_w = (width - 2 * margin_x - gutter * (n_cols - 1)) // n_cols
    col_top = margin_y + int(height * 0.13)
    col_bot = height - int(height * 0.07)

    for ci, col in enumerate(manifest.columns):
        x0 = margin_x + ci * (col_w + gutter)
        y = col_top

        # panel
        draw.rectangle(
            [(x0, y), (x0 + col_w, col_bot)],
            fill=PANEL,
            outline=PANEL_BORDER,
            width=2,
        )

        # heading
        pad = int(width * 0.014)
        draw.text((x0 + pad, y + pad), col.heading, font=heading_font, fill=col.color)
        # underline rule
        rule_y = y + pad + int(height * 0.04)
        draw.line(
            [(x0 + pad, rule_y), (x0 + col_w - pad, rule_y)],
            fill=col.color,
            width=2,
        )

        # items
        cur = rule_y + int(height * 0.018)
        for it in col.items:
            if cur > col_bot - int(height * 0.04):
                break
            draw.text((x0 + pad, cur), f"• {it.name}", font=item_font, fill=FG)
            cur += int(height * 0.028)
            for line in _wrap(draw, it.note, note_font, col_w - 2 * pad - int(width * 0.012)):
                if cur > col_bot - int(height * 0.04):
                    break
                draw.text((x0 + pad + int(width * 0.012), cur), line, font=note_font, fill=DIM)
                cur += int(height * 0.022)
            cur += int(height * 0.010)

    # Footer
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    footer = f"regenerate:  python -m src.render            ·   updated {now}"
    draw.text(
        (margin_x, height - int(height * 0.035)),
        footer,
        font=foot_font,
        fill=DIM,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, format="PNG")
    return output


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="render")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--width", type=int, default=2560)
    p.add_argument("--height", type=int, default=1440)
    args = p.parse_args(argv)

    if not args.config.exists():
        print(f"error: config not found: {args.config}", file=sys.stderr)
        return 2

    manifest = load_manifest(args.config)
    out = render(manifest, width=args.width, height=args.height, output=args.output)
    print(out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
