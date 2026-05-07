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
