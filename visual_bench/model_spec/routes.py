"""HTTP routes of the model_spec module: model catalog, model sources, and model descriptions."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from visual_bench.model_spec import schemas as S
from visual_bench.model_spec.service import ModelService


def router(models: ModelService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["model_spec"])

    @r.get("/models", response_model=list[S.ModelSummary])
    def list_models() -> list[S.ModelSummary]:
        return models.models()

    @r.post("/models", response_model=S.ModelSummary, status_code=201)
    def load_model(body: S.LoadModelBody) -> JSONResponse:
        summary, created = models.load(body.source)
        return JSONResponse(summary.model_dump(), status_code=201 if created else 200)

    @r.post("/models/{model_id}/rebuild", response_model=S.ModelSummary, status_code=201)
    def rebuild_model(model_id: str) -> JSONResponse:
        summary, created = models.rebuild(model_id)
        return JSONResponse(summary.model_dump(), status_code=201 if created else 200)

    @r.get("/sources", response_model=S.SourcesOut)
    def sources() -> S.SourcesOut:
        return models.sources()

    @r.get("/sources/sample", response_model=S.SampleOut)
    def sample(dataset: str, index: int) -> S.SampleOut:
        return models.sample(dataset, index)

    @r.get("/models/{model_id}", response_model=S.ModelDescriptionOut)
    def describe(model_id: str) -> S.ModelDescriptionOut:
        return models.describe(model_id)

    return r
