#!/usr/bin/env python3
"""UserPromptSubmit routing hook for Claude Code.

Reads the prompt from stdin (Claude Code's hook payload JSON), heuristic-
classifies it, and emits a one-line `additionalContext` recommendation.

This hook LABELS where a prompt is best handled. It does NOT switch IDEs,
open windows, or forward the prompt to another app — Claude Code cannot do
those things from a UserPromptSubmit hook. The label is informational; this
session still answers the prompt.

Categories:
  CODE       build/edit/refactor/test/debug/file ops, "run X", "fix Y"
  RESEARCH   open-ended Q/A: "what is", "how should", "explain", "compare"
  IDE_HEAVY  bulk edits across the project, cross-file rename
  DIAGRAM    Figma, FigJam, diagram, sketch, wireframe, flowchart
  TRADING    Alpaca, broker, signals, orders, positions — gated to
             trading_research/ with the human-approval flow
  AMBIGUOUS  no strong signal — treat as CODE by default

Exit: always 0. The recommendation is informational; the hook never blocks.
"""

from __future__ import annotations

import json
import re
import sys

CATEGORIES = {
    "CODE": "→ Routing: CODE — Claude Code is the right surface; handle here.",
    "RESEARCH": "→ Routing: RESEARCH — open-ended; consider claude.ai chat or Cowork. I'll still answer here.",
    "IDE_HEAVY": "→ Routing: IDE_HEAVY — cross-file rename / bulk edits. Use Claude Code or Cursor in your IDE.",
    "DIAGRAM": "→ Routing: DIAGRAM — Figma/FigJam MCP or a diagram tool fits better. I'll still answer here.",
    "TRADING": "→ Routing: TRADING — use trading_research/ with the approval gate. No auto-execute, no whale-mirroring, no pump-channel scraping.",
    "AMBIGUOUS": "→ Routing: AMBIGUOUS — treating as a Code task.",
}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "TRADING",
        re.compile(
            r"\b(alpaca|broker|trade|trading|order|position|portfolio|backtest|"
            r"stop[- ]?loss|whale|pump signal|telegram pump|ipo|short[- ]selling|"
            r"long position|rsi|moving average|crossover|sentiment meter|"
            r"breakout pattern|regime selection)\b",
            re.I,
        ),
    ),
    (
        "DIAGRAM",
        re.compile(
            r"\b(figma|figjam|diagram|sketch|wireframe|mockup|flowchart|whiteboard)\b",
            re.I,
        ),
    ),
    (
        "IDE_HEAVY",
        re.compile(
            r"\b(rename .* across|find and replace|cross[- ]file refactor|"
            r"in every file|throughout the (project|codebase)|"
            r"all files matching)\b",
            re.I,
        ),
    ),
    (
        "CODE",
        re.compile(
            r"\b(write|build|implement|create|fix|debug|refactor|test|lint|"
            r"run|edit|push|commit|branch|pr|workflow|hook|script|module|"
            r"function|class|component|scaffold|wire|install|deploy)\b",
            re.I,
        ),
    ),
    (
        "RESEARCH",
        re.compile(
            r"\b(what is|how should|why does|explain|compare|tradeoff|tradeoffs|"
            r"design (decision|choice)|should i|when to use|what are the)\b",
            re.I,
        ),
    ),
]


def classify(prompt: str) -> str:
    for label, pat in PATTERNS:
        if pat.search(prompt):
            return label
    return "AMBIGUOUS"


def _extract_prompt(payload: dict) -> str:
    for key in ("prompt", "user_prompt", "user_message", "message", "text"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}}))
        return 0

    prompt = _extract_prompt(payload)
    label = classify(prompt) if prompt else "AMBIGUOUS"
    msg = CATEGORIES.get(label, CATEGORIES["AMBIGUOUS"])

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": msg,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
