"""Run worker: executes one ACT run in an isolated process (VER-02, VER-06).

Invoked by the workbench as:
    python -m visual_bench.verification.worker <request.json> <output.json> <progress_fd> [<control_fd>]
ACT writes diagnostics to stdout/stderr, so results go to <output.json>, never stdout.
Fuzzing progress goes as JSON lines to the inherited pipe <progress_fd>: {"progress": FuzzProgress}
or {"frame": FuzzFrame} (the latest mutated input, shown live and not recorded as an event).
Fuzz workers read {"action": "pause"|"resume"|"stop"|"update", "changes": {...}} on control_fd
and emit {"control": FuzzControlChange} / {"control_state": {"paused": bool}} on progress_fd.
Observer-capable verification sends {"propagation": index_entry}; complete tensors and history
are stored in the run directory before a throttled notification is sent.
SIGTERM is a stop request: a fuzz run ends after its current iteration and reports what it found;
other methods are killed by the supervisor instead.
The output always carries "diagnostics" (diagnostics.Capture): warnings, WARNING+ log records, and the
exception chain with its error location when the ACT call failed.
"""
from __future__ import annotations

import dataclasses
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import IO, Any


def _run(req: dict[str, Any], progress: IO[str], stop: threading.Event,
         control: Any = None, control_fd: int | None = None) -> dict[str, Any]:
    from engine_bridge.events import bab_summary
    from engine_bridge.execution import run_verification

    model = Path(req["model_path"])
    if req["method"] == "fuzz":
        from visual_bench.fuzzing import runner

        send_lock = threading.Lock()

        def send(kind: str, item: Any) -> None:
            value = dataclasses.asdict(item) if dataclasses.is_dataclass(item) else item
            with send_lock:
                progress.write(json.dumps({kind: value}) + "\n")
                progress.flush()

        return runner.run(model, req, send, stop, control, control_fd)
    from engine_bridge.contracts import DualOptions

    domain = req.get("domain") or "interval"
    dual = DualOptions(**req["dual"]) if req.get("dual") else None
    tolerance = float((req.get("hybridz") or {}).get("tolerance", 1e-7))
    layers: dict[str, Any] = {}
    if req["method"] == "interval" and req.get("record_propagation", False):
        from engine_bridge.contracts import BridgeError
        from engine_bridge.inspection import run_observed_verification
        from visual_bench.records.propagation import PropagationWriter

        start_ns = time.perf_counter_ns()

        def send_propagation(entry: dict[str, Any]) -> None:
            progress.write(json.dumps({"propagation": entry}, allow_nan=False) + "\n")
            progress.flush()

        writer = PropagationWriter(Path(req["record_directory"]), domain, send_propagation)
        outcome, sink = run_observed_verification(model, float(req["time_budget_s"]), domain, writer, start_ns,
                                                  dual, tolerance)
        writer.finish(sink.ignored_records)
        try:
            layers["layer_states"] = dataclasses.asdict(sink.layer_states(domain))
        except BridgeError as err:
            layers["layer_states_error"] = {"code": err.code, "message": err.message}
    else:
        outcome = run_verification(model, req["method"], float(req["time_budget_s"]), domain=domain, dual=dual,
                                   hybridz_tolerance=tolerance)
        if req["method"] == "interval":
            layers["propagation"] = {"domain": domain, "availability": "unavailable", "complete": True,
                                     "records": [], "phases": [], "ignored_records": 0}
    out: dict[str, Any] = {"outcome": dataclasses.asdict(outcome)}
    out.update(layers)
    if outcome.method == "bab":
        out["bab_summary"] = bab_summary(outcome.metadata)
    return out


def main(request_path: str, output_path: str, progress_fd: int, control_fd: int | None = None) -> int:
    stop = threading.Event()  # installed first, so a stop during ACT imports is still graceful
    control = None

    def request_stop(*_: Any) -> None:
        stop.set()
        if control is not None:
            control.request_stop()  # also wakes ACT while paused

    signal.signal(signal.SIGTERM, request_stop)
    from visual_bench.verification.diagnostics import Capture, default_roots, scrubber

    req = json.loads(Path(request_path).read_text())
    capture = Capture(scrubber(default_roots({"<run>": Path(request_path).parent,
                                               "<model-dir>": Path(req["model_path"]).parent})))
    with capture, os.fdopen(progress_fd, "w") as progress:
        from engine_bridge.contracts import BridgeError
        from engine_bridge.inspection import interval_layer_states

        try:
            if req["method"] == "fuzz":
                from engine_bridge.execution import FuzzRunControl

                control = FuzzRunControl()
                if stop.is_set():
                    control.request_stop()
            out = _run(req, progress, stop, control, control_fd)
            if "layer_states" in out or "layer_states_error" in out:
                pass  # Observed bounds belong to the run's own domain; never rerun interval analysis.
            elif not req.get("record_layers", True):
                out["layer_states_error"] = {"code": "capability_unavailable", "message":
                                             "The active ACT checkout fails the inspect.layer_bounds.interval API checks."}
            else:
                try:
                    out["layer_states"] = dataclasses.asdict(interval_layer_states(Path(req["model_path"])))
                except BridgeError as err:
                    out["layer_states_error"] = {"code": err.code, "message": err.message}
                except Exception as exc:  # e.g. CUDA OOM on a huge net: ACT's outcome above stands without them
                    out["layer_states_error"] = {"code": "unexpected_exception", "message": f"{type(exc).__name__}: {exc}"}
            if "layer_states_error" in out:
                capture.note("layer_states_" + out["layer_states_error"]["code"], out["layer_states_error"]["message"])
        except BridgeError as err:
            capture.exception(err)
            out = {"error": {"code": err.code, "message": err.message, "retryable": err.retryable}}
        except Exception as exc:  # an ACT or adapter fault the bridge did not map: report it with its traceback
            capture.exception(exc)
            out = {"error": {"code": "unexpected_exception", "message": f"{type(exc).__name__}: {exc}",
                             "retryable": False}}
    out["diagnostics"] = capture.report()
    tmp = Path(output_path + ".tmp")
    tmp.write_text(json.dumps(out))
    tmp.replace(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else None))
