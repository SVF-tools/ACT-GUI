"""BaB payloads: observation coverage (/api/runs/{id}/coverage) and the search tree (/api/runs/{id}/bab)."""
from __future__ import annotations

from typing import Literal

from visual_bench.wire import Availability, RunState, Scalar, Wire, WireNumber

__all__ = ['CoverageOut', 'BabNodeState', 'BabPhaseOut', 'BabIntervalOut', 'BabBranchOut', 'BabNodeOut', 'BabLayerOut',
           'BabWaveOut', 'BabTerminalOut', 'BabSharesOut', 'BabTreeOut', 'BabNodeDetailOut']


class CoverageOut(Wire):
    run_id: str
    node_events: Availability
    wave_events: Availability
    final_summary: Availability
    reason: str
    summary: dict[str, Scalar] | None


# Display state from ACT's records only: pending (queued in the frontier), branched (split into children), proved
# (ACT proved its subproblem), falsified (ACT's counterexample came from it), retired (dropped unproven at the depth
# limit or by the terminal LP), evicted (dropped by the frontier cap), unresolved (solved, neither proved nor split).
BabNodeState = Literal["pending", "branched", "proved", "falsified", "retired", "evicted", "unresolved"]


class BabPhaseOut(Wire):
    layer_id: int  # RELU layer
    neuron: int
    sign: int  # 1: the ReLU input is fixed active (>= 0); -1: inactive (<= 0)
    spec_rows: list[int]  # property rows the phase applies to


class BabIntervalOut(Wire):
    axis: int  # index into the flattened input
    lb: WireNumber | None
    ub: WireNumber | None


class BabBranchOut(Wire):
    kind: str  # "neuron" (ReLU phases), "input_axis" (input intervals) or "unknown"
    phases: list[BabPhaseOut] = []
    intervals: list[BabIntervalOut] = []


class BabNodeOut(Wire):
    node_id: int  # ACT's node id; the root is 0
    parent_id: int  # -1 for the root
    depth: int
    state: BabNodeState
    outcome: str | None  # ACT's outcome once the node was solved
    created_wave: int  # 0 for the root
    solved_wave: int | None
    evicted_wave: int | None
    bound: WireNumber | None  # ACT's bound of the node's subproblem once solved
    branch: BabBranchOut | None  # the split that created the node; None for the root
    children: int
    descendants: int
    hidden_children: int = 0  # children beyond this response's node budget


class BabLayerOut(Wire):
    layer_id: int
    kind: str | None
    neurons: int
    lb_min: WireNumber | None
    ub_max: WireNumber | None
    active: int | None = None  # RELU layers: inputs with lb >= 0
    inactive: int | None = None  # inputs with ub <= 0
    unstable: int | None = None  # inputs with lb < 0 < ub


class BabWaveOut(Wire):
    wave: int
    seq: int
    t_ms: float  # since the observed run started
    solved: int
    created: int
    proved: int
    branched: int
    retired: int
    unresolved: int
    evicted: int
    frontier_size: int  # pending subproblems after the wave
    min_bound: WireNumber | None  # lowest ACT bound among the nodes solved in the wave


class BabTerminalOut(Wire):
    seq: int
    wave: int  # 0 when the root presolve decided; a counterexample ends the search inside a wave
    t_ms: float
    status: str  # ACT VerifyStatus name
    reason: str
    frontier_size: int
    node_id: int | None  # the node that decided the search, when one did


class BabSharesOut(Wire):
    """The focused subtree as fractions per leaf state (they sum to 1), each node's share split equally among its
    children: a measure of the split tree, not of input volume, and never a verdict."""
    proved: float
    falsified: float
    pending: float
    evicted: float
    retired: float
    unresolved: float


class BabTreeOut(Wire):
    run_id: str
    status: RunState
    availability: Availability
    reason: str
    complete: bool  # ACT's terminal record is in the log
    root: int  # the focused subtree's root
    path: list[BabNodeOut]  # ancestors of root, from the tree root down
    nodes: list[BabNodeOut]  # breadth-first from root, at most limit
    limit: int
    truncated: bool
    counts: dict[str, int]  # whole tree: "nodes", "solved", and one count per BabNodeState
    shares: BabSharesOut | None
    waves: list[BabWaveOut]
    terminal: BabTerminalOut | None
    ignored_records: int = 0  # ACT records the bridge could not read
    recording_error: str | None = None  # why recording stopped early; ACT's result is unaffected


class BabNodeDetailOut(Wire):
    run_id: str
    node: BabNodeOut
    solve_status: str | None  # ACT SolveStatus of the node's bound problem
    bound_kind: str | None
    layers: list[BabLayerOut]  # empty until solved, or when ACT reported no per-layer bounds
    path: list[BabNodeOut]  # ancestors, from the tree root down
    children: list[BabNodeOut]
