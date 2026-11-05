"""HTTP routes of the engine module: ACT engine status and the Gurobi license."""
from __future__ import annotations

from fastapi import APIRouter

from visual_bench.engine import schemas as S
from visual_bench.engine.service import EngineService
from visual_bench.engine.solver_license import LicenseRejected
from visual_bench.errors import AppError


def router(engine: EngineService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["engine"])

    @r.get("/engine", response_model=S.EngineInfoOut)
    def engine_info() -> S.EngineInfoOut:
        return engine.engine_out()

    @r.get("/solvers/gurobi", response_model=S.SolverStatusOut)
    def gurobi_status() -> S.SolverStatusOut:
        return engine.gurobi.status()

    @r.put("/solvers/gurobi/license", response_model=S.SolverStatusOut)
    def gurobi_upload(req: S.SolverLicenseUpload) -> S.SolverStatusOut:
        try:
            return engine.gurobi.upload(req.content)
        except LicenseRejected as err:
            raise AppError(422, "invalid_license_file", str(err))

    @r.delete("/solvers/gurobi/license", response_model=S.SolverStatusOut)
    def gurobi_remove() -> S.SolverStatusOut:
        return engine.gurobi.remove()

    return r
