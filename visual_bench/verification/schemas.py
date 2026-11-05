"""Run lifecycle payloads: requests, run state, results, and SSE run events (/api/runs)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from visual_bench.wire import Scalar, Verdict, Method, Domain, RunState, Wire, ErrorBody
from visual_bench.model_spec.schemas import NativeResult
from visual_bench.fuzzing.schemas import FuzzOptions

__all__ = ['RunRequest', 'RunResultOut', 'RunOut', 'RunList', 'RunEventKind', 'RunEvent']


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
