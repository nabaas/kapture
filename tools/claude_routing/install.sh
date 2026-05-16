#!/usr/bin/env bash
# Install the UserPromptSubmit routing hook into your local Claude Code.
#
# Idempotent: re-running updates the script and re-merges settings.json
# without duplicating the hook entry.

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
SCRIPTS_DIR="${CLAUDE_DIR}/scripts"
SCRIPT_PATH="${SCRIPTS_DIR}/route_prompt.py"
SETTINGS_PATH="${CLAUDE_DIR}/settings.json"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${SCRIPTS_DIR}"
cp "${HERE}/route_prompt.py" "${SCRIPT_PATH}"
chmod +x "${SCRIPT_PATH}"
echo "wrote ${SCRIPT_PATH}"

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq required. brew install jq / apt-get install jq" >&2
  exit 1
fi

if [[ ! -f "${SETTINGS_PATH}" ]]; then
  echo '{}' > "${SETTINGS_PATH}"
fi

tmp=$(mktemp)
jq '
  .hooks //= {}
  | .hooks.UserPromptSubmit //= []
  | .hooks.UserPromptSubmit |= (
      map(select((.hooks // []) | all(.command != "python3 ~/.claude/scripts/route_prompt.py")))
      + [{ "matcher": "", "hooks": [{ "type": "command", "command": "python3 ~/.claude/scripts/route_prompt.py" }] }]
    )
' "${SETTINGS_PATH}" > "${tmp}"

mv "${tmp}" "${SETTINGS_PATH}"
echo "merged hook into ${SETTINGS_PATH}"

echo
echo "Open Claude Code's /hooks menu once to reload, or restart the session."
echo "Pipe-test:"
echo "  echo '{\"prompt\":\"alpaca order\"}' | python3 ${SCRIPT_PATH}"
