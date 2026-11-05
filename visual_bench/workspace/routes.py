"""HTTP routes of the workspace module: POST /api/presence (heartbeat in, online count out)."""
from __future__ import annotations

from fastapi import APIRouter

from visual_bench.workspace.schemas import PresenceHeartbeat, PresenceOut
from visual_bench.workspace.service import PresenceService


def router(presence: PresenceService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["workspace"])

    @r.post("/presence", response_model=PresenceOut)
    def heartbeat(body: PresenceHeartbeat) -> PresenceOut:
        return PresenceOut(online=presence.beat(body.client_id), window_s=presence.window_s)

    return r
