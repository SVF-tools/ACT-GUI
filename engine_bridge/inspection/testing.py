"""Synthetic observation producer; these fixtures are not ACT computation evidence."""
from __future__ import annotations

import importlib
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from engine_bridge.engine_session import act_imports


def observation_api():
    """Use the real observer registry when present, otherwise a schema-only stub."""
    with act_imports():
        try:
            return importlib.import_module("act.back_end.observe")
        except ModuleNotFoundError as exc:
            if exc.name != "act.back_end.observe":
                raise

    @dataclass
    class RecordKey:
        domain: str
        pass_: str
        layer_id: int
        stage: str = "out"
        version: int = 0
        scope: str = "root"
        parent: str | None = None
        origin: str = "computed"

    @dataclass
    class PhaseEvent:
        phase: str
        status: str
        t_ns: int
        meta: dict = field(default_factory=dict)

    @dataclass
    class LayerBounds:
        key: Any
        kind: str
        lb: Any
        ub: Any
        t_ns: int
        changed: bool = True

    @dataclass
    class Relaxation:
        key: Any
        status: Any
        form: str
        lower_slope: Any = None
        lower_intercept: Any = None
        upper_slope: Any = None
        upper_intercept: Any = None
        extra: dict = field(default_factory=dict)

    @dataclass
    class DualBackward:
        key: Any
        alpha: Any
        alpha_optimized: bool
        nu: Any = None

    @dataclass
    class SpecBound:
        key: Any
        margins: Any
        slack: Any
        iterations: int
        stop_reason: str

    sinks = []

    @contextmanager
    def observe(sink):
        sinks.append(sink)
        try:
            yield sink
        finally:
            sinks.remove(sink)

    def emit(record):
        for sink in sinks:
            sink(record)

    return SimpleNamespace(RecordKey=RecordKey, PhaseEvent=PhaseEvent, LayerBounds=LayerBounds,
                           Relaxation=Relaxation, DualBackward=DualBackward, SpecBound=SpecBound,
                           observe=observe, emit=emit)
