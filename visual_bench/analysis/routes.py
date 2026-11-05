"""HTTP routes of the analysis module: per-layer bounds of a run."""
from __future__ import annotations

from fastapi import APIRouter, Query

from visual_bench.analysis import schemas as S
from visual_bench.analysis.service import AnalysisService


def router(analysis: AnalysisService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["analysis"])

    @r.get("/runs/{run_id}/layers", response_model=S.LayerStatesOut)
    def layers(run_id: str) -> S.LayerStatesOut:
        return analysis.layer_states(run_id)

    @r.get("/runs/{run_id}/propagation", response_model=S.PropagationIndexOut)
    def propagation(run_id: str) -> S.PropagationIndexOut:
        return analysis.propagation(run_id)

    @r.get("/runs/{run_id}/propagation/layers/{layer_id}", response_model=S.PropagationLayerOut)
    def propagation_layer(run_id: str, layer_id: int, scope: str = "root",
                          pass_: str | None = None, stage: str | None = None,
                          version: int | None = Query(default=None, ge=0),
                          fields: str | None = Query(default=None, description="comma-separated tensor names"),
                          neuron: int | None = Query(default=None, ge=0)) -> S.PropagationLayerOut:
        names = [f for f in fields.split(",") if f] if fields else None
        return analysis.propagation_layer(run_id, layer_id, scope, pass_, stage, version, names, neuron)

    return r
