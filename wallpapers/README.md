# Wallpapers

Standalone project. Renders a desktop wallpaper image from the latest daily
research brief produced by `claude_research_stack/`.

Pure local rendering — no network calls, no API keys.

## Layout

```
wallpapers/
├─ README.md
├─ requirements.txt
├─ set_desktop.sh   # OS wallpaper-setter (macOS / Linux / Windows via Git Bash)
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

## Setting it as your desktop wallpaper

`set_desktop.sh` detects your OS/desktop environment and calls the right
command. Run it from the repo root; defaults to the abilities-map PNG.

```bash
# Default — sets claude_abilities/output/abilities.png
./wallpapers/set_desktop.sh

# Set an explicit image
./wallpapers/set_desktop.sh wallpapers/output/today.png
```

Supported targets:
- **macOS** — `osascript` on every connected desktop.
- **Linux GNOME / Unity / Pantheon** — `gsettings` (light + dark URIs).
- **Linux Cinnamon** — `gsettings` with `org.cinnamon.desktop.background`.
- **Linux MATE** — `gsettings` with `org.mate.background`.
- **Linux KDE Plasma** — `plasma-apply-wallpaperimage`.
- **Linux XFCE** — `xfconf-query` on each monitor's `last-image` property.
- **Linux (other)** — falls back to `feh --bg-fill` if present; otherwise
  exits with a clear error and does **not** silently no-op.
- **Windows (Git Bash / MSYS / Cygwin)** — shells out to `powershell.exe`
  and `SystemParametersInfo`.

Exits non-zero on failure. Does not persist the choice across reboots on
every desktop — some environments (XFCE, feh) need a shell-init hook or
systemd unit if you want it to stick.
