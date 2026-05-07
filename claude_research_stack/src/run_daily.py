"""Autonomous daily research loop.

Reads a topic, loads the master routine prompt, asks Claude to produce a
RunOutput-shaped JSON document, then persists the run via save_run and the
markdown brief via build_report.

Designed to be invoked by .github/workflows/research-daily.yml on a cron,
or manually:

    TOPIC="MCP spec changes" python -m claude_research_stack.src.run_daily

Environment
-----------
- ANTHROPIC_API_KEY  required
- TOPIC              required (or pass --topic)
- CRS_MODEL          optional, defaults to claude-opus-4-7
- CRS_MAX_SOURCES    optional, defaults to 25
- CRS_PRIOR_RUN      optional path to a previous runs/*.json for delta
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_agent import build_report, save_run
from .schemas import RunOutput

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "prompts" / "master_routine.md"

DEFAULT_MODEL = os.environ.get("CRS_MODEL", "claude-opus-4-7")

PRIMARY_TYPES = {
    "official_docs",
    "first_party_repo",
    "standard",
    "changelog",
    "release_notes",
    "academic_paper",
    "patent",
    "conference_talk",
    "announcement",
    "dataset",
}

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _load_master_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _load_prior(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _build_user_message(topic: str, max_sources: int, prior: dict | None) -> str:
    schema = RunOutput.model_json_schema()
    parts = [
        f"Topic: {topic}",
        f"max_sources: {max_sources}",
        "Schema your JSON must validate against:",
        "```json",
        json.dumps(schema, indent=2),
        "```",
    ]
    if prior is not None:
        parts.append(
            "Prior run for delta comparison (note new vs removed sources, "
            "changed claims, resolved conflicts/gaps):"
        )
        parts.append("```json")
        parts.append(json.dumps(prior, indent=2)[:20000])
        parts.append("```")
    parts.append(
        "Reply with a single JSON object matching the schema. No prose."
    )
    return "\n\n".join(parts)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    m = _JSON_FENCE_RE.search(text)
    if not m:
        raise ValueError("model response contained no JSON object")
    return json.loads(m.group(1))


def _call_claude(system: str, user: str, model: str) -> str:
    from anthropic import Anthropic  # type: ignore[import-not-found]

    client = Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"
    )


def _primary_ratio(payload: dict) -> float:
    sources = payload.get("sources", [])
    if not sources:
        return 0.0
    primary = sum(1 for s in sources if s.get("source_type") in PRIMARY_TYPES)
    return primary / len(sources)


def run_once(
    topic: str,
    *,
    model: str = DEFAULT_MODEL,
    max_sources: int = 25,
    prior_run_path: str | None = None,
) -> str:
    """Execute one daily run. Returns the timestamp slug used in filenames."""

    system = _load_master_prompt()
    prior = _load_prior(prior_run_path)
    user = _build_user_message(topic, max_sources, prior)

    raw = _call_claude(system, user, model)
    payload = _extract_json(raw)

    validated = RunOutput.model_validate(payload).model_dump()
    validated["topic"] = validated.get("topic") or topic
    validated["generated_at"] = datetime.now(timezone.utc).isoformat()
    validated["model"] = model
    validated["primary_source_ratio"] = _primary_ratio(validated)
    validated["report"] = build_report(validated)

    return save_run(validated)


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="run_daily")
    p.add_argument("--topic", default=os.environ.get("TOPIC"))
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument(
        "--max-sources",
        type=int,
        default=int(os.environ.get("CRS_MAX_SOURCES", "25")),
    )
    p.add_argument("--prior", default=os.environ.get("CRS_PRIOR_RUN"))
    args = p.parse_args(argv)

    if not args.topic:
        print("error: --topic or TOPIC env var required", file=sys.stderr)
        return 2

    ts = run_once(
        topic=args.topic,
        model=args.model,
        max_sources=args.max_sources,
        prior_run_path=args.prior,
    )
    print(ts)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
