"""Application use cases shared by HTTP routes and the assistant (VER-01/02/03, first version).

- Catalog: real ACT models pinned by fixtures/catalog.json (commit + sha256).
- Runs: start returns immediately; a thread supervises one worker process per run.
- Idempotency: the same client_request_id with the same parameters returns the
  same run; with different parameters it is rejected.
- Records are the source of truth; run status is derived from committed events.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import uuid
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine_bridge.contracts import BridgeError, EngineInfo
from engine_bridge.engine_session import act_root, probe
from engine_bridge.events import observation_coverage
from engine_bridge.model_spec import describe_model, file_sha256
from visual_bench import schemas as S
from visual_bench.records import RecordStore
from visual_bench.records.store import now_iso
from visual_bench.verification.solver_license import GurobiLicense

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER_GRACE_S = 120.0


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


def _bridge_error(err: BridgeError, status: int = 422) -> AppError:
    return AppError(status, err.code, err.message, err.retryable)


class Workbench:
    def __init__(self, records_root: Path, catalog_path: Path | None = None, secrets_root: Path | None = None) -> None:
        self.catalog_path = catalog_path or REPO_ROOT / "fixtures" / "catalog.json"
        self.catalog = json.loads(self.catalog_path.read_text())
        self.records = RecordStore(records_root)
        self.gurobi = GurobiLicense(secrets_root or records_root.parent / "secrets")
        self._lock = threading.Lock()
        self._active: dict[str, threading.Thread] = {}
        self._recover_interrupted()

    # -- engine ------------------------------------------------------------
    @property
    def expected_commit(self) -> str:
        return self.catalog["act"]["commit"]

    @lru_cache(maxsize=1)
    def engine(self) -> EngineInfo:
        return probe(self.expected_commit)

    def engine_out(self) -> S.EngineInfoOut:
        e = self.engine()
        d = asdict(e)
        d["usable"] = e.usable
        return S.EngineInfoOut.model_validate(d)

    def _require_engine(self) -> None:
        e = self.engine()
        if not e.usable:
            first = next(d for d in e.diagnostics if d.severity == "error")
            raise AppError(503, first.code, first.message)

    # -- catalog / descriptions -------------------------------------------
    def _model_entry(self, model_id: str) -> dict[str, Any]:
        for m in self.catalog["models"]:
            if m["id"] == model_id:
                return m
        raise AppError(404, "model_not_found", f"Unknown model_id {model_id!r}")

    def model_path(self, model_id: str) -> Path:
        entry = self._model_entry(model_id)
        path = act_root() / entry["act_path"]
        if not path.is_file():
            raise AppError(503, "model_missing", f"{entry['act_path']} is missing from the ACT checkout")
        if file_sha256(path) != entry["sha256"]:
            raise AppError(409, "snapshot_mismatch", f"{entry['act_path']} does not match the pinned sha256")
        return path

    def models(self) -> list[S.ModelSummary]:
        return [S.ModelSummary(model_id=m["id"], description=m["description"], act_path=m["act_path"],
                               sha256=m["sha256"], methods=m["methods"], native=m["native"])
                for m in self.catalog["models"]]

    def describe(self, model_id: str) -> S.ModelDescriptionOut:
        self._require_engine()
        return self._describe_cached(model_id)

    @lru_cache(maxsize=32)
    def _describe_cached(self, model_id: str) -> S.ModelDescriptionOut:
        path = self.model_path(model_id)
        try:
            d = describe_model(path)
        except BridgeError as err:
            raise _bridge_error(err) from err
        raw = asdict(d)
        for spec in raw["input_specs"]:
            spec["lb"] = [S.wire_number(x) for x in spec["lb"]]
            spec["ub"] = [S.wire_number(x) for x in spec["ub"]]
        if raw["output_spec"] and raw["output_spec"]["thresholds"] is not None:
            raw["output_spec"]["thresholds"] = [S.wire_number(x) for x in raw["output_spec"]["thresholds"]]
        raw.pop("source_path")
        return S.ModelDescriptionOut(model_id=model_id, act_commit=self.engine().commit, **raw)

    # -- runs ----------------------------------------------------------------
    def _recover_interrupted(self) -> None:
        for run_id in self.records.run_ids():
            evs = self.records.events(run_id)
            if not evs or evs[-1]["status"] not in ("completed", "failed"):
                self.records.append_event(run_id, "run.failed", "failed",
                                          {"code": "interrupted", "message": "Service stopped before the run finished."})

    def _find_by_request_id(self, client_request_id: str) -> str | None:
        for run_id in self.records.run_ids():
            if self.records.manifest(run_id)["request"].get("client_request_id") == client_request_id:
                return run_id
        return None

    def start_run(self, req: S.RunRequest) -> tuple[S.RunOut, bool]:
        """Return (run, created). Never waits for ACT."""
        entry = self._model_entry(req.model_id)
        if req.method not in entry["methods"]:
            raise AppError(422, "unsupported_method", f"{req.model_id} supports {entry['methods']}, not {req.method!r}")
        self._require_engine()
        with self._lock:
            if req.client_request_id:
                existing = self._find_by_request_id(req.client_request_id)
                if existing:
                    if self.records.manifest(existing)["request"] != req.model_dump():
                        raise AppError(409, "idempotency_conflict",
                                       "client_request_id was already used with different parameters")
                    return self.get_run(existing), False
            path = self.model_path(req.model_id)
            run_id = "run-" + uuid.uuid4().hex[:12]
            env, license_source = self._worker_env()
            self.records.create(run_id, {
                "run_id": run_id, "created_at": now_iso(), "request": req.model_dump(),
                "model": {"act_path": entry["act_path"], "sha256": entry["sha256"]},
                "act": {"commit": self.engine().commit, "expected_commit": self.expected_commit},
                "execution": {"requested_device": self.requested_device, "gurobi_license": license_source},
            })
            self.records.append_event(run_id, "run.queued", "queued", {"method": req.method})
            t = threading.Thread(target=self._supervise, args=(run_id, path, req, env), daemon=True, name=run_id)
            self._active[run_id] = t
            t.start()
        return self.get_run(run_id), True

    @property
    def requested_device(self) -> str:
        return os.environ.get("ACT_GUI_DEVICE", "cpu")

    def _worker_env(self) -> tuple[dict[str, str], str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO_ROOT), env.get("PYTHONPATH")]))
        if self.requested_device == "cpu":
            env["CUDA_VISIBLE_DEVICES"] = ""
        return env, self.gurobi.worker_env(env)

    def _supervise(self, run_id: str, model_path: Path, req: S.RunRequest, env: dict[str, str]) -> None:
        try:
            with tempfile.TemporaryDirectory(prefix="act-gui-run-") as tmp:
                req_file, out_file = Path(tmp) / "request.json", Path(tmp) / "output.json"
                req_file.write_text(json.dumps({"model_path": str(model_path), "method": req.method,
                                                "time_budget_s": req.time_budget_s}))
                proc = subprocess.Popen([sys.executable, "-m", "visual_bench.verification.worker", str(req_file), str(out_file)],
                                        cwd=REPO_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                self.records.append_event(run_id, "run.started", "running", {"pid": proc.pid})
                try:
                    _, stderr = proc.communicate(timeout=req.time_budget_s + WORKER_GRACE_S)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                    raise AppError(504, "worker_timeout", "Worker exceeded its budget plus grace period and was killed.")
                if proc.returncode != 0 or not out_file.is_file():
                    tail = (stderr or "").strip().splitlines()[-3:]
                    raise AppError(500, "worker_crashed", f"Worker exited with code {proc.returncode}: {' | '.join(tail)}")
                out = json.loads(out_file.read_text())
            if "error" in out:
                raise AppError(422, out["error"]["code"], out["error"]["message"])
            self._commit_result(run_id, out)
        except AppError as err:
            self.records.append_event(run_id, "run.failed", "failed", {"code": err.code, "message": err.message})
        except Exception as exc:  # unexpected supervisor fault: still a visible, explicit failure
            self.records.append_event(run_id, "run.failed", "failed", {"code": "supervisor_error", "message": repr(exc)})
        finally:
            with self._lock:
                self._active.pop(run_id, None)

    def _commit_result(self, run_id: str, out: dict[str, Any]) -> None:
        o = out["outcome"]
        result = {"verdict": o["verdict"], "act_status": o["act_status"], "elapsed_s": o["elapsed_s"],
                  "metadata": o["metadata"], "counterexample": o["counterexample"],
                  "bab_summary": out.get("bab_summary"), "device": o["device"]}
        self.records.write_artifact(run_id, "result.json", result)
        if "layer_states" in out:
            self.records.write_artifact(run_id, "layers.json", out["layer_states"])
        hashes = self.records.seal(run_id)
        if result["bab_summary"] is not None:
            self.records.append_event(run_id, "bab.summary", "running", result["bab_summary"])
        self.records.append_event(run_id, "run.completed", "completed",
                                  {"verdict": result["verdict"], "result_sha256": hashes["result.json"]})

    def get_run(self, run_id: str) -> S.RunOut:
        if not self.records.exists(run_id):
            raise AppError(404, "run_not_found", f"Unknown run {run_id!r}")
        m = self.records.manifest(run_id)
        evs = self.records.events(run_id)
        req = S.RunRequest.model_validate(m["request"])
        started = next((e["at"] for e in evs if e["kind"] == "run.started"), None)
        last = evs[-1] if evs else None
        status = last["status"] if last else "queued"
        result = error = None
        if status == "completed":
            raw = self.records.artifact(run_id, "result.json")
            if raw is None:
                status, error = "failed", S.ErrorBody(code="record_corrupt", message="result.json failed its hash check")
            else:
                result = S.RunResultOut.model_validate(raw)
        elif status == "failed" and last:
            error = S.ErrorBody(code=str(last["payload"].get("code")), message=str(last["payload"].get("message")))
        native_raw = self._model_entry(req.model_id)["native"].get(req.method)
        native = S.NativeResult.model_validate(native_raw) if native_raw else None
        matches = None
        if result and native:
            matches = result.act_status == native.status
        return S.RunOut(run_id=run_id, model_id=req.model_id, method=req.method, time_budget_s=req.time_budget_s,
                        client_request_id=req.client_request_id, status=status, created_at=m["created_at"],
                        started_at=started, finished_at=last["at"] if status in ("completed", "failed") and last else None,
                        model_sha256=m["model"]["sha256"], act_commit=m["act"]["commit"], result=result, error=error,
                        native_reference=native, matches_native=matches, last_seq=last["seq"] if last else 0)

    def list_runs(self) -> S.RunList:
        return S.RunList(runs=[self.get_run(r) for r in self.records.run_ids()])

    def layer_states(self, run_id: str) -> S.LayerStatesOut:
        run = self.get_run(run_id)
        if run.status != "completed":
            return S.LayerStatesOut(run_id=run_id, availability="pending" if run.status != "failed" else "not_recorded",
                                    method=None, layers=[], provenance={})
        raw = self.records.artifact(run_id, "layers.json")
        if raw is None:
            return S.LayerStatesOut(run_id=run_id, availability="not_recorded", method=None, layers=[], provenance={})
        layers = [S.LayerStateOut(layer_id=l["layer_id"], kind=l["kind"], stage=l["stage"], shape=l["shape"],
                                  lb=[S.wire_number(x) for x in l["lb"]], ub=[S.wire_number(x) for x in l["ub"]],
                                  before_layer_ids=l["before_layer_ids"]) for l in raw["layers"]]
        prov = dict(raw.get("provenance", {}))
        prov["recorded"] = "computed by the run worker on the run's pinned model snapshot"
        return S.LayerStatesOut(run_id=run_id, availability=raw["availability"], method=raw["method"], layers=layers,
                                provenance=prov)

    def coverage(self, run_id: str) -> S.CoverageOut:
        run = self.get_run(run_id)
        cov = observation_coverage()
        summary = run.result.bab_summary if run.result else None
        return S.CoverageOut(run_id=run_id, node_events=cov["node_events"], wave_events=cov["wave_events"],
                             final_summary="available" if summary is not None else
                             ("pending" if run.status in ("queued", "running") else "not_recorded"),
                             reason=cov["reason"], summary=summary)

    def is_terminal(self, run_id: str) -> bool:
        return self.get_run(run_id).status in ("completed", "failed")
