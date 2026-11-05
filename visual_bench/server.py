"""Thin FastAPI composition root for the workbench service.

Builds the Workbench services, renders AppError/validation errors as ErrorResponse, includes
each module's router (<module>/routes.py), and serves the production browser build.
Development: scripts/dev.sh runs this on 127.0.0.1:18765 behind the Vite dev server
(http://127.0.0.1:5173).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from visual_bench import config
from visual_bench.analysis import routes as analysis_routes
from visual_bench.assistant import routes as assistant_routes
from visual_bench.bab import routes as bab_routes
from visual_bench.engine import routes as engine_routes
from visual_bench.errors import AppError
from visual_bench.fuzzing import routes as fuzzing_routes
from visual_bench.model_spec import routes as model_spec_routes
from visual_bench.records import routes as records_routes
from visual_bench.verification import routes as verification_routes
from visual_bench.wire import ErrorBody, ErrorResponse, HealthOut
from visual_bench.workbench import Workbench

VERSION = "0.1.0"


def create_app(records_root: Path | None = None, secrets_root: Path | None = None) -> FastAPI:
    wb = Workbench(records_root or config.records_root(), secrets_root=secrets_root)
    app = FastAPI(title="ACT-GUI workbench", version=VERSION)
    app.state.workbench = wb

    @app.exception_handler(AppError)
    async def _app_error(_: Request, err: AppError) -> JSONResponse:
        body = ErrorResponse(error=ErrorBody(code=err.code, message=err.message, retryable=err.retryable))
        return JSONResponse(body.model_dump(), status_code=err.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, err: RequestValidationError) -> JSONResponse:
        msg = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in err.errors())
        return JSONResponse(ErrorResponse(error=ErrorBody(code="invalid_request", message=msg)).model_dump(),
                            status_code=422)

    @app.get("/api/health", response_model=HealthOut)
    def health() -> HealthOut:
        return HealthOut(status="ok", service="act-gui-workbench", version=VERSION)

    app.include_router(engine_routes.router(wb.engine))
    app.include_router(model_spec_routes.router(wb.models))
    app.include_router(verification_routes.router(wb.runs))
    app.include_router(fuzzing_routes.router(wb.fuzzing))
    app.include_router(analysis_routes.router(wb.analysis))
    app.include_router(bab_routes.router(wb.bab))
    app.include_router(records_routes.router(wb.records))
    app.include_router(assistant_routes.router(wb))

    if config.WEB_DIST.is_dir():  # production build served from the same origin (npm run build)
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=config.WEB_DIST, html=True), name="web")
    return app


app = create_app()
