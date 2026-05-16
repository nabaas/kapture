"""Built-in stages."""

from __future__ import annotations

import json
from pathlib import Path

from .core import Context, Stage, register


@register("read_text")
def read_text(*, path: str, key: str = "text") -> Stage:
    p = Path(path)

    def stage(ctx: Context) -> Context:
        ctx[key] = p.read_text(encoding="utf-8")
        ctx["source_path"] = str(p)
        return ctx

    return stage


@register("read_latest")
def read_latest(*, dir: str, glob: str = "*", key: str = "text") -> Stage:
    """Read the lexically-last file in `dir` matching `glob`."""

    def stage(ctx: Context) -> Context:
        candidates = sorted(Path(dir).glob(glob))
        if not candidates:
            raise FileNotFoundError(f"no files in {dir} matching {glob}")
        p = candidates[-1]
        ctx[key] = p.read_text(encoding="utf-8")
        ctx["source_path"] = str(p)
        return ctx

    return stage


@register("write_json")
def write_json(*, path: str, key: str = "payload", indent: int = 2) -> Stage:
    p = Path(path)

    def stage(ctx: Context) -> Context:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(ctx[key], indent=indent), encoding="utf-8")
        return ctx

    return stage


@register("append_jsonl")
def append_jsonl(*, path: str, key: str = "payload") -> Stage:
    p = Path(path)

    def stage(ctx: Context) -> Context:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ctx[key]) + "\n")
        return ctx

    return stage


@register("set")
def set_value(*, key: str, value) -> Stage:
    def stage(ctx: Context) -> Context:
        ctx[key] = value
        return ctx

    return stage


@register("count_lines")
def count_lines(*, source_key: str = "text", out_key: str = "line_count") -> Stage:
    def stage(ctx: Context) -> Context:
        ctx[out_key] = len(ctx[source_key].splitlines())
        return ctx

    return stage
