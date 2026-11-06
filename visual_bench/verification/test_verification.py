"""Run lifecycle tests through the HTTP surface, with real ACT worker runs.

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from visual_bench.records import RecordStore
from visual_bench.server import create_app
from visual_bench.testing import follow_to_end, sources_or_skip
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

    url = f"/api/runs/{run_id}/saved-counterexample"
    assert client.get(f"{url}/vnnlib").json()["error"]["code"] == "counterexample_not_saved"
    first, again = client.post(url), client.post(url)
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["counterexample_saved_at"] == again.json()["counterexample_saved_at"] is not None
    resp = client.get(f"{url}/vnnlib")
    assert resp.status_code == 200 and f"{run_id}-ce.counterexample" in resp.headers["content-disposition"]
    lines = resp.text.splitlines()
    x, y = result["counterexample"], result["counterexample_output"]
    shape = client.get("/api/models/unsafe_linear").json()["input_specs"][0]["shape"]
    assert lines[0] == "sat" and lines[1] == f"X float64 [{','.join(map(str, shape))}]"
    assert [float(v) for v in lines[2:2 + len(x)]] == x
    assert lines[2 + len(x)] == f"Y float64 [1,{len(y)}]" and [float(v) for v in lines[3 + len(x):]] == y
    bundle = zipfile.ZipFile(io.BytesIO(client.get(f"/api/runs/{run_id}/export").content))
    assert f"{run_id}/saved_counterexamples.json" in bundle.namelist()

    certified = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()["run_id"]
    follow_to_end(client, certified)
    assert client.post(f"/api/runs/{certified}/saved-counterexample").json()["error"]["code"] == "counterexample_not_found"

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

def test_verification_defaults_match_act_dual_config(client: TestClient):
    from engine_bridge.engine_session import act_imports

    served = client.get("/api/verification/defaults").json()
    with act_imports():
        from act.config.config import DualConfig

        act = DualConfig()
    act_name: dict[str, str] = {"iterations": "n_iters", "max_time_s": "max_time"}
    tunable = {k: v for k, v in served["dual"].items() if k != "alpha"}
    assert tunable == {k: getattr(act, act_name[k] if k in act_name else k) for k in tunable}
    assert served["dual"]["alpha"] == "fixed" and served["hybridz"] == {"tolerance": 1e-7}

def test_dual_alpha_optimization_reaches_act(client: TestClient):
    caps = {c["name"]: c["availability"] for c in client.get("/api/engine").json()["capabilities"]}
    if caps.get("verify.dual.options") != "available":
        pytest.skip("active ACT checkout has no verify_once dual options (branch act-gui-match)")

    def run(dual: dict[str, object] | None) -> dict[str, Any]:
        body = {"model_id": "bab_deep_mlp", "method": "interval", "domain": "dual", **({"dual": dual} if dual else {})}
        run_id = client.post("/api/runs", json=body).json()["run_id"]
        follow_to_end(client, run_id)
        return client.get(f"/api/runs/{run_id}").json()

    fixed = run(None)  # fixed slopes leave bab_deep_mlp UNKNOWN; optimized alpha tightens ACT's dual bound
    assert fixed["dual"]["alpha"] == "fixed" and fixed["result"]["act_status"] == "UNKNOWN"
    slack = fixed["result"]["metadata"]["min_slack"]
    for alpha in ("optimize", "optimize_refresh"):
        optimized = run({"alpha": alpha, "iterations": 20})
        assert optimized["dual"] == {**fixed["dual"], "alpha": alpha, "iterations": 20}
        assert optimized["status"] == "completed", optimized["error"]
        assert optimized["result"]["metadata"]["min_slack"] > slack

def test_torch_batch_verification_records_a_verdict_per_image(client: TestClient):
    sources_or_skip(client)
    m = client.post("/api/models", json={"source": {"kind": "torch", "source_id": "mnist_conv_small", "index": 3,
                                                    "eps": 0.01, "indices": [3, 0, 7]}}).json()
    assert "interval" in m["methods"] and "bab" not in m["methods"]
    run_id = client.post("/api/runs", json={"model_id": m["model_id"], "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "completed", run["error"]
    rows = run["result"]["rows"]
    assert [r["row"] for r in rows] == [0, 1, 2] and run["result"]["metadata"]["batch"] == 3
    assert (run["result"]["verdict"] == "certified") == all(r["verdict"] == "certified" for r in rows)
    layers = client.get(f"/api/runs/{run_id}/layers").json()
    assert layers["availability"] != "available"  # layer inspection reads one input lane

def test_batched_run_saves_and_exports_the_counterexample_of_each_falsified_row(client: TestClient):
    s = sources_or_skip(client)
    cora = next(b for b in s["vnnlib"] if b["benchmark"] == "cora_2024")
    props = [i["vnnlib"] for i in cora["instances"] if i["onnx"] == "onnx/mnist-point.onnx"][:6]
    m = client.post("/api/models", json={"source": {"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "onnx/mnist-point.onnx",
                                                    "vnnlib": props[0], "vnnlibs": props}}).json()
    run_id = client.post("/api/runs", json={"model_id": m["model_id"], "method": "interval", "domain": "dual"}).json()["run_id"]
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    if run["status"] == "failed":  # ACT branches without batched 1-D INPUT support reject this net in verify_once
        pytest.skip(f"this ACT cannot verify a batched VNN-LIB net: {run['error']['message']}")
    result = run["result"]
    falsified = [r for r in result["rows"] if r["verdict"] == "falsified"]
    assert len(falsified) >= 2 and all(r["counterexample"] and r["counterexample_output"] for r in falsified)
    assert (result["counterexample_row"], result["counterexample"]) == (falsified[0]["row"], falsified[0]["counterexample"])

    url = f"/api/runs/{run_id}/saved-counterexample"
    picked = falsified[-2:]  # not only the summary row
    for r in picked:
        assert client.get(f"{url}/vnnlib?row={r['row']}").json()["error"]["code"] == "counterexample_not_saved"
        assert [client.post(f"{url}?row={r['row']}").status_code for _ in range(2)] == [201, 200]
        resp = client.get(f"{url}/vnnlib?row={r['row']}")
        assert f"{run_id}-row{r['row']}-ce.counterexample" in resp.headers["content-disposition"]
        lines, x, y = resp.text.splitlines(), r["counterexample"], r["counterexample_output"]
        assert lines[0] == "sat" and [float(v) for v in lines[2:2 + len(x)]] == x
        assert [float(v) for v in lines[3 + len(x):]] == y
    assert client.get(f"/api/runs/{run_id}").json()["saved_counterexample_rows"] == [r["row"] for r in picked]
    unfalsified = next((r["row"] for r in result["rows"] if r["verdict"] != "falsified"), None)
    if unfalsified is not None:
        assert client.post(f"{url}?row={unfalsified}").json()["error"]["code"] == "counterexample_not_found"

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
    ({"model_id": "range_check", "method": "interval", "dual": {"alpha": "optimize"}}, 422, "invalid_request"),
    ({"model_id": "range_check", "method": "interval", "domain": "dual", "dual": {"iterations": 0}}, 422,
     "invalid_request"),
    ({"model_id": "range_check", "method": "interval", "domain": "dual", "hybridz": {}}, 422, "invalid_request"),
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
