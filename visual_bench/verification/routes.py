"""HTTP routes of the verification module: start, list, read, and stop runs; follow run events over SSE."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from visual_bench.verification import schemas as S
from visual_bench.verification.service import RunService


def router(runs: RunService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["verification"])

    @r.get("/verification/defaults", response_model=S.VerifyDefaults)
    def verification_defaults() -> S.VerifyDefaults:
        return runs.defaults()

    @r.get("/verification/bab-options", response_model=S.BabOptionsOut)
    def bab_options() -> S.BabOptionsOut:
        return runs.bab_options()

    @r.post("/runs", response_model=S.RunOut, status_code=202)
    def start_run(req: S.RunRequest) -> JSONResponse:
        run, created = runs.start(req)
        return JSONResponse(run.model_dump(), status_code=202 if created else 200)

    @r.get("/runs", response_model=S.RunList)
    def list_runs() -> S.RunList:
        return runs.list()

    @r.get("/runs/{run_id}", response_model=S.RunOut)
    def get_run(run_id: str) -> S.RunOut:
        return runs.get(run_id)

    @r.post("/runs/{run_id}/stop", response_model=S.RunOut)
    def stop_run(run_id: str) -> S.RunOut:
        return runs.stop(run_id)

    @r.post("/runs/{run_id}/saved-counterexample", response_model=S.RunOut, status_code=201)
    def save_counterexample(run_id: str, row: int | None = None) -> JSONResponse:
        """Save ACT's counterexample of batch row `row` (default: the run's summary counterexample)."""
        run, created = runs.save_counterexample(run_id, row)
        return JSONResponse(run.model_dump(), status_code=201 if created else 200)

    @r.get("/runs/{run_id}/saved-counterexample/vnnlib")
    def saved_counterexample_file(run_id: str, row: int | None = None) -> Response:
        name = f"{run_id}-ce.counterexample" if row is None else f"{run_id}-row{row}-ce.counterexample"
        return Response(runs.saved_counterexample_file(run_id, row), media_type="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @r.get("/runs/{run_id}/snapshot")
    def snapshot(run_id: str) -> Response:
        return Response(runs.snapshot(run_id), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{run_id}-snapshot.zip"'})

    @r.get("/runs/{run_id}/events")
    async def events(run_id: str, request: Request, after: int = 0) -> StreamingResponse:
        """SSE: replay committed events after seq 'after' (or Last-Event-ID), then follow until terminal."""
        runs.get(run_id)  # 404 before streaming
        start = int(request.headers.get("last-event-id", after))

        async def stream():
            seq = start
            while True:
                evs = await asyncio.to_thread(runs.records.wait_for_events, run_id, seq, 15.0)
                if not evs:
                    yield ": keep-alive\n\n"
                for ev in evs:
                    seq = ev["seq"]
                    payload = S.RunEvent.model_validate(ev).model_dump_json()
                    yield f"id: {seq}\nevent: run\ndata: {payload}\n\n"
                if evs and evs[-1]["status"] in ("completed", "failed") and evs[-1]["kind"].startswith("run."):
                    yield "event: end\ndata: {}\n\n"
                    return
                if await request.is_disconnected():
                    return

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return r
