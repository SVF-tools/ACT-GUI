"""Run lifecycle tests through the HTTP surface, with real ACT worker runs.

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from visual_bench.records import RecordStore
from visual_bench.server import create_app
from visual_bench.testing import follow_to_end
from visual_bench.workbench import Workbench


def test_bab_run_lifecycle_matches_native_and_is_persisted(client: TestClient, tmp_path: Path):
    t0 = time.perf_counter()
    resp = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "bab", "time_budget_s": 15})
    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"
    assert time.perf_counter() - t0 < 2.0, "start must not wait for ACT"
    run_id = resp.json()["run_id"]

    events = follow_to_end(client, run_id)
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert [e["kind"] for e in events] == ["run.queued", "run.started", "bab.summary", "run.completed"]

    run = client.get(f"/api/runs/{run_id}").json()
    assert run["result"]["act_status"] == "CERTIFIED" and run["matches_native"] is True
    layers = client.get(f"/api/runs/{run_id}/layers").json()
    assert layers["availability"] == "available" and len(layers["layers"]) == 8

    record = tmp_path / "records" / run_id
    hashes = json.loads((record / "artifacts.json").read_text())
    assert set(hashes) == {"manifest.json", "result.json", "layers.json"}
    bundle = zipfile.ZipFile(io.BytesIO(client.get(f"/api/runs/{run_id}/export").content))
    assert all(not n.startswith("/") and ".." not in n for n in bundle.namelist())
    assert str(tmp_path) not in bundle.read(f"{run_id}/manifest.json").decode()

def test_falsified_run_reports_act_counterexample(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "unsafe_linear", "method": "bab", "time_budget_s": 15}).json()["run_id"]
    follow_to_end(client, run_id)
    result = client.get(f"/api/runs/{run_id}").json()["result"]
    assert result["verdict"] == "falsified" and result["counterexample"]

def test_stop_ends_a_verification_worker_without_a_verdict(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "bab", "time_budget_s": 60}).json()["run_id"]
    client.post(f"/api/runs/{run_id}/stop")  # before the worker can import ACT, so it never reports a result
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "failed" and run["error"]["code"] == "stopped" and run["result"] is None

def test_domain_run_records_domain_and_has_no_interval_native_reference(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "interval",
                                            "domain": "hybridz"}).json()["run_id"]
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["domain"] == "hybridz" and run["result"]["act_status"] == "CERTIFIED"
    assert run["native_reference"] is None and run["matches_native"] is None
    layers = client.get(f"/api/runs/{run_id}/layers").json()
    assert layers["method"] == "interval" and layers["provenance"]["transfer_function"] == "interval"
    default = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()
    assert default["domain"] == "interval"
    follow_to_end(client, default["run_id"])

def test_idempotent_start_and_conflict(client: TestClient):
    body = {"model_id": "range_check", "method": "interval", "client_request_id": "req-1"}
    first = client.post("/api/runs", json=body)
    again = client.post("/api/runs", json=body)
    assert (first.status_code, again.status_code) == (202, 200)
    assert first.json()["run_id"] == again.json()["run_id"]
    conflict = client.post("/api/runs", json={**body, "method": "bab"})
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "idempotency_conflict"
    follow_to_end(client, first.json()["run_id"])

@pytest.mark.parametrize("body,status,code", [
    ({"model_id": "nope", "method": "bab"}, 404, "model_not_found"),
    ({"model_id": "cnn_1x8x8", "method": "bab"}, 422, "unsupported_method"),
    ({"model_id": "range_check", "method": "magic"}, 422, "invalid_request"),
    ({"model_id": "range_check", "method": "bab", "time_budget_s": 0}, 422, "invalid_request"),
    ({"model_id": "range_check", "method": "bab", "extra": 1}, 422, "invalid_request"),
    ({"model_id": "range_check", "method": "bab", "domain": "dual"}, 422, "invalid_request"),
    ({"model_id": "range_check", "method": "interval", "domain": "zonotope"}, 422, "invalid_request"),
])
def test_invalid_run_requests_are_structured_errors(client: TestClient, body, status, code):
    resp = client.post("/api/runs", json=body)
    assert resp.status_code == status and resp.json()["error"]["code"] == code

def test_unknown_run_and_bad_run_id_are_404(client: TestClient):
    assert client.get("/api/runs/run-000000000000").status_code == 404
    assert client.get("/api/runs/..%2Fetc").status_code == 404

def test_tampered_result_is_not_served(tmp_path: Path):
    client = TestClient(create_app(tmp_path / "records"))
    run_id = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    (tmp_path / "records" / run_id / "result.json").write_text('{"verdict": "certified"}')
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "failed" and run["error"]["code"] == "record_corrupt"

def test_torn_event_tail_keeps_committed_prefix_and_restart_marks_interrupted(tmp_path: Path):
    store = RecordStore(tmp_path)
    store.create("run-aaaaaaaaaaaa", {"run_id": "run-aaaaaaaaaaaa", "created_at": "2026-01-01T00:00:00+00:00",
                                      "request": {"model_id": "range_check", "method": "interval", "time_budget_s": 5.0,
                                                  "client_request_id": None},
                                      "model": {"act_path": "x", "sha256": "y"}, "act": {"commit": None}})
    store.append_event("run-aaaaaaaaaaaa", "run.queued", "queued")
    with open(tmp_path / "run-aaaaaaaaaaaa" / "events.jsonl", "a") as f:
        f.write('{"seq": 2, "kind": "run.sta')
    assert [e["seq"] for e in store.events("run-aaaaaaaaaaaa")] == [1]
    wb = Workbench(tmp_path)
    run = wb.runs.get("run-aaaaaaaaaaaa")
    assert run.status == "failed" and run.error is not None and run.error.code == "interrupted"
