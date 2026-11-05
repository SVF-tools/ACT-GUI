"""Presence count: browsers are deduplicated by client id and expire after the window."""
from __future__ import annotations

from fastapi.testclient import TestClient

from visual_bench.workspace.service import PresenceService


def test_count_dedupes_browsers_and_expires_silent_ones():
    now = [1000.0]
    svc = PresenceService(window_s=90, clock=lambda: now[0])
    assert svc.beat("browser-a1") == 1
    assert svc.beat("browser-a1") == 1
    now[0] += 60
    assert svc.beat("browser-b2") == 2
    now[0] += 31  # a1 last seen 91 s ago
    assert svc.beat("browser-b2") == 1


def test_heartbeat_route_returns_count_and_rejects_bad_ids(client: TestClient):
    first = client.post("/api/presence", json={"client_id": "tab-0000001"})
    assert first.status_code == 200 and first.json() == {"online": 1, "window_s": 90}
    assert client.post("/api/presence", json={"client_id": "tab-0000002"}).json()["online"] == 2
    bad = client.post("/api/presence", json={"client_id": "<script>"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_request"
