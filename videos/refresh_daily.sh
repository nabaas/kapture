#!/bin/bash
# Runs nightly: picks the latest research report and builds a video from it.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS="$REPO/claude_research_stack/reports"
VIDEOS="$REPO/videos"

latest="$(ls -t "$REPORTS"/*.md 2>/dev/null | head -1)"
if [[ -z "$latest" ]]; then
    echo "No reports found in $REPORTS — skipping." >&2
    exit 0
fi

slug="$(date +%Y-%m-%d)"

cd "$VIDEOS"
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 \
    -m src.build_video \
    --input "$latest" \
    --slug "$slug" \
    --width 1920 \
    --height 1080

echo "Built: output/${slug}.mp4"
