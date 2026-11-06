"""Wire payloads of the presence heartbeat (WS-04)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PresenceHeartbeat(BaseModel):
    """One browser's heartbeat; client_id is a random id kept in that browser's localStorage."""

    client_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class CountryCount(BaseModel):
    country: str | None = Field(description="ISO 3166-1 alpha-2 from Cloudflare CF-IPCountry; null when unknown or local")
    count: int = Field(ge=1)


class PresenceOut(BaseModel):
    online: int = Field(ge=0, description="Browsers with a heartbeat inside the window")
    window_s: int = Field(gt=0, description="Seconds a heartbeat keeps a browser counted")
    countries: list[CountryCount] = Field(description="Online browsers per country, largest first")
