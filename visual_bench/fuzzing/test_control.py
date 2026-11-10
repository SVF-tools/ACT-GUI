"""Fake-provider HTTP/control-channel tests. Native ACT semantics are tested in engine_bridge/execution."""
from __future__ import annotations

import json
import os
import select
import threading
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from engine_bridge.contracts import BridgeError, FuzzOptionSpec
from visual_bench.fuzzing import service
from visual_bench.fuzzing.schemas import FuzzControlRequest
from visual_bench.records.store import now_iso
from visual_bench.verification.schemas import RunEvent, RunRequest


OPTIONS = (
    FuzzOptionSpec("perturb_scale", "float", True, "Perturbation scale", (), 0, 1, True, 0.1),
    FuzzOptionSpec("coverage_strategy", "choice", False, "Coverage", ("GlobalCov", "BestInputCov"),
                   None, None, False, "GlobalCov"),
)


def test_control_values_preserve_scalar_types_and_weight_maps():
    changes = {"max_iterations": 10, "perturb_scale": 0.2, "stop_on_first_violation": True,
               "perturb_mode": "fixed", "mutation_weights": {"random": 1.0}}
    parsed = FuzzControlRequest(action="update", request_id="values", changes=changes)
    assert parsed.model_dump()["changes"] == changes
    assert type(parsed.changes["stop_on_first_violation"]) is bool
    assert type(parsed.changes["max_iterations"]) is int

@pytest.fixture
def fake_worker(client, monkeypatch):
    """A fake provider with a real OS control pipe and records; it never imports native control APIs."""
    wb = client.app.state.workbench
    original = wb.engine.capability_available
    monkeypatch.setattr(wb.engine, "capability_available",
                        lambda name: name == "fuzz.control" or original(name))
    monkeypatch.setattr(service, "fuzzing_options", lambda: OPTIONS)

    class FakeControl:
        def update(self, changes):
            if set(changes) != {"perturb_scale"} or not isinstance(changes["perturb_scale"], (int, float)) \
                    or not 0 < changes["perturb_scale"] <= 1:
                raise BridgeError("invalid_options", "Fake provider rejects this live option")
            return {"perturb_scale": float(changes["perturb_scale"])}

    monkeypatch.setattr(service, "FuzzRunControl", FakeControl)
    fds, signals = [], []
    monkeypatch.setattr(wb.runs, "_signal_stop", lambda proc, method: signals.append(method))

    def create(method="fuzz", status="running"):
        run_id = f"run-{len(fds):012x}"
        req = RunRequest(model_id="unsafe_linear", method=method, fuzz={} if method == "fuzz" else None)
        model = wb.models.entry(req.model_id)
        wb.records.create(run_id, {
            "run_id": run_id, "created_at": now_iso(), "request": req.model_dump(),
            "model": {"act_path": model["act_path"], "sha256": model["sha256"]},
            "act": {"commit": wb.engine.info.commit},
            "execution": {"fuzz_live": {"perturb_scale": 0.1} if method == "fuzz" else None},
        })
        wb.records.append_event(run_id, "run.started", status, {})
        read_fd, write_fd = os.pipe()
        fds.append((run_id, read_fd, write_fd))
        wb.runs._procs[run_id] = SimpleNamespace(poll=lambda: None)
        wb.runs._control_writes[run_id] = write_fd
        wb.runs._stop[run_id] = threading.Event()
        return run_id, read_fd

    yield SimpleNamespace(create=create, wb=wb, signals=signals)
    for run_id, read_fd, write_fd in fds:
        wb.runs._procs.pop(run_id, None)
        wb.runs._control_writes.pop(run_id, None)
        wb.runs._stop.pop(run_id, None)
        os.close(read_fd)
        os.close(write_fd)


def command(fd):
    assert select.select([fd], [], [], 1)[0], "command did not reach the worker pipe"
    return json.loads(os.read(fd, 65536))


def test_options_schema_reports_active_provider_metadata(client, fake_worker):
    response = client.get("/api/fuzz/options")
    assert response.status_code == 200
    assert response.json() == {"live_control": True, "options": [
        {**asdict(option), "choices": list(option.choices)} for option in OPTIONS]}
    assert client.get("/api/fuzz/defaults").json()["perturb_scale"] == 0.1


def test_control_is_idempotent_and_duplicate_returns_first_receipt(client, fake_worker):
    run_id, fd = fake_worker.create()
    url = f"/api/runs/{run_id}/fuzz/control"
    first = client.post(url, json={"action": "update", "changes": {"perturb_scale": 0.2}, "request_id": "one"})
    assert first.status_code == 200
    assert first.json() == {"run_id": run_id, "action": "update", "request_id": "one",
                            "status": "queued", "changes": {"perturb_scale": 0.2}}
    assert command(fd) == {"action": "update", "changes": {"perturb_scale": 0.2}}
    fake_worker.wb.records.append_event(run_id, "run.failed", "failed", {"code": "fake", "message": "fake completion"})
    duplicate = client.post(url, json={"action": "pause", "request_id": "one"})
    assert duplicate.status_code == 200
    assert duplicate.json() == {**first.json(), "status": "duplicate"}
    assert not select.select([fd], [], [], 0)[0], "duplicate sent a second command"


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_pause_resume_commands_reach_the_control_pipe(client, fake_worker, action):
    run_id, fd = fake_worker.create()
    response = client.post(f"/api/runs/{run_id}/fuzz/control", json={"action": action, "request_id": action})
    assert response.status_code == 200 and response.json()["status"] == "queued"
    assert command(fd) == {"action": action, "changes": None}


