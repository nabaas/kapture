"""CLI entry: `python -m src.run <pipeline.yml>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import stages  # noqa: F401  (registers built-ins)
from .core import Context, Pipeline, build


def load(path: Path) -> Pipeline:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    name = spec.get("name", path.stem)
    stages_spec = spec.get("stages", [])
    built = []
    for entry in stages_spec:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise ValueError(f"each stage must be a single-key mapping; got {entry!r}")
        (stage_name, params), = entry.items()
        params = params or {}
        built.append(build(stage_name, **params))
    return Pipeline(name=name, stages=built)


def _cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="run")
    p.add_argument("spec", type=Path)
    args = p.parse_args(argv)

    if not args.spec.exists():
        print(f"error: spec not found: {args.spec}", file=sys.stderr)
        return 2

    pipeline = load(args.spec)
    ctx = pipeline.run()
    print(f"pipeline={pipeline.name} keys={sorted(ctx.state)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli(sys.argv[1:]))
