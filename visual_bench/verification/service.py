"""Run lifecycle (VER-01..04, VER-07): start, supervise, stop, and read runs of every method.

- Start returns immediately; a thread supervises one worker process per run (worker.py).
- Idempotency: the same client_request_id with the same parameters returns the same run;
  with different parameters it is rejected.
- Records are the source of truth; run status is derived from committed events.
- Method-specific live output (fuzz frames) goes to a LiveObserver; this module stays method-neutral.
- Every run that reaches a worker leaves diagnostics (diagnostics.py) before its terminal event: the
  worker's warnings, logs and error location, ACT's stdout/stderr, and the engine it ran on.
"""
from __future__ import annotations

import json
import logging
import math
import os
import signal
import subprocess
import sys
import tempfile
import threading
import traceback
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from engine_bridge.contracts import DISPLAY_VALUES
from engine_bridge.execution import required_capability
from visual_bench.config import REPO_ROOT, requested_device
from visual_bench.engine.service import EngineService
from visual_bench.errors import AppError
from visual_bench.model_spec.schemas import NativeResult
from visual_bench.model_spec.service import ModelService
from visual_bench.records import RecordStore
from visual_bench.records.store import now_iso
from visual_bench.fuzzing.schemas import FuzzOptions
from visual_bench.verification import diagnostics as D
from visual_bench.verification import schemas as S
from visual_bench.wire import ErrorBody

log = logging.getLogger(__name__)

WORKER_GRACE_S = 120.0
# The worker loads the ACT net before ACT's budget starts; its deadline adds this much per byte of the net file.
# Conservative JSON parse rate: the 1.9 GB smart_turn_multimodal_2026 net loads in about 100 s.
LOAD_BYTES_PER_S = 10e6
SAVED = "saved_counterexamples.json"  # run annotation shared with the fuzzing module (user-saved counterexamples)
STOP_GRACE_S = 10.0  # a stopped fuzz worker finishes its current iteration within this, else it is killed


