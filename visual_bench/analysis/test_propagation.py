"""Synthetic producer -> storage -> analysis HTTP tests (not scientific ACT fixtures)."""
from __future__ import annotations

import io
import json
import time
import zipfile
from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from engine_bridge.inspection.propagation import PropagationSink
from engine_bridge.inspection.testing import observation_api
from visual_bench.analysis.routes import router
from visual_bench.analysis.service import AnalysisService
from visual_bench.errors import AppError
from visual_bench.records import RecordStore
from visual_bench.records.propagation import PropagationWriter
from visual_bench.verification.schemas import RunEvent

RUN = "run-aaaaaaaaaaaa"


@pytest.fixture
def recorded(tmp_path, monkeypatch):
    store = RecordStore(tmp_path)
    store.create(RUN, {"created_at": "2026-11-05"})
    run = SimpleNamespace(status="running", domain="dual", method="interval")
    service = AnalysisService(SimpleNamespace(get=lambda _: run), store)
    app = FastAPI()
    @app.exception_handler(AppError)
    async def error(_, exc):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)
    app.include_router(router(service))
    client = TestClient(app)
    sent = []
    monkeypatch.setattr("visual_bench.records.propagation.time.monotonic", lambda: 1.0)
    writer = PropagationWriter(store.run_dir(RUN), "dual", sent.append)
    sink = PropagationSink(writer)
    obs = observation_api()
    key = obs.RecordKey("dual", "forward", 3, stage="pre")
    with obs.observe(sink):
        obs.emit(obs.PhaseEvent("verify_once", "start", time.perf_counter_ns()))
        for version in range(100):
            obs.emit(obs.LayerBounds(replace(key, version=version), "RELU",
                                    torch.tensor([[-1., 0., 2.]]), torch.tensor([[3., 0., float("inf")]]),
                                    time.perf_counter_ns()))
        key = replace(key, version=99)
        obs.emit(obs.Relaxation(key, torch.tensor([[-1, 0, 1]]), "linear",
                                lower_slope=torch.zeros(1, 3), upper_slope=torch.ones(1, 3)))
        obs.emit(obs.DualBackward(replace(key, pass_="backward"), torch.ones(1, 2, 3), False))
        obs.emit(obs.SpecBound(replace(key, pass_="backward", layer_id=9), torch.tensor([[.1, .2]]),
                              torch.tensor([[.1]]), 0, "n_iters"))
    writer.finish(sink.ignored_records)
    return store, run, service, client, writer, sent


def test_complete_index_throttled_events_and_deduplicated_sealed_blobs(recorded):
    store, run, service, client, writer, sent = recorded
    assert len(sent) == 2  # first and final notification; full history is durable
    index = client.get(f"/api/runs/{RUN}/propagation").json()
    assert len(index["records"]) == 103 and len(index["phases"]) == 1
    assert index["records"][0]["tensors"]["lb"] == index["records"][99]["tensors"]["lb"]
    assert len(list((store.run_dir(RUN) / "blobs").glob("*.f32"))) < 12
    relu = next(l for l in index["layers"] if l["key"]["layer_id"] == 3 and l["key"]["pass_"] == "forward")
    assert relu["counts"] == {"n_active": 1, "n_inactive": 1, "n_unstable": 1}
    for entry in sent:
        event = store.append_event(RUN, "verify.propagation", "running", entry)
        assert RunEvent.model_validate(event).kind == "verify.propagation"
    hashes = store.seal(RUN)
    assert "propagation.json" in hashes and any(n.startswith("blobs/") for n in hashes)
    run.status = "completed"
    assert client.get(f"/api/runs/{RUN}/propagation").status_code == 200
    bundle = zipfile.ZipFile(io.BytesIO(store.export_zip(RUN)))
    assert {f"{RUN}/{n}" for n in hashes} <= set(bundle.namelist())


