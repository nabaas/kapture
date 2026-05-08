# Wallpapers

Standalone project. Renders a desktop wallpaper image from the latest daily
research brief produced by `claude_research_stack/`.

Pure local rendering — no network calls, no API keys.

## Layout

```
wallpapers/
├─ README.md
├─ requirements.txt
├─ src/
│  ├─ __init__.py
│  └─ render_wallpaper.py
└─ output/         # rendered .png images land here
```

## Usage

```bash
cd wallpapers
pip install -r requirements.txt

# Render from the latest report in claude_research_stack/reports/
python -m src.render_wallpaper

# Render from a specific markdown file at a given resolution
python -m src.render_wallpaper \
    --input ../claude_research_stack/reports/2026-05-08T1300.md \
    --width 3840 --height 2160 \
    --output output/today.png
```

## What it does

- Reads a markdown brief.
- Pulls the title (first `#` heading), the date, the first 3 bullets, and
  the first paragraph of the synthesis.
- Renders them onto a solid-background image with Pillow.
- Writes a PNG into `output/`.

The intent is something you can set as a desktop wallpaper or have your OS
refresh on a schedule (macOS: `osascript`, Linux: `feh`/`gsettings`,
Windows: `SystemParametersInfo`). This project does not configure your OS;
it just produces the image file.
