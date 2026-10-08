#!/usr/bin/env bash
# Set the OS desktop wallpaper to a PNG from this repo.
#
# Usage:
#   ./wallpapers/set_desktop.sh                              # defaults to the abilities-map PNG
#   ./wallpapers/set_desktop.sh path/to/image.png            # explicit path
#
# Supported:
#   - macOS         (osascript)
#   - Linux         (GNOME, KDE Plasma, XFCE, MATE, Cinnamon; feh fallback)
#   - Windows       (invoked from Git Bash / MSYS / Cygwin; shells out to PowerShell)
#
# Exits non-zero on failure. Never silently falls through to default styling.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_PNG="${REPO_ROOT}/claude_abilities/output/abilities.png"
PNG="${1:-$DEFAULT_PNG}"

if [[ ! -f "$PNG" ]]; then
    echo "error: image not found: $PNG" >&2
    exit 2
fi

# Resolve to an absolute, canonical path so each OS backend gets a clean argument.
PNG="$(cd "$(dirname "$PNG")" && pwd)/$(basename "$PNG")"

uname_s="$(uname -s)"
case "$uname_s" in
    Darwin)
        osascript -e "tell application \"System Events\" to set picture of every desktop to POSIX file \"${PNG}\""
        ;;
    Linux)
        de="${XDG_CURRENT_DESKTOP:-}"
        de_lc="$(printf '%s' "$de" | tr '[:upper:]' '[:lower:]')"
        case "$de_lc" in
            *gnome*|*unity*|*pantheon*)
                gsettings set org.gnome.desktop.background picture-uri "file://${PNG}"
                # GNOME 42+ has a separate dark-mode URI; ignore error on older versions.
                gsettings set org.gnome.desktop.background picture-uri-dark "file://${PNG}" 2>/dev/null || true
                ;;
            *cinnamon*)
                gsettings set org.cinnamon.desktop.background picture-uri "file://${PNG}"
                ;;
            *mate*)
                gsettings set org.mate.background picture-filename "${PNG}"
                ;;
            *kde*|*plasma*)
                if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
                    plasma-apply-wallpaperimage "${PNG}"
                else
                    echo "error: plasma-apply-wallpaperimage not on PATH; install plasma-workspace tools" >&2
                    exit 1
                fi
                ;;
            *xfce*)
                # XFCE stores one last-image key per monitor; set them all.
                mapfile -t props < <(xfconf-query -c xfce4-desktop -l | grep -E '/last-image$' || true)
                if [[ ${#props[@]} -eq 0 ]]; then
                    echo "error: no xfconf last-image properties found; is xfdesktop running?" >&2
                    exit 1
                fi
                for prop in "${props[@]}"; do
                    xfconf-query -c xfce4-desktop -p "$prop" -s "${PNG}"
                done
                ;;
            *)
                if command -v feh >/dev/null 2>&1; then
                    feh --bg-fill "${PNG}"
                else
                    echo "error: unknown desktop (XDG_CURRENT_DESKTOP='${de}'); install feh or extend this script" >&2
                    exit 1
                fi
                ;;
        esac
        ;;
    MINGW*|MSYS*|CYGWIN*)
        # Git Bash / MSYS / Cygwin on Windows — convert path and shell out to PowerShell.
        if command -v cygpath >/dev/null 2>&1; then
            win_png="$(cygpath -w "${PNG}")"
        else
            win_png="${PNG}"
        fi
        powershell.exe -NoProfile -Command "Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class W{[DllImport(\"user32.dll\")]public static extern bool SystemParametersInfo(int u,int a,string s,int f);}'; [W]::SystemParametersInfo(20, 0, '${win_png//\'/\'\'}', 3) | Out-Null"
        ;;
    *)
        echo "error: unsupported OS: ${uname_s}" >&2
        exit 1
        ;;
esac

echo "wallpaper set: ${PNG}"
