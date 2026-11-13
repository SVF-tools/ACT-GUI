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
# Input-sized vectors kept for display only (fuzz frames and seeds, a counterexample's seed) are omitted (None)
# above this many values, the largest image input in ACT's data (3x224x224); larger inputs such as the packed
# 1,268,224-value smart_turn_multimodal_2026 input would make records and responses hundreds of MB.
DISPLAY_VALUES = 3 * 224 * 224
# Dual alpha handling of verify_once: fixed slopes (one backward pass), Adam over alpha with the forward bounds
# kept fixed, or Adam over alpha recomputing the forward bounds from the current alpha every iteration.
DualAlpha = Literal["fixed", "optimize", "optimize_refresh"]


@dataclass(frozen=True)
class DualOptions:
    """DualSolver settings of a dual verify_once run. Defaults equal ACT's DualConfig; alpha "fixed" is ACT's
    verify_once default, so DualOptions() calls verify_once exactly as before (no extra ACT API needed)."""
    alpha: DualAlpha = "fixed"
    iterations: int = 50
    lr_alpha: float = 0.1
    lr_decay: float = 0.98
    per_class_alpha: bool = True
    stagnation_patience: int = 0
    stagnation_tol: float = 1e-5
    max_time_s: float = 0.0
    forward_lin_max_perturbed: int = 100


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
class ApiCheck:
    """One ACT symbol a capability's adapter calls, checked on the imported checkout."""
    capability: str
    symbol: str
    ok: bool
    detail: str


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
    api_checks: tuple[ApiCheck, ...] = ()

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


# Input provenance (capability source.provenance): what a VNN-LIB property was built from, copied out of ACT's
# provenance sidecar (act.pipeline.gui.provenance_gui). A point of the model input space (e.g. a counterexample)
# is never turned into text; it is only ranked against known examples (InputNeighbour).
@dataclass(frozen=True)
class ProvenanceTask:
    name: str
    title: str
    description: str
    class_names: tuple[str, ...]  # index = model output class
    dataset: str
    dataset_url: str | None


@dataclass(frozen=True)
class TextVariant:
    text: str
    kind: str  # perturbation that produced it, e.g. "char_swapping"
    kept: bool  # passed the benchmark's filter, so it helps span the property's box
    cosine: float | None


@dataclass(frozen=True)
class InputProvenance:
    benchmark: str
    key: str  # instance path relative to the benchmark directory
    modality: str
    representation: str
    task: ProvenanceTask
    family: str
    family_title: str
    family_index: int
    example_id: str | None
    text: str | None  # None when ACT matched no source example
    label: int | None
    split: str | None
    anchor: tuple[float, ...] | None  # the source example's point in the model input space
    variants: tuple[TextVariant, ...]
    variants_status: str  # replayed | partial | not_published | not_reproduced
    match_status: str  # verified | aligned | unmatched
    match_detail: str
    sources: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class InputNeighbour:
    example_id: str
    text: str
    label: int | None
    split: str | None
    distance: float  # Euclidean, in the model input space


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
    stage: Literal["after", "pre"]
    lb: tuple[float, ...]
    ub: tuple[float, ...]
    shape: tuple[int, ...]
    before_layer_ids: tuple[int, ...]  # the "before" state is the 'after' state of these preds


@dataclass(frozen=True)
class LayerStates:
    method: Domain
    availability: Availability
    layers: tuple[LayerState, ...]
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LaneOutcome:
    """ACT's verdict for one INPUT row of a batched net, with that row's counterexample when ACT reported one."""
    row: int
    verdict: Verdict
    act_status: str
    counterexample: tuple[float, ...] | None = None
    counterexample_output: tuple[float, ...] | None = None  # as RunOutcome.counterexample_output, for this row
    counterexample_output_error: str | None = None


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
    # Batched nets only: ACT's per-row verdicts; verdict/act_status then summarize them (see execution/verify.py).
    rows: tuple[LaneOutcome, ...] = ()
    counterexample_row: int | None = None  # the row `counterexample` belongs to (batched nets)
    # ACT's rebuilt model (ACTToTorch) evaluated at the counterexample, for export; the verdict stays ACT's.
    counterexample_output: tuple[float, ...] | None = None
    counterexample_output_error: str | None = None  # why counterexample_output could not be computed


@dataclass(frozen=True)
class FuzzOptionSpec:
    name: str
    kind: str
    live: bool
    description: str
    choices: tuple[str, ...]
    minimum: float | None
    maximum: float | None
    exclusive_minimum: bool
    default: object


@dataclass(frozen=True)
class BabOptionSpec:
    """One verify_bab_batched setting from ACT's bab_gui.bab_options (capability verify.bab.options)."""
    name: str  # a PipelineConfig.from_yaml override (bab_<field>, dual_<field>) or max_batch_size
    kind: str
    description: str
    choices: tuple[str, ...]
    minimum: float | None
    maximum: float | None
    exclusive_minimum: bool
    default: object
    group: str


