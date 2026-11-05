"""Run lifecycle payloads: requests, run state, results, and SSE run events (/api/runs)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from visual_bench.wire import Scalar, Verdict, Method, Domain, RunState, Wire, ErrorBody
from visual_bench.model_spec.schemas import NativeResult
from visual_bench.fuzzing.schemas import FuzzOptions

__all__ = ['RunRequest', 'RowVerdictOut', 'RunResultOut', 'RunOut', 'RunList', 'RunEventKind', 'RunEvent']


class RunRequest(Wire):
    model_id: str = Field(min_length=1, max_length=64)
    method: Method
    time_budget_s: float = Field(default=30.0, gt=0, le=600)
    client_request_id: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    fuzz: FuzzOptions | None = None
    domain: Domain | None = None  # method "interval" only; the service defaults it to "interval"

    @model_validator(mode="after")
    def _options_match_method(self) -> "RunRequest":
        if self.fuzz is not None and self.method != "fuzz":
            raise ValueError("fuzz options are only valid with method 'fuzz'")
        if self.domain is not None and self.method != "interval":
            raise ValueError("domain is only valid with method 'interval'")
        return self

class RowVerdictOut(Wire):
    row: int  # INPUT row of a batched net (one test image)
    verdict: Verdict
    act_status: str

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

class RunOut(Wire):
    run_id: str
    model_id: str
    method: Method
    domain: Domain | None  # abstract domain of a verify_once run; None for bab/fuzz
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

class RunList(Wire):
    runs: list[RunOut]

RunEventKind = Literal["run.queued", "run.started", "run.stop_requested", "run.completed", "run.failed", "bab.summary",
                       "fuzz.progress"]

class RunEvent(Wire):
    run_id: str
    seq: int
    kind: RunEventKind
    at: str
    status: RunState
    payload: dict[str, Scalar]
