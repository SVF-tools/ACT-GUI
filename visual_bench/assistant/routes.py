"""HTTP routes of the assistant module: provider list and evidence-based explanations."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from visual_bench.assistant import schemas as S
from visual_bench.assistant.explain import explain, providers

if TYPE_CHECKING:
    from visual_bench.workbench import Workbench


def router(wb: "Workbench") -> APIRouter:
    r = APIRouter(prefix="/api/assistant", tags=["assistant"])

    @r.get("/providers", response_model=S.ProviderList)
    def assistant_providers() -> S.ProviderList:
        return providers()

    @r.post("/explain", response_model=S.ExplainResponse)
    def assistant_explain(req: S.ExplainRequest) -> S.ExplainResponse:
        return explain(wb, req)

    return r
