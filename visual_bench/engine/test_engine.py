"""Engine and Gurobi license tests through the HTTP surface.

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from visual_bench.testing import follow_to_end


HOST_BOUND_LICENSE = "# test license\nTYPE=ACADEMIC\nVERSION=13\nHOSTID=deadbeef\nUSERNAME=nobody\nKEY=SECRETKEY123\n"

def test_gurobi_license_upload_is_private_checked_and_used_by_runs(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GRB_LICENSE_FILE", raising=False)
    before = client.get("/api/solvers/gurobi").json()
    assert before["license_source"] == "none" and before["used_by_methods"] == []
    if before["license_state"] == "not_installed":
        pytest.skip("gurobipy is not installed in this environment")

    up = client.put("/api/solvers/gurobi/license", json={"content": HOST_BOUND_LICENSE})
    assert up.status_code == 200
    status = up.json()
    assert status["license_source"] == "uploaded" and status["license_state"] == "invalid"
    assert "HostID mismatch" in status["message"] and "SECRETKEY123" not in up.text
    stored = tmp_path / "secrets" / "gurobi.lic"
    assert stored.read_text() == HOST_BOUND_LICENSE and stored.stat().st_mode & 0o777 == 0o600

    run_id = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "completed"
    manifest = json.loads((tmp_path / "records" / run_id / "manifest.json").read_text())
    assert manifest["execution"]["gurobi_license"] == "uploaded"
    assert "SECRETKEY123" not in json.dumps(manifest)

    removed = client.delete("/api/solvers/gurobi/license").json()
    assert removed["license_source"] == "none" and not stored.exists()

@pytest.mark.parametrize("content", ["hello world", "FOO=1\nBAR=2", "KEY=abc\n\x00bad=1", ""])
def test_non_license_uploads_are_rejected(client: TestClient, tmp_path: Path, content: str):
    resp = client.put("/api/solvers/gurobi/license", json={"content": content})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] in ("invalid_license_file", "invalid_request")
    assert not (tmp_path / "secrets" / "gurobi.lic").exists()
