# Claude Research Stack

This repo is a template for a daily autonomous research loop that searches, crawls, extracts, ranks, and synthesizes primary sources.

## Core stack
- Claude Code routines as the orchestrator
- OpenAI web search for grounded discovery
- Crawl4AI or Firecrawl for crawling and extraction
- Pydantic + DuckDB/SQLite for structured storage
- A reranker/scoring layer for authority and recency

## Flow
1. Load topic and constraints.
2. Search broad, then narrow.
3. Crawl the best sources.
4. Extract structured facts.
5. Score and rerank sources.
6. Detect contradictions and missing evidence.
7. Write a daily report and JSON run file.

## Files
- `prompts/master_routine.md`: the executable prompt.
- `src/research_agent.py`: pipeline skeleton.
- `src/schemas.py`: output schemas.
- `runs/`: daily JSON outputs.
- `reports/`: daily markdown briefs.

## Notes
- Prefer primary sources.
- Do not copy-paste long passages.
- Preserve URLs, dates, and evidence trail.

## Daily autonomous loop

The loop is driven by `src/run_daily.py` and scheduled by
`.github/workflows/research-daily.yml`. It:

1. Loads `prompts/master_routine.md` as the system prompt.
2. Calls Claude with the topic, the `RunOutput` JSON schema, and (when
   present) the most recent prior run for delta computation.
3. Validates the model's JSON against `RunOutput`.
4. Calls `build_report(data)` to render the markdown brief and
   `save_run(payload)` to persist `runs/<ts>.json` and
   `reports/<ts>.md`.
5. Commits the artifacts back to the repo so daily runs accumulate.

### Local invocation

```bash
cd claude_research_stack
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
TOPIC="MCP spec changes" python -m src.run_daily
```

Optional env vars: `CRS_MODEL` (default `claude-opus-4-7`),
`CRS_MAX_SOURCES` (default `25`), `CRS_PRIOR_RUN` (path to a previous
`runs/*.json` to anchor deltas).

### GitHub Actions

Set in the repository:

- **Secret** `ANTHROPIC_API_KEY`
- **Variable** `RESEARCH_TOPIC` (or pass `topic` via
  `workflow_dispatch`)

The workflow runs daily at 13:00 UTC and on manual dispatch. It
auto-discovers the most recent `runs/*.json` to feed as the prior run,
so successive days produce comparable diffs.
