"""Thin FastAPI composition root for the workbench service.

Development: scripts/dev.sh runs this on 127.0.0.1:18765 behind the Vite dev
server (http://127.0.0.1:5173). Routes only map HTTP to application use cases.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, StreamingResponse

from visual_bench import schemas as S
from visual_bench.assistant.explain import explain, providers
from visual_bench.verification.service import REPO_ROOT, AppError, Workbench
from visual_bench.verification.solver_license import LicenseRejected

VERSION = "0.1.0"


def create_app(records_root: Path | None = None, secrets_root: Path | None = None) -> FastAPI:
    root = records_root or Path(os.environ.get("ACT_GUI_RECORDS", REPO_ROOT / "var" / "records"))
    secrets = secrets_root or (Path(os.environ["ACT_GUI_SECRETS"]) if os.environ.get("ACT_GUI_SECRETS") else None)
    wb = Workbench(root, secrets_root=secrets)
    app = FastAPI(title="ACT-GUI workbench", version=VERSION)
    app.state.workbench = wb

    @app.exception_handler(AppError)
    async def _app_error(_: Request, err: AppError) -> JSONResponse:
        body = S.ErrorResponse(error=S.ErrorBody(code=err.code, message=err.message, retryable=err.retryable))
        return JSONResponse(body.model_dump(), status_code=err.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, err: RequestValidationError) -> JSONResponse:
        msg = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in err.errors())
        return JSONResponse(S.ErrorResponse(error=S.ErrorBody(code="invalid_request", message=msg)).model_dump(),
                            status_code=422)

    @app.get("/api/health", response_model=S.HealthOut)
    def health() -> S.HealthOut:
        return S.HealthOut(status="ok", service="act-gui-workbench", version=VERSION)

    @app.get("/api/engine", response_model=S.EngineInfoOut)
    def engine() -> S.EngineInfoOut:
        return wb.engine_out()

    @app.get("/api/models", response_model=list[S.ModelSummary])
    def models() -> list[S.ModelSummary]:
        return wb.models()

    @app.get("/api/models/{model_id}", response_model=S.ModelDescriptionOut)
    def model(model_id: str) -> S.ModelDescriptionOut:
        return wb.describe(model_id)

    @app.post("/api/runs", response_model=S.RunOut, status_code=202)
    def start_run(req: S.RunRequest) -> JSONResponse:
        run, created = wb.start_run(req)
        return JSONResponse(run.model_dump(), status_code=202 if created else 200)

    @app.get("/api/runs", response_model=S.RunList)
    def runs() -> S.RunList:
        return wb.list_runs()

    @app.get("/api/runs/{run_id}", response_model=S.RunOut)
    def run(run_id: str) -> S.RunOut:
        return wb.get_run(run_id)

    @app.get("/api/runs/{run_id}/layers", response_model=S.LayerStatesOut)
    def layers(run_id: str) -> S.LayerStatesOut:
        return wb.layer_states(run_id)

    @app.get("/api/runs/{run_id}/coverage", response_model=S.CoverageOut)
    def coverage(run_id: str) -> S.CoverageOut:
        return wb.coverage(run_id)

    @app.get("/api/runs/{run_id}/events")
    async def events(run_id: str, request: Request, after: int = 0) -> StreamingResponse:
        """SSE: replay committed events after seq 'after' (or Last-Event-ID), then follow until terminal."""
        wb.get_run(run_id)  # 404 before streaming
        start = int(request.headers.get("last-event-id", after))

        async def stream():
            seq = start
            while True:
                evs = await asyncio.to_thread(wb.records.wait_for_events, run_id, seq, 15.0)
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

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str) -> Response:
        wb.get_run(run_id)
        try:
            data = wb.records.export_zip(run_id)
        except FileNotFoundError:
            raise AppError(409, "record_not_sealed", "Only completed, sealed runs can be exported")
        return Response(data, media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{run_id}.zip"'})

    @app.get("/api/solvers/gurobi", response_model=S.SolverStatusOut)
    def gurobi_status() -> S.SolverStatusOut:
        return wb.gurobi.status()

    @app.put("/api/solvers/gurobi/license", response_model=S.SolverStatusOut)
    def gurobi_upload(req: S.SolverLicenseUpload) -> S.SolverStatusOut:
        try:
            return wb.gurobi.upload(req.content)
        except LicenseRejected as err:
            raise AppError(422, "invalid_license_file", str(err))

    @app.delete("/api/solvers/gurobi/license", response_model=S.SolverStatusOut)
    def gurobi_remove() -> S.SolverStatusOut:
        return wb.gurobi.remove()

    @app.get("/api/assistant/providers", response_model=S.ProviderList)
    def assistant_providers() -> S.ProviderList:
        return providers()

    @app.post("/api/assistant/explain", response_model=S.ExplainResponse)
    def assistant_explain(req: S.ExplainRequest) -> S.ExplainResponse:
        return explain(wb, req)

    dist = REPO_ROOT / "dist" / "web"
    if dist.is_dir():  # production build served from the same origin (npm run build)
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=dist, html=True), name="web")
    return app


app = create_app()