@pytest.mark.parametrize("changes", [None, {}, {"coverage_strategy": "BestInputCov"}, {"perturb_scale": 2}])
def test_invalid_live_options_never_reach_worker(client, fake_worker, changes):
    run_id, fd = fake_worker.create()
    response = client.post(f"/api/runs/{run_id}/fuzz/control",
                           json={"action": "update", "changes": changes, "request_id": "invalid"})
    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_options"
    assert not select.select([fd], [], [], 0)[0]


@pytest.mark.parametrize("body", [
    {"action": "unknown", "request_id": "one"}, {"action": "pause"}, {"action": "pause", "request_id": ""},
    {"action": "pause", "changes": {"perturb_scale": 0.2}, "request_id": "one"},
    {"action": "update", "changes": [], "request_id": "one"},
])
def test_control_request_shape_is_validated(client, fake_worker, body):
    run_id, _ = fake_worker.create()
    response = client.post(f"/api/runs/{run_id}/fuzz/control", json=body)
    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_request"


@pytest.mark.parametrize("method,status", [("fuzz", "queued"), ("fuzz", "failed"), ("interval", "running")])
def test_control_requires_a_running_fuzz_run(client, fake_worker, method, status):
    run_id, _ = fake_worker.create(method, status)
    response = client.post(f"/api/runs/{run_id}/fuzz/control", json={"action": "pause", "request_id": "one"})
    assert response.status_code == 409 and response.json()["error"]["code"] == "run_not_running"


def test_missing_run_and_unavailable_control_keep_stop_fallback(client, fake_worker, monkeypatch):
    missing = client.post("/api/runs/missing/fuzz/control", json={"action": "stop", "request_id": "missing"})
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "run_not_found"
    run_id, fd = fake_worker.create()
    monkeypatch.setattr(fake_worker.wb.engine, "capability_available", lambda _: False)
    unavailable = client.post(f"/api/runs/{run_id}/fuzz/control", json={"action": "pause", "request_id": "pause"})
    assert unavailable.status_code == 409 and unavailable.json()["error"]["code"] == "capability_unavailable"
    stopped = client.post(f"/api/runs/{run_id}/fuzz/control", json={"action": "stop", "request_id": "stop"})
    assert stopped.status_code == 200 and stopped.json()["status"] == "queued"
    assert command(fd) == {"action": "stop"}
    assert fake_worker.signals == ["fuzz"]
    assert client.post(f"/api/runs/{run_id}/fuzz/control",
                       json={"action": "stop", "request_id": "stop"}).json()["status"] == "duplicate"
    assert fake_worker.signals == ["fuzz"]


def test_control_projection_replays_applied_changes_and_pause_events(client, fake_worker):
    run_id, _ = fake_worker.create()
    live, records = fake_worker.wb.fuzzing.live, fake_worker.wb.records
    weights = {"pgd": 0.0, "random": 1.0}
    applied = {"iteration": 4, "requested": {"perturb_scale": 0.2, "mutation_weights": weights},
               "applied": {"perturb_scale": 0.2, "mutation_weights": weights}, "rejected": ""}
    rejected = {"iteration": 4, "requested": {"perturb_scale": 0}, "applied": {}, "rejected": "invalid"}
    for msg in ({"control_state": {"paused": True}}, {"control": applied}, {"control": rejected}):
        kind, payload = live.observe(run_id, msg)
        records.append_event(run_id, kind, "running", payload)
    live.forget(run_id)
    control = client.get(f"/api/runs/{run_id}/fuzzing").json()["control"]
    assert control == {"paused": True, "live": {"perturb_scale": 0.2, "mutation_weights": weights},
                       "changes": [applied, rejected]}
    kind, payload = live.observe(run_id, {"control_state": {"paused": False}})
    records.append_event(run_id, kind, "running", payload)
    assert not client.get(f"/api/runs/{run_id}/fuzzing").json()["control"]["paused"]
    # The SSE route serializes every committed event through RunEvent.
    streamed = [RunEvent.model_validate(ev).model_dump(mode="json") for ev in records.events(run_id)]
    assert [e["kind"] for e in streamed if e["kind"].startswith("fuzz.")] == [
        "fuzz.paused", "fuzz.control", "fuzz.control", "fuzz.resumed"]
    assert streamed[-3]["payload"] == applied
