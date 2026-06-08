# Claude Abilities Map

A standalone wallpaper renderer that visualizes, at a glance:

- **Agents** available to Claude Code in this repo
- **Skills** loaded for the current session
- **VS Code extensions** that pair well with these projects
- **Integrations** — Claude in Chrome, kapture (this repo's Chrome
  DevTools extension), GitHub MCP, Figma MCP, Notion MCP

Output is a PNG you can set as a desktop wallpaper. The data is read
from a JSON manifest (`config/abilities.json`) so you can edit what's
shown without touching the renderer.

This is intentionally separate from `wallpapers/` (which renders the
daily research brief). They share the visual idea — render to PNG, set
as desktop background — but the contents are different and the
projects don't depend on each other.

## Layout

```
claude_abilities/
├─ README.md
├─ requirements.txt        # Pillow only
├─ config/
│  └─ abilities.json       # editable manifest of agents/skills/extensions
├─ src/
│  ├─ __init__.py
│  └─ render.py            # CLI that produces output/<slug>.png
└─ output/                 # rendered PNGs land here
```

## Run

```bash
cd claude_abilities
pip install -r requirements.txt

python -m src.render                          # 2560x1440 to output/abilities.png
python -m src.render --width 3840 --height 2160 --output output/abilities-4k.png
python -m src.render --config config/abilities.json   # use a different manifest
```

## Refresh

There's no daemon — re-run the command. Wire it however you like:

- macOS: `launchd` plist that runs the command every hour, then
  `osascript -e 'tell application "Finder" to set desktop picture to ...'`
- Linux + GNOME:
  `gsettings set org.gnome.desktop.background picture-uri-dark "file://$PWD/output/abilities.png"`
- Cron: add an entry that re-renders and sets the wallpaper

## On "Claude home"

If you meant claude.ai's home/UI: this wallpaper cannot reach into
Claude's web UI. It's a local PNG. You can set it as your OS
wallpaper so that when Claude Code is in the foreground, the
abilities map is the visible background.