def vnncomp_sat(x: list[float], y: list[float], x_shape: list[int]) -> str:
    """A counterexample as a VNN-COMP result: "sat" plus the VNN-LIB 2.0 command-line assignment.

    VNN-LIB 2.0 (Sec. 5.3.1): per declared variable, "<name> <type> [<dims>]" then one value per line in
    row-major order. Variables are the conventional X (input, shaped like the input spec) and Y (output,
    [1, n]); the element type is float64 because ACT computed and checked the counterexample in float64.
    """
    def header(name: str, shape: list[int]) -> str:
        return f"{name} float64 [{','.join(str(d) for d in shape)}]"

    return "\n".join(["sat", header("X", x_shape), *map(repr, x), header("Y", [1, len(y)]), *map(repr, y)]) + "\n"


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

    @staticmethod
    def defaults() -> S.VerifyDefaults:
        return S.VerifyDefaults(dual=S.DualOptions(), hybridz=S.HybridzOptions())

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
        if req.domain == "dual" and req.dual is None:
            req = req.model_copy(update={"dual": S.DualOptions()})
        if req.domain == "hybridz" and req.hybridz is None:
            req = req.model_copy(update={"hybridz": S.HybridzOptions()})
        self.engine.require_capability(required_capability(req.method, req.domain))
        if req.dual is not None and req.dual != S.DualOptions():
            self.engine.require_capability("verify.dual.options")
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
                "act": {"commit": self.engine.info.commit, "expected_commit": self.engine.expected_commit,
                        "source": self.engine.source.model_dump()},
                "execution": {"requested_device": requested_device(), "gurobi_license": license_source},
            })
            self.records.append_event(run_id, "run.queued", "queued", {"method": req.method})
            context = {"engine": self._engine_snapshot(),
                       "environment": {"requested_device": requested_device(), "gurobi_license": license_source,
                                       "cuda_visible_devices": env.get("CUDA_VISIBLE_DEVICES")}}
            t = threading.Thread(target=self._supervise, args=(run_id, path, req, env, context), daemon=True,
                                 name=run_id)
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

    def _engine_snapshot(self) -> dict[str, Any]:
        """The ACT engine a run is started on, frozen into its diagnostics."""
        info, scrub = self.engine.info, D.scrubber(D.default_roots())
        return {"commit": info.commit, "expected_commit": info.expected_commit, "tracked_changes": info.tracked_changes,
                "act_root": scrub(info.act_root), "python": info.python, "torch": info.torch,
                "cuda_available": info.cuda_available, "source": self.engine.source.model_dump(),
                "capabilities": {c.name: c.availability for c in info.capabilities},
                "diagnostics": [asdict(d) for d in info.diagnostics],
                "failing_api_checks": [{**asdict(c), "detail": scrub(c.detail)} for c in info.api_checks if not c.ok]}

    def _supervise(self, run_id: str, model_path: Path, req: S.RunRequest, env: dict[str, str],
                   context: dict[str, Any]) -> None:
        captured: dict[str, Any] = {**context, "worker": None, "process": None}
        try:
            with tempfile.TemporaryDirectory(prefix="act-gui-run-") as tmp:
                req_file, out_file, err_file, std_file = (
                    Path(tmp) / n for n in ("request.json", "output.json", "stderr.txt", "stdout.txt"))
                worker_req = {"model_path": str(model_path), "method": req.method,
                              "time_budget_s": req.time_budget_s, "domain": req.domain,
                              "dual": req.dual.model_dump() if req.dual else None,
                              "hybridz": req.hybridz.model_dump() if req.hybridz else None,
                              "record_layers": self.engine.capability_available("inspect.layer_bounds.interval"),
                              "record_propagation": self.engine.capability_available("observe.propagation"),
                              "record_directory": str(self.records.run_dir(run_id).resolve()),
                              "fuzz": req.fuzz.model_dump() if req.fuzz else None}
                req_file.write_text(json.dumps(worker_req))
                captured["request"] = {**worker_req, "model_path": f"model/{req.model_id}.json",
                                       "record_directory": "reproduced_records"}
                captured["tmp"] = tmp
                read_fd, write_fd = os.pipe()
                with open(err_file, "w") as stderr, open(std_file, "w") as stdout:
                    try:
                        proc = subprocess.Popen(
                            [sys.executable, "-m", "visual_bench.verification.worker", str(req_file), str(out_file),
                             str(write_fd)],
                            cwd=REPO_ROOT, env=env, stdout=stdout, stderr=stderr, pass_fds=(write_fd,))
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

                    load_s = model_path.stat().st_size / LOAD_BYTES_PER_S
                    timer = threading.Timer(req.time_budget_s + WORKER_GRACE_S + load_s, kill)
                    timer.start()
                    try:
                        with os.fdopen(read_fd) as progress:
                            for line in progress:  # ends at EOF: worker exited or was killed
                                msg = json.loads(line)
                                event = (("verify.propagation", msg["propagation"]) if "propagation" in msg
                                         else self.live.observe(run_id, msg))
                                if event is not None:
                                    self.records.append_event(run_id, event[0], "running", event[1])
                        proc.wait()
                    finally:
                        timer.cancel()
                out = json.loads(out_file.read_text()) if out_file.is_file() else None
                scrub = D.scrubber(D.default_roots({"<run>": tmp, "<model-dir>": model_path.parent}))
                captured["worker"] = (out or {}).pop("diagnostics", None)
                captured["process"] = {"exit_code": proc.returncode, "killed_at_deadline": killed.is_set(),
                                       "stop_requested": self._stop[run_id].is_set()}
                captured["logs"], captured["printed"] = {}, []
                for src, name in ((std_file, "act_stdout.log"), (err_file, "worker_stderr.log")):
                    text, captured["logs"][name] = D.log_tail(src, scrub)
                    captured["printed"] += D.printed_problems(text, name)
                    self.records.write_diagnostic(run_id, name, text.encode())
                if self._stop[run_id].is_set() and (proc.returncode != 0 or out is None):
                    raise AppError(409, "stopped", "Stopped by the user before ACT returned a result.")
                if killed.is_set():
                    raise AppError(504, "worker_timeout", "Worker exceeded its budget plus grace period and was killed.")
                if proc.returncode != 0 or out is None:
                    tail = err_file.read_text().strip().splitlines()[-3:]
                    raise AppError(500, "worker_crashed", f"Worker exited with code {proc.returncode}: {' | '.join(tail)}")
            if "error" in out:
                raise AppError(422, out["error"]["code"], out["error"]["message"])
            self._write_diagnostics(run_id, captured, None)
            self._commit_result(run_id, out)
        except AppError as err:
            self._write_diagnostics(run_id, captured, {"code": err.code, "message": err.message})
            self.records.append_event(run_id, "run.failed", "failed", {"code": err.code, "message": err.message})
        except Exception as exc:  # unexpected supervisor fault: still a visible, explicit failure
            captured["supervisor_traceback"] = traceback.format_exc()
            self._write_diagnostics(run_id, captured, {"code": "supervisor_error", "message": repr(exc)})
            self.records.append_event(run_id, "run.failed", "failed", {"code": "supervisor_error", "message": repr(exc)})
        finally:
            self.live.forget(run_id)
            with self._lock:
                self._active.pop(run_id, None)
                self._procs.pop(run_id, None)
                self._stop.pop(run_id, None)

    def _write_diagnostics(self, run_id: str, captured: dict[str, Any], failure: dict[str, str] | None) -> None:
        """Write diagnostics.json; a failure here is logged and never blocks the run's terminal event."""
        try:
            scrub = D.scrubber(D.default_roots({"<run>": captured.pop("tmp", None),
                                                "<records>": self.records.root, "<models>": self.models.models_root}))
            if "supervisor_traceback" in captured:
                captured["supervisor_traceback"] = scrub(captured["supervisor_traceback"])
            diag = {"version": D.DIAGNOSTICS_VERSION, "run_id": run_id, "captured_at": now_iso(),
                    "failure": failure and {**failure, "message": scrub(failure["message"])}, **captured}
            diag["summary"] = D.summary(diag)
            self.records.write_diagnostic(run_id, "diagnostics.json", json.dumps(diag, indent=2, default=str).encode())
        except Exception:
            log.exception("could not record diagnostics of %s", run_id)

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
                  "bab_summary": out.get("bab_summary"), "device": o["device"],
                  "rows": o.get("rows") or [], "counterexample_row": o.get("counterexample_row"),
                  "counterexample_output": o.get("counterexample_output"),
                  "counterexample_output_error": o.get("counterexample_output_error")}
        self.records.write_artifact(run_id, "result.json", result)
        if "layer_states" in out:
            self.records.write_artifact(run_id, "layers.json", out["layer_states"])
        if "fuzzing" in out:
            self.records.write_artifact(run_id, "fuzzing.json", out["fuzzing"])
        if "propagation" in out:
            self.records.write_artifact(run_id, "propagation.json", out["propagation"])
        hashes = self.records.seal(run_id)
        if result["bab_summary"] is not None:
            self.records.append_event(run_id, "bab.summary", "running", result["bab_summary"])
        self.records.append_event(run_id, "run.completed", "completed",
                                  {"verdict": result["verdict"], "result_sha256": hashes["result.json"]})

    # -- queries -----------------------------------------------------------------
    def request(self, run_id: str) -> S.RunRequest:
        return S.RunRequest.model_validate(self.records.manifest(run_id)["request"])

    def get(self, run_id: str, *, full: bool = False) -> S.RunOut:
        """A run; counterexample inputs above DISPLAY_VALUES values are None unless `full` (save reads them)."""
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
                if not full:
                    result = _displayable(result)
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
        diag = self.records.diagnostics(run_id)
        diagnostics = S.RunDiagnosticsOut.model_validate(diag["summary"]) if diag and "summary" in diag else None
        saved = [] if req.method == "fuzz" else self.records.annotation(run_id, SAVED) or []
        return S.RunOut(run_id=run_id, model_id=req.model_id, method=req.method, domain=domain, diagnostics=diagnostics,
                        dual=req.dual, hybridz=req.hybridz,
                        time_budget_s=req.time_budget_s,
                        client_request_id=req.client_request_id, status=status, created_at=m["created_at"],
                        started_at=started, finished_at=last["at"] if status in ("completed", "failed") and last else None,
                        model_sha256=m["model"]["sha256"], act_commit=m["act"]["commit"], result=result, error=error,
                        native_reference=native, matches_native=matches, last_seq=last["seq"] if last else 0,
                        counterexample_saved_at=next((e["saved_at"] for e in saved), None),
                        saved_counterexample_rows=[e["counterexample"]["row"] for e in saved])

    # -- saved counterexamples (user annotations on a verification run; ACT decided the violation) ----------
    @staticmethod
    def _row_counterexample(r: S.RunResultOut | None, row: int | None) -> tuple[int, list[float], list[float] | None, str | None] | None:
        """(row, input, output, output error) of ACT's counterexample on a batch row; None (no row) means the run's
        summary counterexample. Single-row nets and runs recorded before per-row counterexamples use the summary."""
        if r is None:
            return None
        summary = r.counterexample_row or 0
        if r.counterexample is not None and (row is None or row == summary):
            return summary, r.counterexample, r.counterexample_output, r.counterexample_output_error
        lane = next((x for x in r.rows if x.row == row and x.counterexample is not None), None)
        return None if lane is None else (lane.row, lane.counterexample, lane.counterexample_output,
                                          lane.counterexample_output_error)

    def save_counterexample(self, run_id: str, row: int | None = None) -> tuple[S.RunOut, bool]:
        """Save ACT's counterexample of a verify_once/BaB run (of batch row `row`; default: the summary one) on its
        record; saving the same row again is a no-op."""
        run = self.get(run_id, full=True)
        if run.method == "fuzz":
            raise AppError(422, "unsupported_method", "Fuzz runs save counterexamples by index (saved-counterexamples).")
        ce = self._row_counterexample(run.result, row)
        if ce is None:
            where = "" if row is None else f" on row {row}"
            raise AppError(404, "counterexample_not_found", f"ACT reported no counterexample{where} for {run_id}")
        with self._lock:
            saved = self.records.annotation(run_id, SAVED) or []
            created = all(e["counterexample"]["row"] != ce[0] for e in saved)
            if created:
                self.records.write_annotation(run_id, SAVED, [*saved, {"saved_at": now_iso(), "counterexample": {
                    "row": ce[0], "input": ce[1], "output": ce[2]}}])
        return self.get(run_id), created

    def saved_counterexample_file(self, run_id: str, row: int | None = None) -> str:
        """A saved counterexample (of batch row `row`; default: the first saved) as a VNN-COMP witness (see
        vnncomp_sat); X takes one input row's shape."""
        run = self.get(run_id)
        saved = self.records.annotation(run_id, SAVED) if run.method != "fuzz" else None
        entry = next((e for e in saved or [] if row is None or e["counterexample"]["row"] == row), None)
        if entry is None:
            where = "" if row is None else f" for row {row}"
            raise AppError(404, "counterexample_not_saved", f"No counterexample{where} is saved on {run_id}")
        ce = entry["counterexample"]
        if ce["output"] is None:
            found = self._row_counterexample(run.result, ce["row"])
            reason = found[3] if found else None
            raise AppError(422, "output_unavailable", "The network output at this counterexample could not be computed, "
                           f"so it has no VNN-COMP witness: {reason or 'not recorded'}")
        specs = self.models.describe(run.model_id).input_specs
        shape = [1, *specs[0].shape[1:]] if specs and specs[0].shape else [1, len(ce["input"])]
        return vnncomp_sat(ce["input"], ce["output"], shape if math.prod(shape) == len(ce["input"]) else [1, len(ce["input"])])

    # -- reproduction snapshot -------------------------------------------------------------------------
    def snapshot(self, run_id: str) -> bytes:
        """Zip of everything needed to replay a finished run's ACT call (see diagnostics.snapshot_zip)."""
        run = self.get(run_id)
        if run.status not in ("completed", "failed"):
            raise AppError(409, "run_active", "A snapshot is taken once the run has finished.")
        manifest = self.records.manifest(run_id)
        entry = self.models.entry(run.model_id)
        model_file, note = None, None
        try:
            model_file = self.models.path(run.model_id)
            if run.model_sha256 != entry["sha256"]:
                model_file, note = None, f"the model now has sha256 {entry['sha256']}, not the run's {run.model_sha256}"
        except AppError as err:
            note = f"not included ({err.code}: {err.message})"
        return D.snapshot_zip(run_id, self.records.run_dir(run_id), manifest, run.status,
                              run.error.model_dump() if run.error else None, self.records.diagnostics(run_id),
                              model_file, entry, note)

    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def list(self) -> S.RunList:
        return S.RunList(runs=[self.get(r) for r in self.records.run_ids()])


def _displayable(r: S.RunResultOut) -> S.RunResultOut:
    """The result with counterexample inputs above DISPLAY_VALUES values omitted (records keep them)."""
    def shown(xs: list[float] | None) -> list[float] | None:
        return None if xs is None or len(xs) > DISPLAY_VALUES else xs
    return r.model_copy(update={"counterexample": shown(r.counterexample),
                                "rows": [x.model_copy(update={"counterexample": shown(x.counterexample)}) for x in r.rows]})
