# Pipelines

Standalone project. A small ETL framework for running scheduled
extract → transform → load pipelines on local files.

Independent from the research, wallpapers, videos, and bots projects.
You can wire any of them together by pointing one pipeline's input at
another's output, but the projects do not depend on each other.

## Layout

```
pipelines/
├─ README.md
├─ requirements.txt
├─ src/
│  ├─ __init__.py
│  ├─ core.py           # Pipeline / Stage / Context primitives
│  ├─ stages.py         # built-in stages (read_text, write_json, jsonl_append)
│  └─ run.py            # CLI: `python -m src.run <pipeline.yml>`
├─ examples/
│  └─ daily_brief_to_jsonl.yml
└─ data/                # default landing zone for outputs
```

## Concepts

- **Pipeline**: an ordered list of stages.
- **Stage**: a callable that takes a `Context` and returns it (mutated).
- **Context**: a dict-shaped state object the stages read from and write
  to. Inputs and outputs both flow through it.

A pipeline is described by a YAML file: a name, a list of stages, and
each stage's parameters. Custom stages register via
`@register("stage_name")`.

## Run

```bash
cd pipelines
pip install -r requirements.txt
python -m src.run examples/daily_brief_to_jsonl.yml
```
