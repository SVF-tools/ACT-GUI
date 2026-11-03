"""Workbench wire schemas: the single handwritten source for REST/SSE payloads.

Browser types in visual_bench/generated/wire.ts are generated from these models
(npm run gen:types; npm run check:types fails on drift).

Numeric encoding: JSON has no Infinity/NaN, so bound values use WireNumber:
a finite float, or one of the strings "Infinity", "-Infinity", "NaN".
"""
from __future__ import annotations

import math
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

WireNumber = Union[float, Literal["Infinity", "-Infinity", "NaN"]]
Scalar = Union[str, int, float, bool, None]
Availability = Literal["available", "pending", "not_recorded", "unsupported"]
Verdict = Literal["certified", "falsified", "unknown", "timeout", "error"]
Method = Literal["interval", "bab", "fuzz"]
RunState = Literal["queued", "running", "completed", "failed"]


def wire_number(x: float) -> WireNumber:
    if math.isfinite(x):
        return x
    if math.isnan(x):
        return "NaN"
    return "Infinity" if x > 0 else "-Infinity"


class Wire(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(Wire):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(Wire):
    error: ErrorBody


class CapabilityOut(Wire):
    name: str
    availability: Availability
    source: str


class DiagnosticOut(Wire):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str


class EngineInfoOut(Wire):
    act_root: str
    commit: str | None
    expected_commit: str | None
    tracked_changes: bool | None
    python: str
    torch: str | None
    cuda_available: bool | None
    usable: bool
    capabilities: list[CapabilityOut]
    diagnostics: list[DiagnosticOut]


class HealthOut(Wire):
    status: Literal["ok"]
    service: str
    version: str


class NativeResult(Wire):
    status: str
    elapsed_s: float
    nodes: int | None


class ModelSummary(Wire):
    model_id: str
    description: str
    act_path: str
    sha256: str
    methods: list[Method]
    native: dict[str, NativeResult]


class ParamOut(Wire):
    name: str
    shape: list[int] | None
    value: str | None


class LayerOut(Wire):
    layer_id: int
    kind: str
    in_vars: int
    out_vars: int
    output_shape: list[int] | None
    preds: list[int]
    succs: list[int]
    params: list[ParamOut]


class InputSpecOut(Wire):
    layer_id: int
    kind: str
    lb: list[WireNumber]
    ub: list[WireNumber]


class OutputSpecOut(Wire):
    layer_id: int
    kind: str
    rows: int
    matrix: list[list[float]] | None
    thresholds: list[WireNumber] | None
    text: str


class ModelDescriptionOut(Wire):
    model_id: str
    sha256: str
    act_commit: str | None
    layers: list[LayerOut]
    input_specs: list[InputSpecOut]
    output_spec: OutputSpecOut | None
    input_dim: int
    output_dim: int


class FuzzOptions(Wire):
    """ACTFuzzer budget for method "fuzz"; other settings come from ACT's pipeline.yaml."""
    max_iterations: int = Field(default=100000, ge=1, le=1_000_000)
    rng_seed: int = Field(default=0, ge=0, le=2**31 - 1)
    stop_on_first: bool = False


class RunRequest(Wire):
    model_id: str = Field(min_length=1, max_length=64)
    method: Method
    time_budget_s: float = Field(default=30.0, gt=0, le=600)
    client_request_id: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    fuzz: FuzzOptions | None = None

    @model_validator(mode="after")
    def _fuzz_options_only_for_fuzz(self) -> "RunRequest":
        if self.fuzz is not None and self.method != "fuzz":
            raise ValueError("fuzz options are only valid with method 'fuzz'")
        return self


class RunResultOut(Wire):
    verdict: Verdict
    act_status: str
    elapsed_s: float
    metadata: dict[str, Scalar]
    counterexample: list[float] | None
    bab_summary: dict[str, Scalar] | None
    device: str | None = None  # torch device ACT computed on; None for runs recorded before it was captured


class RunOut(Wire):
    run_id: str
    model_id: str
    method: Method
    time_budget_s: float
    client_request_id: str | None
    status: RunState
    created_at: str
    started_at: str | None
    finished_at: str | None
    model_sha256: str
    act_commit: str | None
    result: RunResultOut | None
    error: ErrorBody | None
    native_reference: NativeResult | None
    matches_native: bool | None
    last_seq: int


class RunList(Wire):
    runs: list[RunOut]


class LayerStateOut(Wire):
    layer_id: int
    kind: str
    stage: Literal["after"]
    shape: list[int]
    lb: list[WireNumber]
    ub: list[WireNumber]
    before_layer_ids: list[int]


class LayerStatesOut(Wire):
    run_id: str
    availability: Availability
    method: Literal["interval"] | None
    layers: list[LayerStateOut]
    provenance: dict[str, str]


RunEventKind = Literal["run.queued", "run.started", "run.completed", "run.failed", "bab.summary", "fuzz.progress"]


class RunEvent(Wire):
    run_id: str
    seq: int
    kind: RunEventKind
    at: str
    status: RunState
    payload: dict[str, Scalar]


class CoverageOut(Wire):
    run_id: str
    node_events: Availability
    wave_events: Availability
    final_summary: Availability
    reason: str
    summary: dict[str, Scalar] | None


class FuzzPointOut(Wire):
    iteration: int
    elapsed_s: float
    coverage: float
    counterexamples: int
    corpus: int


class FuzzStrategyOut(Wire):
    name: str
    weight: float
    selected: int
    violations: int


class FuzzCounterexampleOut(Wire):
    index: int
    iteration: int
    elapsed_s: float
    strategy: str | None
    kind: str
    spec_row: int
    severity: WireNumber
    true_class: int | None
    input: list[WireNumber]
    output: list[WireNumber]
    seed_input: list[WireNumber]
    seed_output: list[WireNumber] | None = None  # absent in records written before it was captured


class FuzzSeedOut(Wire):
    row: int
    input: list[WireNumber]
    output: list[WireNumber]


class FuzzSummaryOut(Wire):
    act_status: str
    iterations: int
    elapsed_s: float
    neuron_coverage: float
    coverage_strategy: str
    seeds_explored: int
    total_mutations: int
    counterexample_count: int
    never_activated_count: int
    never_activated_sample: list[str]
    rng_seed: int
    device: str


class FuzzingOut(Wire):
    """ACTFuzzer record of a run. While running, timeline comes from committed fuzz.progress events."""
    run_id: str
    availability: Availability
    status: RunState
    options: FuzzOptions | None
    summary: FuzzSummaryOut | None
    timeline: list[FuzzPointOut]
    strategies: list[FuzzStrategyOut]
    counterexamples: list[FuzzCounterexampleOut]
    seeds: list[FuzzSeedOut] = []
    config: dict[str, Scalar]
    provenance: dict[str, str]


class SelectionContext(Wire):
    model_id: str
    run_id: str | None = None
    layer_id: int | None = None
    neuron: int | None = Field(default=None, ge=0)


class ExplainRequest(Wire):
    context: SelectionContext
    question: str = Field(min_length=1, max_length=2000)


EvidenceKind = Literal["layer_state", "run_result", "spec", "coverage"]


class EvidenceRef(Wire):
    ref_id: str
    kind: EvidenceKind
    label: str
    run_id: str | None
    layer_id: int | None
    neuron: int | None
    value: str


class AnswerSection(Wire):
    kind: Literal["observation", "interpretation", "hypothesis", "missing"]
    text: str
    evidence: list[str]


class ExplainResponse(Wire):
    answer_id: str
    provider: str
    provider_kind: Literal["fake", "real"]
    context: SelectionContext
    question: str
    sections: list[AnswerSection]
    evidence: list[EvidenceRef]


class ProviderOut(Wire):
    name: str
    kind: Literal["fake", "real"]
    availability: Literal["available", "not_configured"]
    note: str


class ProviderList(Wire):
    providers: list[ProviderOut]


class SolverLicenseUpload(Wire):
    """Text of a solver license file (e.g. gurobi.lic). Stored server-side; never returned."""
    content: str = Field(min_length=1, max_length=16384)


class SolverStatusOut(Wire):
    solver: Literal["gurobi"]
    version: str | None
    license_source: Literal["uploaded", "environment", "none"]
    license_fingerprint: str | None  # first 12 hex digits of the license file's sha256
    license_updated_at: str | None
    license_state: Literal["licensed", "restricted", "invalid", "not_installed"]
    message: str
    used_by_methods: list[Method]  # workbench methods whose ACT path calls this solver


WIRE_MODELS: tuple[type[BaseModel], ...] = (
    ErrorResponse, HealthOut, EngineInfoOut, ModelSummary, ModelDescriptionOut, RunRequest, RunOut, RunList,
    LayerStatesOut, RunEvent, CoverageOut, FuzzingOut, ExplainRequest, ExplainResponse, ProviderList, SolverLicenseUpload,
    SolverStatusOut,
)
