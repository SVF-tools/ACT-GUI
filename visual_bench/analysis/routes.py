"""HTTP routes of the analysis module: per-layer bounds of a run."""
from __future__ import annotations

from fastapi import APIRouter

from visual_bench.analysis import schemas as S
from visual_bench.analysis.service import AnalysisService


def router(analysis: AnalysisService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["analysis"])

    @r.get("/runs/{run_id}/layers", response_model=S.LayerStatesOut)
    def layers(run_id: str) -> S.LayerStatesOut:
        return analysis.layer_states(run_id)

    return r
