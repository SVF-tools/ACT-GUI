"""Workbench service tests through the HTTP surface, with a real ACT worker run.

Run completion is awaited on the run's own SSE stream (bounded by the worker
timeout), never with sleeps.
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
from visual_bench.verification.service import Workbench


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "records"))


def follow_to_end(client: TestClient, run_id: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    with client.stream("GET", f"/api/runs/{run_id}/events") as resp:
        for line in resp.iter_lines():
            if line.startswith("data: ") and line != "data: {}":
                events.append(json.loads(line[6:]))
            if line == "event: end":
                break
    return events


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


def test_fuzz_run_streams_progress_and_records_act_counterexamples(client: TestClient, tmp_path: Path):
    assert "fuzz" in client.get("/api/models").json()[0]["methods"]
    body = {"model_id": "unsafe_linear", "method": "fuzz", "time_budget_s": 10,
            "fuzz": {"max_iterations": 50, "rng_seed": 7}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    kinds = [e["kind"] for e in follow_to_end(client, run_id)]
    assert kinds[:2] == ["run.queued", "run.started"] and kinds[-1] == "run.completed"
    assert set(kinds[2:-1]) == {"fuzz.progress"}

    run = client.get(f"/api/runs/{run_id}").json()
    assert run["result"]["verdict"] == "falsified" and run["native_reference"] is None
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["availability"] == "available" and fz["options"]["rng_seed"] == 7
    assert fz["summary"]["iterations"] == 50 and fz["summary"]["counterexample_count"] >= 1
    assert run["result"]["counterexample"] == fz["counterexamples"][0]["input"]
    assert fz["seeds"] and len(fz["counterexamples"][0]["seed_output"]) == len(fz["seeds"][0]["output"])
    assert fz["timeline"][-1]["iteration"] == 50
    assert fz["frames"] and fz["frames"][-1]["iteration"] == 50
    assert len(fz["frames"][0]["input"]) == len(fz["frames"][0]["seed_input"]) == len(fz["seeds"][0]["input"])
    assert sum(s["selected"] for s in fz["strategies"]) == 50
    assert "fuzzing.json" in json.loads((tmp_path / "records" / run_id / "artifacts.json").read_text())


def test_saved_counterexample_is_idempotent_and_exports_vnnlib2_assignment(client: TestClient):
    body = {"model_id": "unsafe_linear", "method": "fuzz", "time_budget_s": 10,
            "fuzz": {"max_iterations": 50, "rng_seed": 7}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    follow_to_end(client, run_id)
    ce = client.get(f"/api/runs/{run_id}/fuzzing").json()["counterexamples"][0]
    url = f"/api/runs/{run_id}/saved-counterexamples"
    first, again = client.post(url, json={"index": ce["index"]}), client.post(url, json={"index": ce["index"]})
    assert (first.status_code, again.status_code) == (201, 200) and first.json() == again.json()
    assert client.post(url, json={"index": 999}).json()["error"]["code"] == "counterexample_not_found"
    saved = client.get(f"/api/runs/{run_id}/fuzzing").json()["saved"]
    assert [s["counterexample"] for s in saved] == [ce]

    resp = client.get(f"{url}/{ce['index']}/vnnlib")
    assert resp.status_code == 200 and f"{run_id}-ce{ce['index']}.counterexample" in resp.headers["content-disposition"]
    # VNN-COMP result: "sat", then per variable "<name> <type> [<dims>]" and its values in row-major order.
    lines = resp.text.splitlines()
    shape = client.get("/api/models/unsafe_linear").json()["input_specs"][0]["shape"]
    nx, ny = len(ce["input"]), len(ce["output"])
    assert lines[0] == "sat" and lines[1] == f"X float64 [{','.join(map(str, shape))}]"
    assert [float(v) for v in lines[2:2 + nx]] == ce["input"]
    assert lines[2 + nx] == f"Y float64 [1,{ny}]" and [float(v) for v in lines[3 + nx:]] == ce["output"]
    assert client.get(f"{url}/12345/vnnlib").status_code == 404
    bundle = zipfile.ZipFile(io.BytesIO(client.get(f"/api/runs/{run_id}/export").content))
    assert f"{run_id}/saved_counterexamples.json" in bundle.namelist()


def test_stop_ends_fuzz_run_with_act_report_of_iterations_run(tmp_path: Path):
    app = create_app(tmp_path / "records")
    client = TestClient(app)
    body = {"model_id": "bab_deep_mlp", "method": "fuzz", "time_budget_s": 120,
            "fuzz": {"max_iterations": 1_000_000, "rng_seed": 0}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    # Wait on the record store's commit signal for ACT's first progress report (an SSE stream the test
    # closes early would keep the TestClient waiting until the run ends).
    records = app.state.workbench.records
    seq = 0
    while True:
        evs = records.wait_for_events(run_id, seq, 60.0)
        assert evs, "no fuzz progress within 60 s"
        if any(e["kind"] == "fuzz.progress" for e in evs):
            break
        seq = evs[-1]["seq"]
    assert client.post(f"/api/runs/{run_id}/stop").json()["status"] == "running"
    kinds = [e["kind"] for e in follow_to_end(client, run_id)]
    assert "run.stop_requested" in kinds and kinds[-1] == "run.completed"
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["summary"]["stopped"] is True and fz["summary"]["iterations"] < 1_000_000
    assert client.post(f"/api/runs/{run_id}/stop").json()["status"] == "completed"  # no-op once terminal


def test_stop_ends_a_verification_worker_without_a_verdict(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "bab", "time_budget_s": 60}).json()["run_id"]
    client.post(f"/api/runs/{run_id}/stop")  # before the worker can import ACT, so it never reports a result
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "failed" and run["error"]["code"] == "stopped" and run["result"] is None


def test_fuzz_options_require_fuzz_method_and_other_runs_have_no_fuzzing(client: TestClient):
    bad = client.post("/api/runs", json={"model_id": "range_check", "method": "interval", "fuzz": {}})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_request"
    run_id = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    assert client.get(f"/api/runs/{run_id}/fuzzing").json()["availability"] == "unsupported"


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
    run = wb.get_run("run-aaaaaaaaaaaa")
    assert run.status == "failed" and run.error is not None and run.error.code == "interrupted"


def test_explanation_cites_resolvable_evidence_and_keeps_context(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    ctx = {"model_id": "bab_deep_mlp", "run_id": run_id, "layer_id": 3, "neuron": 1}
    ans = client.post("/api/assistant/explain", json={"context": ctx, "question": "why?"}).json()
    assert ans["context"] == ctx and ans["provider_kind"] == "fake"
    ids = {e["ref_id"] for e in ans["evidence"]}
    assert all(ref in ids for s in ans["sections"] for ref in s["evidence"])
    assert any("UNKNOWN" in e["value"] for e in ans["evidence"] if e["kind"] == "run_result")
    mismatch = client.post("/api/assistant/explain", json={"context": {**ctx, "model_id": "range_check"}, "question": "?"})
    assert mismatch.status_code == 422 and mismatch.json()["error"]["code"] == "context_mismatch"


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


def _sources_or_skip(client: TestClient) -> dict[str, Any]:
    s = client.get("/api/sources").json()
    if not s["classifiers"] or not s["vnnlib"]:
        pytest.skip("ACT checkout has no classifier ONNX models or VNN-LIB benchmarks")
    return s


def test_torch_model_load_is_idempotent_listed_runnable_and_persisted(client: TestClient, tmp_path: Path):
    _sources_or_skip(client)
    body = {"source": {"kind": "torch", "source_id": "mnist_conv_small", "index": 3, "eps": 0.05}}
    first, again = client.post("/api/models", json=body), client.post("/api/models", json=body)
    assert (first.status_code, again.status_code) == (201, 200)
    m = first.json()
    assert again.json()["model_id"] == m["model_id"] and m["model_id"].startswith("torch-")
    assert (m["source"], m["params"]["index"], m["params"]["eps"], m["native"]) == ("torch", 3, 0.05, {})
    d = client.get(f"/api/models/{m['model_id']}").json()
    assert d["input_specs"][0]["shape"] == [1, 1, 28, 28] and d["output_spec"]["true_class"] == m["params"]["label"]

    run_id = client.post("/api/runs", json={"model_id": m["model_id"], "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "completed" and run["native_reference"] is None and run["model_sha256"] == m["sha256"]

    restarted = TestClient(create_app(tmp_path / "records"))
    assert m["model_id"] in [x["model_id"] for x in restarted.get("/api/models").json()]


def test_vnnlib_instance_load_and_dataset_sample(client: TestClient):
    s = _sources_or_skip(client)
    cora = next(b for b in s["vnnlib"] if b["benchmark"] == "cora_2024")
    inst = next(i for i in cora["instances"] if i["onnx"] == "onnx/mnist-point.onnx")
    resp = client.post("/api/models", json={"source": {"kind": "vnnlib", "benchmark": "cora_2024", **inst}})
    assert resp.status_code == 201
    m = resp.json()
    assert m["source"] == "vnnlib" and m["params"]["vnnlib"] == inst["vnnlib"]
    d = client.get(f"/api/models/{m['model_id']}").json()
    assert d["input_specs"][0]["dataset"] == "mnist" and d["output_spec"]["kind"] == "TOP1_ROBUST"
    sample = client.get("/api/sources/sample", params={"dataset": "mnist", "index": 3}).json()
    assert (sample["index"], sample["shape"], len(sample["pixels"])) == (3, [1, 28, 28], 784)


@pytest.mark.parametrize("body,status,code", [
    ({"kind": "torch", "source_id": "nope", "index": 0, "eps": 0.1}, 404, "source_not_found"),
    ({"kind": "torch", "source_id": "mnist_conv_small", "index": 10_000, "eps": 0.1}, 422, "invalid_instance"),
    ({"kind": "torch", "source_id": "mnist_conv_small", "index": 0, "eps": 2}, 422, "invalid_request"),
    ({"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "../../etc/x.onnx", "vnnlib": "v.vnnlib"}, 422, "invalid_request"),
    ({"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "onnx/missing.onnx", "vnnlib": "vnnlib/mnist-img0.vnnlib"}, 404, "source_not_found"),
])
def test_invalid_model_loads_are_structured_errors(client: TestClient, tmp_path: Path, body, status, code):
    _sources_or_skip(client)
    resp = client.post("/api/models", json={"source": body})
    assert resp.status_code == status and resp.json()["error"]["code"] == code
    assert list((tmp_path / "models").glob("*.json")) == []


@pytest.mark.parametrize("content", ["hello world", "FOO=1\nBAR=2", "KEY=abc\n\x00bad=1", ""])
def test_non_license_uploads_are_rejected(client: TestClient, tmp_path: Path, content: str):
    resp = client.put("/api/solvers/gurobi/license", json={"content": content})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] in ("invalid_license_file", "invalid_request")
    assert not (tmp_path / "secrets" / "gurobi.lic").exists()
