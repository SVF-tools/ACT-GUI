"""Run diagnostics and reproduction snapshots: a real ACT failure is captured, located, and replayable."""
from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from engine_bridge.engine_session import act_root
from visual_bench.config import CATALOG_PATH, REPO_ROOT
from visual_bench.server import create_app
from visual_bench.testing import follow_to_end
from visual_bench.verification.diagnostics import Capture, printed_problems, scrubber


def _broken_model(models: Path) -> tuple[str, bytes]:
    """range_check with its first computing layer renamed to a kind ACT does not know (a synthetic fault)."""
    entry = next(m for m in json.loads(CATALOG_PATH.read_text())["models"] if m["id"] == "range_check")
    net = json.loads((act_root() / entry["act_path"]).read_text())
    layer = next(lay for lay in net["act_net"]["layers"] if lay["kind"] not in ("INPUT", "INPUT_SPEC", "ASSERT"))
    layer["kind"] = "NOT_A_LAYER"
    data = json.dumps(net).encode()
    sha = hashlib.sha256(data).hexdigest()
    model_id = f"vnnlib-{sha[:12]}"
    models.mkdir(parents=True)
    (models / f"{model_id}.json").write_bytes(data)
    (models / f"{model_id}.meta.json").write_text(json.dumps({
        "id": model_id, "description": "synthetic broken net", "act_path": f"workbench-models/{model_id}.json",
        "sha256": sha, "methods": ["interval"], "native": {}, "source": "vnnlib", "params": {}, "built_with": None}))
    return model_id, data


def test_failed_act_call_leaves_a_snapshot_that_reproduces_it(tmp_path: Path):
    model_id, net = _broken_model(tmp_path / "models")
    client = TestClient(create_app(tmp_path / "records"))
    run_id = client.post("/api/runs", json={"model_id": model_id, "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)

    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "failed" and run["error"]["code"] == "model_load_failed"
    diag = run["diagnostics"]
    assert "NOT_A_LAYER" in diag["exception"]
    assert diag["location"].startswith("<ACT>/act/"), diag["location"]
    assert any(r["run_id"] == run_id and r["diagnostics"] for r in client.get("/api/runs").json()["runs"])

    resp = client.get(f"/api/runs/{run_id}/snapshot")
    assert resp.status_code == 200 and f"{run_id}-snapshot.zip" in resp.headers["content-disposition"]
    bundle = zipfile.ZipFile(io.BytesIO(resp.content))
    root = f"{run_id}-snapshot"
    names = set(bundle.namelist())
    assert {f"{root}/{n}" for n in ("README.md", "diagnostics.json", "request.json", "reproduce.py", "model/entry.json",
                                    f"model/{model_id}.json", "run/manifest.json", "run/events.jsonl",
                                    "logs/act_stdout.log", "logs/worker_stderr.log")} <= names
    assert bundle.read(f"{root}/model/{model_id}.json") == net
    request = json.loads(bundle.read(f"{root}/request.json"))
    assert request["model_path"] == f"model/{model_id}.json" and request["method"] == "interval"
    recorded = json.loads(bundle.read(f"{root}/diagnostics.json"))
    manifest = json.loads(bundle.read(f"{root}/run/manifest.json"))
    assert recorded["engine"]["commit"] == manifest["act"]["commit"] is not None
    assert recorded["engine"]["source"]["kind"] == "baseline" and recorded["engine"]["capabilities"]
    assert recorded["worker"]["error"]["chain"][-1]["frames"][-1]["origin"] == "act"
    for name in names:
        text = bundle.read(name).decode(errors="replace")
        assert str(tmp_path) not in text and str(REPO_ROOT) not in text, name

    bundle.extractall(tmp_path / "unpacked")
    replay = subprocess.run([sys.executable, "reproduce.py", "--act-gui", str(REPO_ROOT)],
                            cwd=tmp_path / "unpacked" / root, env={**os.environ, "CUDA_VISIBLE_DEVICES": ""},
                            capture_output=True, text=True, timeout=300)
    assert replay.returncode == 0, replay.stderr
    out = json.loads((tmp_path / "unpacked" / root / "reproduced_output.json").read_text())
    assert out["error"]["code"] == "model_load_failed"
    assert out["diagnostics"]["error"]["location"] == recorded["worker"]["error"]["location"]


def test_snapshot_waits_for_the_run_to_end(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "bab", "time_budget_s": 60}).json()["run_id"]
    assert client.get(f"/api/runs/{run_id}/snapshot").json()["error"]["code"] == "run_active"
    client.post(f"/api/runs/{run_id}/stop")
    follow_to_end(client, run_id)
    assert client.get(f"/api/runs/{run_id}/snapshot").status_code == 200


def test_capture_records_warnings_logs_and_the_failing_frame(tmp_path: Path):
    scrub = scrubber({"<ACT-GUI>": REPO_ROOT, "<tmp>": tmp_path})
    before = logging.root.manager.disable
    with Capture(scrub) as capture:
        warnings.warn(f"odd input in {tmp_path}/x", RuntimeWarning)
        logging.getLogger("act.back_end").warning("solver %s fell back", "gurobi")
        logging.getLogger("act.back_end").info("not kept")
        capture.note("layer_states_too_large", "skipped")
        try:
            json.loads("{")
        except ValueError as exc:
            capture.exception(exc)
    report = capture.report()
    assert [w["message"] for w in report["warnings"]] == ["odd input in <tmp>/x"]
    assert report["warnings"][0]["origin"] == "visual_bench"
    assert [(r["logger"], r["message"]) for r in report["logs"]] == [("act.back_end", "solver gurobi fell back")]
    assert report["notes"] == [{"code": "layer_states_too_large", "message": "skipped"}]
    assert report["error"]["exception"].startswith("json.decoder.JSONDecodeError")
    assert report["error"]["location"]["function"]
    assert logging.root.manager.disable == before and capture._handler not in logging.getLogger().handlers


def test_scrubber_replaces_whole_paths_only():
    scrub = scrubber({"<ACT>": "/ACT", "<ACT-GUI>": "/srv/ACT-GUI"})
    assert scrub("/ACT/act/x.py ../ACT/y /ACTX/z /srv/ACT-GUI/visual_bench") == \
        "<ACT>/act/x.py ../ACT/y /ACTX/z <ACT-GUI>/visual_bench"


def test_act_printed_warnings_are_found_in_worker_logs():
    text = "[ACT] Auto-detecting project root\n[WARN] Gurobi license not found\nok\n[ERROR] bad shape\n"
    assert printed_problems(text, "act_stdout.log") == [
        {"log": "act_stdout.log", "line": 2, "level": "WARNING", "message": "Gurobi license not found"},
        {"log": "act_stdout.log", "line": 4, "level": "ERROR", "message": "bad shape"}]
