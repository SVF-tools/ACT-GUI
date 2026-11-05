"""Wire primitives shared by every module's schemas (the workbench's shared kernel).

Each module owns its payload models in <module>/schemas.py; visual_bench/schemas.py
aggregates them for code generation. Only types used by more than one module live here.

Numeric encoding: JSON has no Infinity/NaN, so bound values use WireNumber:
a finite float, or one of the strings "Infinity", "-Infinity", "NaN".
"""
from __future__ import annotations

import math
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict

__all__ = ['WireNumber', 'Scalar', 'Availability', 'Verdict', 'Method', 'Domain', 'RunState', 'wire_number',
           'wire_numbers', 'Wire', 'ErrorBody', 'ErrorResponse', 'HealthOut']

WireNumber = Union[float, Literal["Infinity", "-Infinity", "NaN"]]
Scalar = Union[str, int, float, bool, None]
Availability = Literal["available", "pending", "not_recorded", "unsupported"]
Verdict = Literal["certified", "falsified", "unknown", "timeout", "error"]
Method = Literal["interval", "bab", "fuzz"]
# Abstract domain of method "interval" (ACT verify_once): IntervalTF, DualSolver, or HybridzTF + HZSolver.
Domain = Literal["interval", "dual", "hybridz"]
RunState = Literal["queued", "running", "completed", "failed"]


def wire_number(x: float) -> WireNumber:
    if math.isfinite(x):
        return x
    if math.isnan(x):
        return "NaN"
    return "Infinity" if x > 0 else "-Infinity"


def wire_numbers(xs: "list[float] | tuple[float, ...]") -> list[WireNumber]:
    return [wire_number(x) for x in xs]


class Wire(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(Wire):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(Wire):
    error: ErrorBody


class HealthOut(Wire):
    status: Literal["ok"]
    service: str
    version: str
    instance: str  # changes whenever the service process (re)starts
