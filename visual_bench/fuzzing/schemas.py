"""ACTFuzzer options and fuzzing record payloads (/api/fuzz/defaults, /api/runs/{id}/fuzzing, saved counterexamples)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from visual_bench.wire import WireNumber, Scalar, Availability, RunState, Wire

__all__ = ['FuzzMutationWeights', 'FuzzOptions', 'FuzzPointOut', 'FuzzStrategyOut', 'FuzzCounterexampleOut', 'FuzzSeedOut', 'FuzzSummaryOut', 'FuzzFrameOut', 'SavedCounterexampleOut', 'SaveCounterexampleRequest', 'FuzzingOut']


class FuzzMutationWeights(Wire):
    """Relative selection weights of ACT's mutation operators (ACT normalizes them; 0 disables one)."""
    gradient: float = Field(default=0.0, ge=0, le=1000)
    pgd: float = Field(default=0.4, ge=0, le=1000)
    activation: float = Field(default=0.3, ge=0, le=1000)
    boundary: float = Field(default=0.2, ge=0, le=1000)
    random: float = Field(default=0.1, ge=0, le=1000)

    @model_validator(mode="after")
    def _some_operator_enabled(self) -> "FuzzMutationWeights":
        if self.gradient + self.pgd + self.activation + self.boundary + self.random <= 0:
            raise ValueError("mutation weights must sum to > 0")
        return self

class FuzzOptions(Wire):
    """ACTFuzzer settings for method "fuzz". Defaults other than max_iterations equal the fuzzing section of
    the pinned ACT act/config/pipeline.yaml (drift-checked in fuzzing/test_fuzzing.py); the browser reads them from
    GET /api/fuzz/defaults. Output, tracing and reporting stay owned by engine_bridge."""
    max_iterations: int = Field(default=100000, ge=1, le=1_000_000)
    rng_seed: int = Field(default=0, ge=0, le=2**31 - 1)
    stop_on_first: bool = False
    coverage_strategy: Literal["GlobalCov", "BestInputCov"] = "GlobalCov"
    activation_threshold: float = Field(default=0.0001, ge=0, le=1000)
    mutation_weights: FuzzMutationWeights = Field(default_factory=FuzzMutationWeights)
    perturb_mode: Literal["adaptive_scalar", "adaptive_perdim", "fixed"] = "adaptive_scalar"
    perturb_scale: float = Field(default=0.1, gt=0, le=1)
    seed_selection_strategy: Literal["energy", "random"] = "energy"
    pgd_restarts: int = Field(default=1, ge=1, le=100)
    pgd_restarts_binarized: int = Field(default=40, ge=1, le=200)

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
    stopped: bool = False  # ended early on a user stop request

class FuzzFrameOut(Wire):
    """Lane 0 of the batch ACTFuzzer mutated in one iteration. Display only; not a counterexample unless violation."""
    iteration: int
    elapsed_s: float
    strategy: str | None
    seed_row: int
    depth: int
    violation: bool
    input: list[WireNumber]
    seed_input: list[WireNumber]
    counterexample: FuzzCounterexampleOut | None = None  # ACT's newest counterexample of a violating iteration

class SavedCounterexampleOut(Wire):
    """An ACT counterexample the user saved on its run record (user annotation; ACT decided the violation)."""
    saved_at: str
    counterexample: FuzzCounterexampleOut

class SaveCounterexampleRequest(Wire):
    index: int = Field(ge=0)  # ACT discovery index (FuzzCounterexampleOut.index)

class FuzzingOut(Wire):
    """ACTFuzzer record of a run. While running, timeline comes from committed fuzz.progress events
    and frames holds only the latest mutated input the worker reported (kept in memory, not recorded)."""
    run_id: str
    availability: Availability
    status: RunState
    options: FuzzOptions | None
    summary: FuzzSummaryOut | None
    timeline: list[FuzzPointOut]
    strategies: list[FuzzStrategyOut]
    counterexamples: list[FuzzCounterexampleOut]
    seeds: list[FuzzSeedOut] = []
    frames: list[FuzzFrameOut] = []  # recorded filmstrip when completed; [latest] while running
    saved: list[SavedCounterexampleOut] = []  # counterexamples the user saved, in save order
    config: dict[str, Scalar]
    provenance: dict[str, str]
