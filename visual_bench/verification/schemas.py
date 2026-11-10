"""Run lifecycle payloads: requests, run state, results, and SSE run events (/api/runs)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from visual_bench.wire import Scalar, Verdict, Method, Domain, RunState, Wire, ErrorBody
from visual_bench.model_spec.schemas import NativeResult
from visual_bench.fuzzing.schemas import FuzzConfigChangeOut, FuzzOptions
from visual_bench.analysis.schemas import PropagationRecordOut

__all__ = ['DualOptions', 'HybridzOptions', 'VerifyDefaults', 'RunRequest', 'RowVerdictOut', 'RunResultOut', 'RunDiagnosticsOut', 'RunOut', 'RunList', 'RunEventKind', 'RunEvent']


class DualOptions(Wire):
    """DualSolver settings of a dual-domain verify_once run. Defaults equal ACT's DualConfig (drift-checked in
    test_verification.py); with every default the run calls verify_once exactly as without options."""
    # fixed: fixed ReLU slopes, one backward pass (ACT's verify_once default); optimize: Adam over alpha with the
    # forward bounds kept fixed; optimize_refresh: Adam over alpha, recomputing the forward bounds every iteration.
    alpha: Literal["fixed", "optimize", "optimize_refresh"] = "fixed"
    iterations: int = Field(default=50, ge=1, le=10_000)
    lr_alpha: float = Field(default=0.1, gt=0, le=10)
    lr_decay: float = Field(default=0.98, gt=0, le=1)
    per_class_alpha: bool = True
    stagnation_patience: int = Field(default=0, ge=0, le=10_000)  # 0 disables the stagnation stop
    stagnation_tol: float = Field(default=1e-5, ge=0, le=1)
    max_time_s: float = Field(default=0.0, ge=0, le=600)  # 0 disables the optimization time limit
    forward_lin_max_perturbed: int = Field(default=100, ge=0, le=1_000_000)

class HybridzOptions(Wire):
    """HybridZ verdict-solver settings of a hybridz-domain verify_once run; its time limit is the run budget."""
    tolerance: float = Field(default=1e-7, gt=0, le=1e-2)

class VerifyDefaults(Wire):
    """GET /api/verification/defaults: the settings a verify_once run uses when the request leaves them out."""
    dual: DualOptions
    hybridz: HybridzOptions

class RunRequest(Wire):
    model_id: str = Field(min_length=1, max_length=64)
    method: Method
    time_budget_s: float = Field(default=30.0, gt=0, le=600)
    client_request_id: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    fuzz: FuzzOptions | None = None
    domain: Domain | None = None  # method "interval" only; the service defaults it to "interval"
    dual: DualOptions | None = None  # domain "dual" only; the service fills in the defaults
    hybridz: HybridzOptions | None = None  # domain "hybridz" only; the service fills in the defaults

    @model_validator(mode="after")
    def _options_match_method(self) -> "RunRequest":
        if self.fuzz is not None and self.method != "fuzz":
            raise ValueError("fuzz options are only valid with method 'fuzz'")
        if self.domain is not None and self.method != "interval":
            raise ValueError("domain is only valid with method 'interval'")
        if self.dual is not None and self.domain != "dual":
            raise ValueError("dual options are only valid with domain 'dual'")
        if self.hybridz is not None and self.domain != "hybridz":
            raise ValueError("hybridz options are only valid with domain 'hybridz'")
        return self

class RowVerdictOut(Wire):
    row: int  # INPUT row of a batched net (one test image)
    verdict: Verdict
    act_status: str
    # This row's counterexample and the output for its VNN-COMP export (as RunResultOut); None for runs recorded before.
    counterexample: list[float] | None = None
    counterexample_output: list[float] | None = None
    counterexample_output_error: str | None = None

class RunResultOut(Wire):
    verdict: Verdict  # batched nets: the conjunction of the row verdicts below
    act_status: str
    elapsed_s: float
    metadata: dict[str, Scalar]
    counterexample: list[float] | None
    bab_summary: dict[str, Scalar] | None
    device: str | None = None  # torch device ACT computed on; None for runs recorded before it was captured
    rows: list[RowVerdictOut] = []  # ACT's per-row verdicts of a batched verify_once run; empty for single-row nets
    counterexample_row: int | None = None  # the batch row the counterexample belongs to
    # Output of ACT's rebuilt model (ACTToTorch) at the counterexample, for its VNN-COMP export; None with a reason.
    counterexample_output: list[float] | None = None
    counterexample_output_error: str | None = None

class RunDiagnosticsOut(Wire):
    """What the worker captured while driving ACT; its presence means GET /api/runs/{id}/snapshot has diagnostics."""
    # Python warnings, WARNING log records, ACT's printed [WARN] lines, and handled problems (e.g. no layer states)
    warnings: int
    errors: int  # ERROR/CRITICAL log records and ACT's printed [ERROR] lines
    messages: list[str] = []  # the first few warnings, for display
    exception: str | None  # root cause of a failed ACT call, "<type>: <message>"
    location: str | None  # innermost ACT frame of that exception (else the innermost frame), "<file>:<line> in <fn>"

class RunOut(Wire):
    run_id: str
    model_id: str
    method: Method
    domain: Domain | None  # abstract domain of a verify_once run; None for bab/fuzz
    dual: DualOptions | None = None  # settings of a dual run; None for other runs and for runs recorded before them
    hybridz: HybridzOptions | None = None  # settings of a hybridz run, likewise
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
    counterexample_saved_at: str | None = None  # when the user saved ACT's counterexample (verification runs)
    saved_counterexample_rows: list[int] = []  # batch rows whose counterexample the user saved (verification runs)
    diagnostics: RunDiagnosticsOut | None = None  # None for runs recorded before diagnostics were captured

class RunList(Wire):
    runs: list[RunOut]

RunEventKind = Literal["run.queued", "run.started", "run.stop_requested", "run.completed", "run.failed", "bab.summary",
                       "fuzz.progress", "fuzz.control", "fuzz.paused", "fuzz.resumed", "verify.propagation"]

class RunEvent(Wire):
    run_id: str
    seq: int
    kind: RunEventKind
    at: str
    status: RunState
    payload: dict[str, Scalar] | PropagationRecordOut | FuzzConfigChangeOut