def test_layer_values_versions_passes_nonfinite_and_missing_data(recorded):
    store, run, service, client, writer, sent = recorded
    url = f"/api/runs/{RUN}/propagation/layers/3"
    response = client.get(url)
    assert response.status_code == 200, response.text
    detail = response.json()
    assert len(detail["records"]) == 3
    bound = next(r for r in detail["records"] if r["kind"] == "LayerBounds")
    assert bound["key"]["version"] == 99
    assert bound["values"]["lb"] == [-1, 0, 2]
    assert bound["values"]["ub"] == [3, 0, "Infinity"]
    alpha = next(r for r in detail["records"] if r["kind"] == "DualBackward")
    assert alpha["tensors"]["alpha"]["shape"] == [1, 2, 3] and alpha["metadata"]["alpha_optimized"] is False
    old = client.get(url + "?pass_=forward&stage=pre&version=5").json()
    assert len(old["records"]) == 1 and old["records"][0]["key"]["version"] == 5
    assert client.get(url + "?version=999").json()["availability"] == "not_recorded"
    spec = client.get(f"/api/runs/{RUN}/propagation/layers/9?pass_=backward").json()
    assert "margins" in spec["records"][0]["values"]
    assert client.get(url + "?version=-1").status_code == 422


def test_corrupt_seal_or_blob_never_serves_values(recorded):
    store, run, service, client, writer, sent = recorded
    store.seal(RUN)
    run.status = "completed"
    blob = next((store.run_dir(RUN) / "blobs").glob("*.f32"))
    blob.write_bytes(b"tampered")
    # Query every layer since the selected corrupt blob may belong to the ASSERT record.
    responses = [client.get(f"/api/runs/{RUN}/propagation/layers/{i}") for i in (3, 9)]
    assert any(r.status_code == 409 and r.json()["error"]["code"] == "record_corrupt" for r in responses)
    (store.run_dir(RUN) / "propagation.json").write_text("{}")
    assert client.get(f"/api/runs/{RUN}/propagation").status_code == 409


def test_value_limit_rejects_without_truncation(recorded):
    store, run, service, client, writer, sent = recorded
    obs = observation_api()
    sink = PropagationSink(writer)
    with obs.observe(sink):
        obs.emit(obs.LayerBounds(obs.RecordKey("dual", "forward", 100), "LINEAR", torch.zeros(1, 65537),
                                torch.ones(1, 65537), time.perf_counter_ns()))
    writer.finish(0)
    response = client.get(f"/api/runs/{RUN}/propagation/layers/100")
    assert response.status_code == 413 and response.json()["error"]["code"] == "too_large"


def test_layer_fields_and_single_neuron_keep_large_layers_in_the_limit(recorded):
    store, run, service, client, writer, sent = recorded
    url = f"/api/runs/{RUN}/propagation/layers/3"
    mapped = client.get(url + "?fields=lb,ub,status").json()
    assert mapped["records"] and {n for r in mapped["records"] for n in r["values"]} <= {"lb", "ub", "status"}
    one = client.get(url + "?pass_=backward&neuron=2").json()
    alpha = next(r for r in one["records"] if r["kind"] == "DualBackward")
    assert one["neuron"] == 2 and alpha["tensors"]["alpha"]["shape"] == [1, 2, 1] and alpha["values"]["alpha"] == [1.0, 1.0]
    pre = next(r for r in client.get(url + "?pass_=forward&stage=pre&neuron=2").json()["records"] if r["kind"] == "LayerBounds")
    assert pre["values"]["lb"] == [2.0] and pre["values"]["ub"] == ["Infinity"]
    assert client.get(url + "?neuron=3").status_code == 422


def test_missing_sealed_index_is_corruption_not_missing_history(recorded):
    store, run, service, client, writer, sent = recorded
    store.seal(RUN)
    run.status = "completed"
    (store.run_dir(RUN) / "propagation.json").unlink()
    assert client.get(f"/api/runs/{RUN}/propagation").status_code == 409


def test_unavailable_index_is_explicit_and_old_records_remain_readable(recorded):
    store, run, service, client, writer, sent = recorded
    store.write_artifact(RUN, "propagation.json", {
        "domain": "dual", "availability": "unavailable", "complete": True,
        "records": [], "phases": [], "ignored_records": 0,
    })
    store.seal(RUN)
    run.status = "completed"
    assert client.get(f"/api/runs/{RUN}/propagation").json()["availability"] == "unavailable"
    assert client.get(f"/api/runs/{RUN}/propagation/layers/3").json()["availability"] == "unavailable"
