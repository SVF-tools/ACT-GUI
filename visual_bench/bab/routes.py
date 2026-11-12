"""HTTP routes of the bab module: BaB observation coverage and the search tree of a run."""
from __future__ import annotations

from fastapi import APIRouter, Query

from visual_bench.bab import schemas as S
from visual_bench.bab.service import BabService


def router(bab: BabService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["bab"])

    @r.get("/runs/{run_id}/coverage", response_model=S.CoverageOut)
    def coverage(run_id: str) -> S.CoverageOut:
        return bab.coverage(run_id)

    @r.get("/runs/{run_id}/bab", response_model=S.BabTreeOut)
    def tree(run_id: str, root: int = Query(default=0, ge=0),
             limit: int = Query(default=2000, ge=1, le=20000)) -> S.BabTreeOut:
        return bab.tree(run_id, root, limit)

    @r.get("/runs/{run_id}/bab/nodes/{node_id}", response_model=S.BabNodeDetailOut)
    def node(run_id: str, node_id: int) -> S.BabNodeDetailOut:
        return bab.node(run_id, node_id)

    return r
