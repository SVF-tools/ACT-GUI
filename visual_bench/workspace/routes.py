"""HTTP routes of the workspace module: POST /api/presence (heartbeat in, online count out)."""
from __future__ import annotations

from fastapi import APIRouter, Header

from visual_bench.workspace.schemas import CountryCount, PresenceHeartbeat, PresenceOut
from visual_bench.workspace.service import PresenceService, normalize_country


def router(presence: PresenceService) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["workspace"])

    @r.post("/presence", response_model=PresenceOut)
    def heartbeat(body: PresenceHeartbeat, cf_ipcountry: str | None = Header(default=None)) -> PresenceOut:
        snap = presence.beat(body.client_id, normalize_country(cf_ipcountry))
        return PresenceOut(online=snap.online, window_s=presence.window_s,
                           countries=[CountryCount(country=c, count=n) for c, n in snap.countries])

    return r