@dataclass(frozen=True)
class FuzzControlChange:
    iteration: int
    requested: dict
    applied: dict
    rejected: str


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
    seed_input: tuple[float, ...] | None  # None above DISPLAY_VALUES values
    seed_output: tuple[float, ...]  # ACT model output on seed_input (the unmutated input)


@dataclass(frozen=True)
class FuzzSeed:
    """An initial seed (one INPUT row) and the ACT model's output on it."""
    row: int
    input: tuple[float, ...] | None  # None above DISPLAY_VALUES values
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
    input: tuple[float, ...] | None  # flattened mutated input that ACT ran through the model (None above DISPLAY_VALUES)
    seed_input: tuple[float, ...] | None  # flattened original INPUT row (FuzzingSeed.original_tensor), likewise
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
    stop_reason: str = "max_iterations"


# BaB search tree (EVT-02): ACT's committed BaB waves (act.pipeline.gui.bab_gui BaBWave / BaBTerminal), copied out
# of ACT. Node identity is ACT's node_id (the root is 0, its parent -1); a wave is ACT's commit point, so records of
# work ACT rolled back never arrive.
@dataclass(frozen=True)
class BabPhase:
    """A ReLU phase a split fixed: `neuron` of RELU layer `layer_id` is active (sign 1) or inactive (sign -1)."""
    layer_id: int
    neuron: int
    sign: int
    spec_rows: tuple[int, ...] = (0,)  # property rows the phase applies to (ACT keeps split signs per spec row)


@dataclass(frozen=True)
class BabInterval:
    """An input split: the child's new bounds on input `axis` (None when not finite)."""
    axis: int
    lb: float | None
    ub: float | None


@dataclass(frozen=True)
class BabBranch:
    """What distinguishes a child from its parent: ReLU phases (kind "neuron"), input intervals ("input_axis"),
    or "unknown" when ACT saw neither change."""
    kind: str
    phases: tuple[BabPhase, ...] = ()
    intervals: tuple[BabInterval, ...] = ()


@dataclass(frozen=True)
class BabLayerBounds:
    """One layer's bounds at a node, reduced from ACT's per-neuron bounds: their range and, for a RELU layer, how many
    of its inputs are stably active (lb >= 0), stably inactive (ub <= 0) or unstable (lb < 0 < ub)."""
    layer_id: int
    kind: str | None  # ACT layer kind, None when the model description lacks the layer
    neurons: int
    lb_min: float | None  # None when not finite
    ub_max: float | None
    active: int | None = None  # RELU layers only, from the bounds of the layer's input
    inactive: int | None = None
    unstable: int | None = None


@dataclass(frozen=True)
class BabNodeResult:
    """A node ACT solved in a wave and what ACT decided for it."""
    node_id: int
    parent_id: int  # -1 for the root
    depth: int
    solve_status: str  # ACT SolveStatus of the node's bound problem
    # ACT's outcome: proved_main | proved_terminal | branched | retired_max_depth | retired_terminal | unresolved
    outcome: str
    bound: float | None  # ACT's node bound (see bound_kind); None when not finite
    bound_kind: str
    layers: tuple[BabLayerBounds, ...] = ()  # empty when ACT reported no per-layer bounds (e.g. solver tier lp)


@dataclass(frozen=True)
class BabChild:
    """A subproblem ACT created in a wave by splitting `parent_id`."""
    node_id: int
    parent_id: int
    depth: int
    branch: BabBranch
    frontier_state: str  # "pending" (queued) or "evicted" (dropped by the frontier cap)


@dataclass(frozen=True)
class BabWave:
    """One committed BaB wave: the nodes ACT solved and the children it queued."""
    seq: int
    wave: int
    t_ms: float  # since the observed run started
    nodes: tuple[BabNodeResult, ...]
    children: tuple[BabChild, ...]
    frontier_size: int  # pending subproblems after the wave
    evicted_node_ids: tuple[int, ...]  # pending nodes the frontier cap dropped during the wave


@dataclass(frozen=True)
class BabTerminal:
    """ACT's end of the search: its verdict and reason, and the node that decided it when one did."""
    seq: int
    wave: int  # 0 when the root presolve decided
    t_ms: float
    status: str  # ACT VerifyStatus name
    reason: str
    frontier_size: int
    node_id: int | None = None  # e.g. the node whose counterexample falsified the property
    parent_id: int | None = None
    depth: int | None = None


LicenseState = Literal["licensed", "restricted", "invalid", "not_installed"]


@dataclass(frozen=True)
class SolverStatus:
    """Result of starting the solver's own license check; not a claim that any method uses it."""
    solver: Literal["gurobi"]
    version: str | None
    license_state: LicenseState
    message: str  # the solver's own license/error lines (credential values are never included)
