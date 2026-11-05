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
Method = Literal["interval", "bab", "fuzz"]
# Abstract domain of single-shot verification (method "interval", ACT verify_once):
# interval = IntervalTF bounds, dual = ACT DualSolver, hybridz = HybridzTF + HZSolver.
Domain = Literal["interval", "dual", "hybridz"]
DOMAINS: tuple[Domain, ...] = ("interval", "dual", "hybridz")


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
    shape: tuple[int, ...] = ()  # tensor shape of lb/ub as ACT stores it, e.g. (1, 3, 32, 32)
    center: tuple[float, ...] | None = None  # unperturbed input when the spec records one
    dataset: str | None = None  # INPUT layer dataset_name, e.g. "mnist", "cifar10"


@dataclass(frozen=True)
class OutputSpec:
    layer_id: int
    kind: str
    rows: int
    matrix: tuple[tuple[float, ...], ...] | None  # C, one row per constraint lane
    thresholds: tuple[float, ...] | None
    text: str  # human-readable rendering of what ACT checks
    true_class: int | None = None  # y_true of a TOP1/margin robustness assertion


@dataclass(frozen=True)
class VnnlibInstance:
    benchmark: str  # directory under ACT_ROOT/data/vnnlib
    onnx: str  # path relative to the benchmark directory, as listed in instances.csv
    vnnlib: str


@dataclass(frozen=True)
class ClassifierSource:
    source_id: str
    dataset: str  # "mnist" | "cifar10"
    onnx: str  # path relative to ACT_ROOT
    description: str


@dataclass(frozen=True)
class DatasetSample:
    dataset: str
    index: int
    size: int  # number of test images
    label: int
    shape: tuple[int, ...]  # C, H, W
    pixels: tuple[float, ...]  # CHW in [0, 1]


@dataclass(frozen=True)
class BuiltNet:
    """An ACT net written by a model source builder; params record how it was built."""
    description: str
    params: dict[str, str | int | float]
    input_rows: int = 1  # INPUT rows (one per batched image); decides the methods in execution.methods


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
    domain: Domain | None = None  # set for verify_once runs; None for BaB


@dataclass(frozen=True)
class FuzzProgress:
    """ACTFuzzer state after `iteration` samples (read between fuzzing iterations)."""
    iteration: int
    elapsed_s: float
    coverage: float  # ACT CoverageTracker value for the configured coverage strategy
    counterexamples: int  # counterexamples ACT's PropertyChecker has reported so far
    corpus: int  # seed corpus size


@dataclass(frozen=True)
class FuzzStrategyStats:
    name: str
    weight: float  # selection weight from ACT's fuzzing config
    selected: int  # fuzzing iterations (batches) that used this mutation strategy
    violations: int  # counterexamples reported in those iterations


@dataclass(frozen=True)
class FuzzCounterexample:
    index: int  # discovery order
    iteration: int  # samples completed when ACT reported it
    elapsed_s: float
    strategy: str | None  # mutation strategy of the iteration that produced it
    kind: str  # OutputSpec kind ACT checked
    spec_row: int
    severity: float  # ACT's signed violation margin
    true_class: int | None
    input: tuple[float, ...]  # flattened; ACT checked it satisfies the input spec
    output: tuple[float, ...]
    seed_input: tuple[float, ...]
    seed_output: tuple[float, ...]  # ACT model output on seed_input (the unmutated input)


@dataclass(frozen=True)
class FuzzSeed:
    """An initial seed (one INPUT row) and the ACT model's output on it."""
    row: int
    input: tuple[float, ...]
    output: tuple[float, ...]


@dataclass(frozen=True)
class FuzzFrame:
    """Lane 0 of the batch ACTFuzzer mutated in one iteration, read after that iteration (display only)."""
    iteration: int
    elapsed_s: float
    strategy: str | None  # mutation strategy ACT selected for that batch
    seed_row: int  # INPUT row the mutated lane descends from (FuzzingSeed.original_index)
    depth: int  # mutations applied since that INPUT row, including this one
    violation: bool  # the iteration added a counterexample to ACT's list
    input: tuple[float, ...]  # flattened mutated input that ACT ran through the model
    seed_input: tuple[float, ...]  # flattened original INPUT row (FuzzingSeed.original_tensor)
    # Newest counterexample ACT reported in this iteration (violation only); it need not be lane 0.
    counterexample: FuzzCounterexample | None = None


@dataclass(frozen=True)
class FuzzOutcome:
    """ACTFuzzer report. Fuzzing can falsify (a concrete counterexample) but never certify."""
    verdict: Verdict  # "falsified" iff ACT reported a counterexample, otherwise "unknown"
    act_status: str  # "COUNTEREXAMPLE_FOUND" or "NO_COUNTEREXAMPLE"
    iterations: int
    elapsed_s: float
    neuron_coverage: float
    coverage_strategy: str
    seeds_explored: int
    total_mutations: int
    counterexample_count: int
    never_activated_count: int
    never_activated_sample: tuple[str, ...]  # "layer[index]"
    counterexamples: tuple[FuzzCounterexample, ...]  # first ones in discovery order (capped)
    seeds: tuple[FuzzSeed, ...]  # initial seeds (capped)
    frames: tuple[FuzzFrame, ...]  # mutated inputs sampled over the run (capped, evenly thinned)
    timeline: tuple[FuzzProgress, ...]
    strategies: tuple[FuzzStrategyStats, ...]
    config: dict[str, object]  # effective ACT FuzzingConfig scalars
    rng_seed: int
    device: str
    stopped: bool = False  # ended early on a caller stop request; the report covers the iterations run


LicenseState = Literal["licensed", "restricted", "invalid", "not_installed"]


@dataclass(frozen=True)
class SolverStatus:
    """Result of starting the solver's own license check; not a claim that any method uses it."""
    solver: Literal["gurobi"]
    version: str | None
    license_state: LicenseState
    message: str  # the solver's own license/error lines (credential values are never included)
