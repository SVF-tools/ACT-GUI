"""Neutral bridge data types shared by engine_bridge modules (see contracts.md).

These are plain frozen dataclasses: no ACT objects, no tensors, no workbench/API types.
Numbers are Python floats; non-finite values are kept as float('inf') here and
encoded explicitly by the workbench wire layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Availability = Literal["available", "pending", "not_recorded", "unsupported"]
Verdict = Literal["certified", "falsified", "unknown", "timeout", "error"]
Method = Literal["interval", "bab"]


class BridgeError(Exception):
    """Expected integration failure. Never a substitute for a scientific verdict."""

    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class Capability:
    name: str
    availability: Availability
    source: str  # where the claim comes from: verified call, missing hook, ...


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Literal["info", "warning", "error"]
    message: str


@dataclass(frozen=True)
class EngineInfo:
    act_root: str
    commit: str | None
    expected_commit: str | None
    tracked_changes: bool | None
    python: str
    torch: str | None
    cuda_available: bool | None
    capabilities: tuple[Capability, ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def usable(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)


@dataclass(frozen=True)
class ParamInfo:
    name: str
    shape: tuple[int, ...] | None  # tensor shape, or None for scalars/strings
    value: str | None  # short scalar rendering; tensors are never copied here


@dataclass(frozen=True)
class LayerDescription:
    layer_id: int
    kind: str
    in_vars: int
    out_vars: int
    output_shape: tuple[int, ...] | None
    preds: tuple[int, ...]
    succs: tuple[int, ...]
    params: tuple[ParamInfo, ...]


@dataclass(frozen=True)
class InputSpec:
    layer_id: int
    kind: str
    lb: tuple[float, ...]
    ub: tuple[float, ...]


@dataclass(frozen=True)
class OutputSpec:
    layer_id: int
    kind: str
    rows: int
    matrix: tuple[tuple[float, ...], ...] | None  # C, one row per constraint lane
    thresholds: tuple[float, ...] | None
    text: str  # human-readable rendering of what ACT checks


@dataclass(frozen=True)
class ModelDescription:
    source_path: str
    sha256: str
    layers: tuple[LayerDescription, ...]
    input_specs: tuple[InputSpec, ...]
    output_spec: OutputSpec | None
    input_dim: int
    output_dim: int


@dataclass(frozen=True)
class LayerState:
    layer_id: int
    kind: str
    stage: Literal["after"]
    lb: tuple[float, ...]
    ub: tuple[float, ...]
    shape: tuple[int, ...]
    before_layer_ids: tuple[int, ...]  # the "before" state is the 'after' state of these preds


@dataclass(frozen=True)
class LayerStates:
    method: Literal["interval"]
    availability: Availability
    layers: tuple[LayerState, ...]
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunOutcome:
    method: Method
    verdict: Verdict
    act_status: str  # raw ACT VerifyStatus name
    elapsed_s: float
    metadata: dict[str, object]
    counterexample: tuple[float, ...] | None
    device: str  # torch default device after the ACT call, e.g. "cpu" or "cuda:0"


LicenseState = Literal["licensed", "restricted", "invalid", "not_installed"]


@dataclass(frozen=True)
class SolverStatus:
    """Result of starting the solver's own license check; not a claim that any method uses it."""
    solver: Literal["gurobi"]
    version: str | None
    license_state: LicenseState
    message: str  # the solver's own license/error lines (credential values are never included)
