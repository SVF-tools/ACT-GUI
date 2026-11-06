"""Model catalog and model source tests through the HTTP surface (real ACT builds).

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from engine_bridge.model_spec import file_sha256
from visual_bench.server import create_app
from visual_bench.testing import follow_to_end, sources_or_skip


def test_torch_model_load_is_idempotent_listed_runnable_and_persisted(client: TestClient, tmp_path: Path):
    sources_or_skip(client)
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

def test_model_from_another_engine_is_flagged_when_it_fails_to_load_and_rebuilds(client: TestClient, tmp_path: Path):
    sources_or_skip(client)
    body = {"source": {"kind": "torch", "source_id": "mnist_conv_small", "index": 3, "eps": 0.05, "indices": [3, 0]}}
    m = client.post("/api/models", json=body).json()
    commit = client.get("/api/engine").json()["commit"]
    assert (m["built_with"]["commit"], m["built_with"]["kind"], m["engine_check"]) == (commit, "baseline", "same_commit")

    # Synthetic stand-in for a net written by another ACT commit: a model file this engine's loader rejects.
    models = tmp_path / "models"
    old_id = "torch-000000000000"
    (models / f"{old_id}.json").write_text('{"layers": [{"id": 0, "kind": "NOT_AN_ACT_LAYER"}]}')
    meta = {**json.loads((models / f"{m['model_id']}.meta.json").read_text()), "id": old_id,
            "act_path": f"workbench-models/{old_id}.json", "sha256": file_sha256(models / f"{old_id}.json"),
            "built_with": {"commit": "0" * 40, "kind": "branch", "remote": "elsewhere", "branch": "old"}}
    (models / f"{old_id}.meta.json").write_text(json.dumps(meta))
    restarted = TestClient(create_app(tmp_path / "records"))

    def check() -> str:
        return next(x for x in restarted.get("/api/models").json() if x["model_id"] == old_id)["engine_check"]

    assert check() == "unchecked"
    failed = restarted.get(f"/api/models/{old_id}")
    assert failed.status_code >= 400 and failed.json()["error"]["code"] == "model_load_failed"
    assert check() == "load_failed"

    rebuilt = restarted.post(f"/api/models/{old_id}/rebuild")
    assert rebuilt.status_code == 200 and rebuilt.json()["model_id"] == m["model_id"]  # same source, same content
    assert rebuilt.json()["engine_check"] == "same_commit"
    assert restarted.post("/api/models/bab_deep_mlp/rebuild").json()["error"]["code"] == "not_rebuildable"

def test_vnnlib_instance_load_and_dataset_sample(client: TestClient):
    s = sources_or_skip(client)
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
    ({"kind": "torch", "source_id": "mnist_conv_small", "index": 0, "eps": 0.1, "indices": [0, 1, 0]}, 422, "invalid_request"),
    ({"kind": "torch", "source_id": "mnist_conv_small", "index": 0, "eps": 0.1, "indices": [0, 10_000]}, 422, "invalid_instance"),
    ({"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "../../etc/x.onnx", "vnnlib": "v.vnnlib"}, 422, "invalid_request"),
    ({"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "onnx/missing.onnx", "vnnlib": "vnnlib/mnist-img0.vnnlib"}, 404, "source_not_found"),
])
def test_invalid_model_loads_are_structured_errors(client: TestClient, tmp_path: Path, body, status, code):
    sources_or_skip(client)
    resp = client.post("/api/models", json={"source": body})
    assert resp.status_code == status and resp.json()["error"]["code"] == code
    assert list((tmp_path / "models").glob("*.json")) == []
