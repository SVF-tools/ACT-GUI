"""Run lifecycle (VER-01..04, VER-07): start, supervise, stop, and read runs of every method.

- Start returns immediately; a thread supervises one worker process per run (worker.py).
- Idempotency: the same client_request_id with the same parameters returns the same run;
  with different parameters it is rejected.
- Records are the source of truth; run status is derived from committed events.
- Method-specific live output (fuzz frames) goes to a LiveObserver; this module stays method-neutral.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Protocol

from visual_bench.config import REPO_ROOT, requested_device
from visual_bench.engine.service import EngineService
from visual_bench.errors import AppError
from visual_bench.model_spec.schemas import NativeResult
from visual_bench.model_spec.service import ModelService
from visual_bench.records import RecordStore
from visual_bench.records.store import now_iso
from visual_bench.fuzzing.schemas import FuzzOptions
from visual_bench.verification import schemas as S
from visual_bench.wire import ErrorBody

WORKER_GRACE_S = 120.0
STOP_GRACE_S = 10.0  # a stopped fuzz worker finishes its current iteration within this, else it is killed


class LiveObserver(Protocol):
    def observe(self, run_id: str, msg: dict[str, Any]) -> tuple[str, dict[str, Any]] | None: ...

    def forget(self, run_id: str) -> None: ...


class RunService:
    def __init__(self, records: RecordStore, models: ModelService, engine: EngineService, live: LiveObserver) -> None:
        self.records = records
        self.models = models
        self.engine = engine
        self.live = live
        self._lock = threading.Lock()
        self._active: dict[str, threading.Thread] = {}
        self._procs: dict[str, subprocess.Popen[bytes]] = {}
        self._stop: dict[str, threading.Event] = {}
        self._recover_interrupted()

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

    # -- commands ------------------------------------------------------------
    def start(self, req: S.RunRequest) -> tuple[S.RunOut, bool]:
        """Return (run, created). Never waits for ACT."""
        entry = self.models.entry(req.model_id)
        methods = self.models.methods(entry)
        if req.method not in methods:
            raise AppError(422, "unsupported_method", f"{req.model_id} supports {methods}, not {req.method!r}")
        if req.method == "fuzz" and req.fuzz is None:
            req = req.model_copy(update={"fuzz": FuzzOptions()})
        if req.method == "interval" and req.domain is None:
            req = req.model_copy(update={"domain": "interval"})
        self.engine.require_engine()
        with self._lock:
            if req.client_request_id:
                existing = self._find_by_request_id(req.client_request_id)
                if existing:
                    if self.records.manifest(existing)["request"] != req.model_dump():
                        raise AppError(409, "idempotency_conflict",
                                       "client_request_id was already used with different parameters")
                    return self.get(existing), False
            path = self.models.path(req.model_id)
            run_id = "run-" + uuid.uuid4().hex[:12]
            env, license_source = self._worker_env()
            self.records.create(run_id, {
                "run_id": run_id, "created_at": now_iso(), "request": req.model_dump(),
                "model": {"act_path": entry["act_path"], "sha256": entry["sha256"]},
                "act": {"commit": self.engine.info.commit, "expected_commit": self.engine.expected_commit},
                "execution": {"requested_device": requested_device(), "gurobi_license": license_source},
            })
            self.records.append_event(run_id, "run.queued", "queued", {"method": req.method})
            t = threading.Thread(target=self._supervise, args=(run_id, path, req, env), daemon=True, name=run_id)
            self._active[run_id] = t
            self._stop[run_id] = threading.Event()
            t.start()
        return self.get(run_id), True

    def stop(self, run_id: str) -> S.RunOut:
        """Request a stop; idempotent, and a no-op on a terminal run."""
        run = self.get(run_id)
        with self._lock:
            ev = self._stop.get(run_id)
            if ev is None or ev.is_set() or run.status in ("completed", "failed"):
                return run
            ev.set()
            proc = self._procs.get(run_id)
        self.records.append_event(run_id, "run.stop_requested", run.status, {})
        if proc is not None:
            self._signal_stop(proc, run.method)
        return self.get(run_id)

    # -- worker supervision ----------------------------------------------------
    def _worker_env(self) -> tuple[dict[str, str], str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO_ROOT), env.get("PYTHONPATH")]))
        if requested_device() == "cpu":
            env["CUDA_VISIBLE_DEVICES"] = ""
        return env, self.engine.gurobi.worker_env(env)

    def _supervise(self, run_id: str, model_path: Path, req: S.RunRequest, env: dict[str, str]) -> None:
        try:
            with tempfile.TemporaryDirectory(prefix="act-gui-run-") as tmp:
                req_file, out_file, err_file = (Path(tmp) / n for n in ("request.json", "output.json", "stderr.txt"))
                req_file.write_text(json.dumps({"model_path": str(model_path), "method": req.method,
                                                "time_budget_s": req.time_budget_s, "domain": req.domain,
                                                "fuzz": req.fuzz.model_dump() if req.fuzz else None}))
                read_fd, write_fd = os.pipe()
                with open(err_file, "w") as stderr:
                    try:
                        proc = subprocess.Popen(
                            [sys.executable, "-m", "visual_bench.verification.worker", str(req_file), str(out_file),
                             str(write_fd)],
                            cwd=REPO_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=stderr, pass_fds=(write_fd,))
                    finally:
                        os.close(write_fd)
                    self.records.append_event(run_id, "run.started", "running", {"pid": proc.pid})
                    with self._lock:
                        self._procs[run_id] = proc
                        stop_requested = self._stop[run_id].is_set()
                    if stop_requested:  # stop arrived before the worker existed
                        self._signal_stop(proc, req.method)
                    killed = threading.Event()

                    def kill() -> None:
                        killed.set()
                        proc.kill()

                    timer = threading.Timer(req.time_budget_s + WORKER_GRACE_S, kill)
                    timer.start()
                    try:
                        with os.fdopen(read_fd) as progress:
                            for line in progress:  # ends at EOF: worker exited or was killed
                                event = self.live.observe(run_id, json.loads(line))
                                if event is not None:
                                    self.records.append_event(run_id, event[0], "running", event[1])
                        proc.wait()
                    finally:
                        timer.cancel()
                if self._stop[run_id].is_set() and (proc.returncode != 0 or not out_file.is_file()):
                    raise AppError(409, "stopped", "Stopped by the user before ACT returned a result.")
                if killed.is_set():
                    raise AppError(504, "worker_timeout", "Worker exceeded its budget plus grace period and was killed.")
                if proc.returncode != 0 or not out_file.is_file():
                    tail = err_file.read_text().strip().splitlines()[-3:]
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
            self.live.forget(run_id)
            with self._lock:
                self._active.pop(run_id, None)
                self._procs.pop(run_id, None)
                self._stop.pop(run_id, None)

    @staticmethod
    def _signal_stop(proc: subprocess.Popen[bytes], method: str) -> None:
        if method == "fuzz":  # the worker ends ACTFuzzer after the current iteration and reports it
            proc.send_signal(signal.SIGTERM)
            threading.Timer(STOP_GRACE_S, proc.kill).start()
        else:  # verify_once / BaB expose no stop hook: end the worker
            proc.kill()

    def _commit_result(self, run_id: str, out: dict[str, Any]) -> None:
        o = out["outcome"]
        result = {"verdict": o["verdict"], "act_status": o["act_status"], "elapsed_s": o["elapsed_s"],
                  "metadata": o["metadata"], "counterexample": o["counterexample"],
                  "bab_summary": out.get("bab_summary"), "device": o["device"]}
        self.records.write_artifact(run_id, "result.json", result)
        if "layer_states" in out:
            self.records.write_artifact(run_id, "layers.json", out["layer_states"])
        if "fuzzing" in out:
            self.records.write_artifact(run_id, "fuzzing.json", out["fuzzing"])
        hashes = self.records.seal(run_id)
        if result["bab_summary"] is not None:
            self.records.append_event(run_id, "bab.summary", "running", result["bab_summary"])
        self.records.append_event(run_id, "run.completed", "completed",
                                  {"verdict": result["verdict"], "result_sha256": hashes["result.json"]})

    # -- queries -----------------------------------------------------------------
    def request(self, run_id: str) -> S.RunRequest:
        return S.RunRequest.model_validate(self.records.manifest(run_id)["request"])

    def get(self, run_id: str) -> S.RunOut:
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
                status, error = "failed", ErrorBody(code="record_corrupt", message="result.json failed its hash check")
            else:
                result = S.RunResultOut.model_validate(raw)
        elif status == "failed" and last:
            error = ErrorBody(code=str(last["payload"].get("code")), message=str(last["payload"].get("message")))
        # Records written before domains existed are interval-domain verify_once runs.
        domain = req.domain or ("interval" if req.method == "interval" else None)
        # Native references were recorded with the default (interval) domain only.
        native_raw = None if domain not in (None, "interval") else self.models.native(req.model_id, req.method)
        native = NativeResult.model_validate(native_raw) if native_raw else None
        matches = None
        if result and native:
            matches = result.act_status == native.status
        return S.RunOut(run_id=run_id, model_id=req.model_id, method=req.method, domain=domain,
                        time_budget_s=req.time_budget_s,
                        client_request_id=req.client_request_id, status=status, created_at=m["created_at"],
                        started_at=started, finished_at=last["at"] if status in ("completed", "failed") and last else None,
                        model_sha256=m["model"]["sha256"], act_commit=m["act"]["commit"], result=result, error=error,
                        native_reference=native, matches_native=matches, last_seq=last["seq"] if last else 0)

    def list(self) -> S.RunList:
        return S.RunList(runs=[self.get(r) for r in self.records.run_ids()])
