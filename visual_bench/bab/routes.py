"""HTTP routes of the bab module: BaB observation coverage of a run."""
from __future__ import annotations

from fastapi import APIRouter

from visual_bench.bab import schemas as S
from visual_bench.bab.service import BabService


def router(bab: BabService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["bab"])

    @r.get("/runs/{run_id}/coverage", response_model=S.CoverageOut)
    def coverage(run_id: str) -> S.CoverageOut:
        return bab.coverage(run_id)

    return r
