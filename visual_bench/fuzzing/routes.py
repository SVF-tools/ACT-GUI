"""HTTP routes of the fuzzing module: fuzz defaults, fuzzing records, and saved counterexamples."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from visual_bench.fuzzing import schemas as S
from visual_bench.fuzzing.service import FuzzingService


def router(fuzzing: FuzzingService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["fuzzing"])

    @r.get("/fuzz/defaults", response_model=S.FuzzOptions)
    def fuzz_defaults() -> S.FuzzOptions:
        return fuzzing.defaults()

    @r.get("/runs/{run_id}/fuzzing", response_model=S.FuzzingOut)
    def fuzzing_record(run_id: str) -> S.FuzzingOut:
        return fuzzing.fuzzing(run_id)

    @r.post("/runs/{run_id}/saved-counterexamples", response_model=S.SavedCounterexampleOut, status_code=201)
    def save_counterexample(run_id: str, req: S.SaveCounterexampleRequest) -> JSONResponse:
        saved, created = fuzzing.save_counterexample(run_id, req.index)
        return JSONResponse(saved.model_dump(), status_code=201 if created else 200)

    @r.get("/runs/{run_id}/saved-counterexamples/{index}/vnnlib")
    def saved_assignment(run_id: str, index: int) -> Response:
        return Response(fuzzing.saved_assignment(run_id, index), media_type="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{run_id}-ce{index}.counterexample"'})

    return r
