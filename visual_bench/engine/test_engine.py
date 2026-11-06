"""Engine and Gurobi license tests through the HTTP surface.

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_bridge.testing import CATALOG, fake_act_remote
from visual_bench.engine import service as engine_service
from visual_bench.server import create_app
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

def test_act_branch_switch_is_checked_persisted_and_restarts_the_service(tmp_path: Path, monkeypatch):
    url, commits = fake_act_remote(tmp_path / "remote")
    monkeypatch.setenv("ACT_GUI_ACT_REMOTES", f"fake={url}")
    monkeypatch.delenv("ACT_CODE_ROOT", raising=False)
    restarts: list[str] = []
    monkeypatch.setattr(engine_service, "restart_service", lambda: restarts.append("restart"))
    app = create_app(tmp_path / "records")
    client = TestClient(app)
    baseline = {"kind": "baseline", "remote": None, "url": None, "branch": None, "commit": None, "switched_at": None}
    assert client.get("/api/engine/source").json() == {
        "active": baseline, "remotes": [{"name": "fake", "url": url, "custom": False}], "custom_allowed": True}
    assert client.get("/api/engine/branches", params={"remote": "fake"}).json()["branches"] == ["broken", "feature"]
    assert client.get("/api/engine/branches", params={"remote": "other"}).status_code == 404
    assert client.put("/api/engine/source", json={"remote": "fake", "branch": "nope"}).status_code == 404

    checked = client.post("/api/engine/source/check", json={"remote": "fake", "branch": "feature"}).json()
    assert checked["commit"] == commits["feature"] and checked["api_checks"]
    assert not any(c["ok"] for c in checked["api_checks"])
    assert restarts == [] and client.get("/api/engine/source").json()["active"] == baseline
    broken = client.put("/api/engine/source", json={"remote": "fake", "branch": "broken"})
    assert broken.status_code == 422 and broken.json()["error"]["code"] == "engine_unusable"
    app.state.workbench.engine.active_runs = lambda: 1
    busy = client.put("/api/engine/source", json={"remote": "fake", "branch": "feature"})
    assert busy.status_code == 409 and busy.json()["error"]["code"] == "runs_active"
    assert restarts == [] and not (tmp_path / "engines" / "active.json").exists()

    app.state.workbench.engine.active_runs = lambda: 0
    info = client.put("/api/engine/source", json={"remote": "fake", "branch": "feature"}).json()
    assert restarts == ["restart"] and info["usable"] and info["commit"] == commits["feature"]
    assert info["source"]["branch"] == "feature" and info["source"]["commit"] == commits["feature"]
    assert [d["code"] for d in info["diagnostics"]] == ["version_mismatch", "api_mismatch"]
    pending = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"})
    assert pending.status_code == 503 and pending.json()["error"]["code"] == "restart_pending"

    restarted = TestClient(create_app(tmp_path / "records"))  # what the re-executed service does at start
    assert restarted.get("/api/engine/source").json()["active"] == info["source"]
    assert os.environ["ACT_CODE_ROOT"] == info["act_root"]
    back = restarted.put("/api/engine/source", json={}).json()
    assert back["source"] == baseline and back["commit"] == CATALOG["act"]["commit"]
    assert not (tmp_path / "engines" / "active.json").exists()
    TestClient(create_app(tmp_path / "records"))
    assert "ACT_CODE_ROOT" not in os.environ

@pytest.mark.parametrize("url", [
    "file:///data1/guanqin/ACT", "ext::sh -c touch% /tmp/pwned", "http://github.com/o/ACT.git", "git@github.com:o/ACT.git",
    "ssh://github.com/o/ACT.git", "https://user:token@github.com/o/ACT.git", "https://github.com/../etc",
    "https://github.com/o/ACT.git?x=1", "https://localhost/o/ACT.git", "https://127.0.0.1/o/ACT.git", "--upload-pack=touch /tmp/pwned"])
def test_unsafe_repository_urls_are_rejected(client: TestClient, url: str):
    resp = client.get("/api/engine/branches", params={"url": url})
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "invalid_remote_url"
    switch = client.put("/api/engine/source", json={"url": url, "branch": "main"})
    assert switch.status_code == 422 and switch.json()["error"]["code"] == "invalid_remote_url"

def test_repository_url_names():
    assert engine_service.custom_remote(" https://GitHub.com/someone/ACT.git ") == (
        "github.com/someone/ACT", "https://GitHub.com/someone/ACT.git")
    assert engine_service.custom_remote("https://gitlab.example.org:8443/group/sub/act")[0] == "gitlab.example.org/group/sub/act"

def test_entered_repository_is_checked_then_offered_to_everyone(tmp_path: Path, monkeypatch):
    url, commits = fake_act_remote(tmp_path / "remote")
    monkeypatch.setenv("ACT_GUI_ACT_REMOTES", "")
    monkeypatch.delenv("ACT_CODE_ROOT", raising=False)
    # The synthetic remote is a local file:// repository; accept it in place of an https URL.
    monkeypatch.setattr(engine_service, "custom_remote", lambda u: ("example.org/someone/ACT", u))
    restarts: list[str] = []
    monkeypatch.setattr(engine_service, "restart_service", lambda: restarts.append("restart"))
    client = TestClient(create_app(tmp_path / "records"))
    assert client.get("/api/engine/source").json()["remotes"] == []
    assert client.get("/api/engine/branches", params={"url": url}).json() == {
        "remote": "example.org/someone/ACT", "url": url, "branches": ["broken", "feature"]}
    assert client.post("/api/engine/source/check", json={"url": url, "branch": "broken"}).json()["usable"] is False
    assert client.get("/api/engine/source").json()["remotes"] == []  # never imported as ACT: not offered
    checked = client.post("/api/engine/source/check", json={"url": url, "branch": "feature"}).json()
    assert checked["usable"] and checked["source"]["remote"] == "example.org/someone/ACT"
    offered = [{"name": "example.org/someone/ACT", "url": url, "custom": True}]
    assert TestClient(create_app(tmp_path / "records")).get("/api/engine/source").json()["remotes"] == offered
    info = client.put("/api/engine/source", json={"remote": "example.org/someone/ACT", "branch": "feature"}).json()
    assert restarts == ["restart"] and info["commit"] == commits["feature"]
    assert info["source"]["remote"] == "example.org/someone/ACT" and info["source"]["url"] == url
    TestClient(create_app(tmp_path / "records")).put("/api/engine/source", json={})

def test_remembered_repositories_keep_ten_newest_and_never_drop_guanqin(tmp_path: Path):
    remotes = {"guanqin-123": "https://github.com/guanqin-123/ACT.git"}
    engine = engine_service.EngineService("0" * 40, tmp_path / "secrets", tmp_path / "engines", remotes)
    url = lambda i: f"https://github.com/user{i}/ACT.git"  # noqa: E731
    stale = tmp_path / "engines" / hashlib.sha256(url(0).encode()).hexdigest()[:12] / ("a" * 40)
    stale.mkdir(parents=True)  # a staged checkout of the repository that will be evicted
    engine._remember("github.com/guanqin-123/ACT-fork", "https://github.com/guanqin-123/ACT-fork")
    for i in range(10):
        engine._remember(f"github.com/user{i}/ACT", url(i))
    engine._remember("github.com/user1/ACT", url(1))  # used again: now the newest
    engine._remember("github.com/user10/ACT", url(10))  # 11th unprotected one: user0 is the oldest
    names = [r.name for r in engine.sources().remotes if r.custom]
    assert names[:2] == ["github.com/user10/ACT", "github.com/user1/ACT"]
    assert "github.com/user0/ACT" not in names and len([n for n in names if "guanqin" not in n]) == 10
    assert "github.com/guanqin-123/ACT-fork" in names and not stale.parent.exists()

def test_operator_can_forbid_entered_repositories(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACT_GUI_ALLOW_CUSTOM_REMOTES", "0")
    client = TestClient(create_app(tmp_path / "records"))
    assert client.get("/api/engine/source").json()["custom_allowed"] is False
    resp = client.get("/api/engine/branches", params={"url": "https://github.com/someone/ACT.git"})
    assert resp.status_code == 403 and resp.json()["error"]["code"] == "custom_remotes_disabled"

def test_methods_and_runs_are_gated_on_checked_capabilities(client: TestClient):
    engine = cast(FastAPI, client.app).state.workbench.engine
    info = engine.info
    assert {c["capability"] for c in client.get("/api/engine").json()["api_checks"]} >= {"verify.bab", "fuzz.actfuzzer"}
    engine.__dict__["info"] = replace(info, capabilities=tuple(
        replace(c, availability="unsupported", source="API check failed: test") if c.name in ("verify.bab", "verify.dual")
        else c for c in info.capabilities))
    model = next(m for m in client.get("/api/models").json() if m["model_id"] == "range_check")
    assert "bab" not in model["methods"] and "interval" in model["methods"]
    assert client.post("/api/runs", json={"model_id": "range_check", "method": "bab"}).json()["error"]["code"] == "unsupported_method"
    dual = client.post("/api/runs", json={"model_id": "range_check", "method": "interval", "domain": "dual"})
    assert dual.status_code == 422 and dual.json()["error"]["code"] == "capability_unavailable"
    assert "verify.dual" in dual.json()["error"]["message"]

@pytest.mark.parametrize("content", ["hello world", "FOO=1\nBAR=2", "KEY=abc\n\x00bad=1", ""])
def test_non_license_uploads_are_rejected(client: TestClient, tmp_path: Path, content: str):
    resp = client.put("/api/solvers/gurobi/license", json={"content": content})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] in ("invalid_license_file", "invalid_request")
    assert not (tmp_path / "secrets" / "gurobi.lic").exists()
