# Claude Code routing hook (portable install)

A `UserPromptSubmit` hook that labels every prompt with a routing
recommendation (`CODE` / `RESEARCH` / `IDE_HEAVY` / `DIAGRAM` /
`TRADING` / `AMBIGUOUS`).

**This labels — it does not switch apps.** Claude Code cannot move
windows or forward prompts to other surfaces. The hook adds a one-line
hint to context so the assistant can suggest the right surface, and so
you can see at a glance whether a prompt was misrouted.

## Install on your machine

```bash
bash tools/claude_routing/install.sh
# then open Claude Code's /hooks menu once to reload, or restart the session
```

## Files

- `route_prompt.py` — the classifier. Stdlib only; no third-party deps.
- `install.sh` — idempotent installer. Copies the script to
  `~/.claude/scripts/`, merges a `UserPromptSubmit` hook into
  `~/.claude/settings.json`, preserves any existing hooks.

## Behavior

The hook is informational and never blocks (`exit 0` always). On
malformed stdin it emits an empty `additionalContext` and returns.

## Tweaking categories

Edit the `PATTERNS` list in `route_prompt.py`. First match wins. After
editing, re-run `install.sh` to copy the new version to `~/.claude/`.
