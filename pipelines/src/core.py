"""Pipeline primitives: Context, Stage, Pipeline, registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

Stage = Callable[["Context"], "Context"]
_REGISTRY: dict[str, Callable[..., Stage]] = {}


@dataclass
class Context:
    state: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)


def register(name: str) -> Callable[[Callable[..., Stage]], Callable[..., Stage]]:
    def deco(factory: Callable[..., Stage]) -> Callable[..., Stage]:
        _REGISTRY[name] = factory
        return factory
    return deco


def build(name: str, **params: Any) -> Stage:
    if name not in _REGISTRY:
        raise KeyError(f"unknown stage: {name}. registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name](**params)


@dataclass
class Pipeline:
    name: str
    stages: list[Stage]

    def run(self, ctx: Context | None = None) -> Context:
        ctx = ctx or Context()
        for stage in self.stages:
            ctx = stage(ctx)
        return ctx
