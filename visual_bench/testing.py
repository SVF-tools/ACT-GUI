"""Helpers shared by the workbench HTTP tests (imported by <module>/test_*.py)."""
from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient


def follow_to_end(client: TestClient, run_id: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    with client.stream("GET", f"/api/runs/{run_id}/events") as resp:
        for line in resp.iter_lines():
            if line.startswith("data: ") and line != "data: {}":
                events.append(json.loads(line[6:]))
            if line == "event: end":
                break
    return events


def sources_or_skip(client: TestClient) -> dict[str, Any]:
    s = client.get("/api/sources").json()
    if not s["classifiers"] or not s["vnnlib"]:
        pytest.skip("ACT checkout has no classifier ONNX models or VNN-LIB benchmarks")
    return s
