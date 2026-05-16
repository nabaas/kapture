#!/usr/bin/env bash
# Wire steps 2-5 of the daily run: wallpaper -> pipeline -> notify -> video.
#
# Each step is independent. Failures in optional steps (notify, video) do
# not abort the run — they're logged and skipped. Wallpaper and pipeline
# are required and will fail the script if they break.
#
# Reads the most recent file under claude_research_stack/reports/*.md as
# the day's brief. Run claude_research_stack/src/run_daily.py first, or
# rely on the daily Actions workflow to populate that directory.
#
# Env (all optional):
#   BOT_WEBHOOK_URL   if set, src.notifier posts a summary to this URL
#   BUILD_VIDEO       set to "1" to also produce a daily video (needs ffmpeg)
#   WALLPAPER_WIDTH   default 2560
#   WALLPAPER_HEIGHT  default 1440

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${ROOT}/claude_research_stack/reports"

log() { printf '[run_daily] %s\n' "$*"; }

if [[ ! -d "${REPORTS_DIR}" ]]; then
  echo "error: ${REPORTS_DIR} does not exist. Run the research loop first." >&2
  exit 1
fi

LATEST="$(ls -1 "${REPORTS_DIR}"/*.md 2>/dev/null | sort | tail -n 1 || true)"
if [[ -z "${LATEST}" ]]; then
  echo "error: no markdown reports under ${REPORTS_DIR}." >&2
  exit 1
fi
log "latest brief: ${LATEST}"

WALLPAPER_WIDTH="${WALLPAPER_WIDTH:-2560}"
WALLPAPER_HEIGHT="${WALLPAPER_HEIGHT:-1440}"

# Step 2: wallpaper (required)
log "step 2/5 wallpaper"
(
  cd "${ROOT}/wallpapers"
  python -m src.render_wallpaper \
    --input "${LATEST}" \
    --width "${WALLPAPER_WIDTH}" \
    --height "${WALLPAPER_HEIGHT}"
)

# Step 3: pipeline (required)
log "step 3/5 pipeline"
(
  cd "${ROOT}/pipelines"
  python -m src.run examples/daily_brief_to_jsonl.yml
)

# Step 4: notifier (optional — soft fail)
log "step 4/5 notifier"
if [[ -z "${BOT_WEBHOOK_URL:-}" ]]; then
  log "  BOT_WEBHOOK_URL not set; skipping live post (running dry-run instead)"
fi
if ! ( cd "${ROOT}/bots" && python -m src.notifier --input "${LATEST}" ); then
  log "  notifier failed; continuing"
fi

# Step 5: video (optional — gated on BUILD_VIDEO=1)
log "step 5/5 video"
if [[ "${BUILD_VIDEO:-0}" != "1" ]]; then
  log "  BUILD_VIDEO != 1; skipping"
else
  if ! command -v ffmpeg >/dev/null 2>&1; then
    log "  ffmpeg not on PATH; skipping"
  else
    SLUG="$(date -u +%Y%m%d)"
    (
      cd "${ROOT}/videos"
      python -m src.build_video --input "${LATEST}" --slug "${SLUG}"
    ) || log "  video build failed; continuing"
  fi
fi

log "done"
