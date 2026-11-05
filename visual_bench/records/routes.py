"""HTTP routes of the records module: export a sealed run record as a zip bundle."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from visual_bench.errors import AppError
from visual_bench.records.store import RecordStore


def router(records: RecordStore) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["records"])

    @r.get("/runs/{run_id}/export")
    def export(run_id: str) -> Response:
        if not records.exists(run_id):
            raise AppError(404, "run_not_found", f"Unknown run {run_id!r}")
        try:
            data = records.export_zip(run_id)
        except FileNotFoundError:
            raise AppError(409, "record_not_sealed", "Only completed, sealed runs can be exported")
        return Response(data, media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{run_id}.zip"'})

    return r
