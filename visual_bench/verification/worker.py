"""Run worker: executes one ACT run in an isolated process (VER-02, VER-06).

Invoked by the workbench as:
    python -m visual_bench.verification.worker <request.json> <output.json> <progress_fd>
ACT writes diagnostics to stdout/stderr, so results go to <output.json>, never stdout.
Fuzzing progress goes as JSON lines to the inherited pipe <progress_fd>: {"progress": FuzzProgress}
or {"frame": FuzzFrame} (the latest mutated input, shown live and not recorded as an event).
SIGTERM is a stop request: a fuzz run ends after its current iteration and reports what it found;
other methods are killed by the supervisor instead.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from typing import IO, Any


def _run(req: dict[str, Any], progress: IO[str], stop: threading.Event) -> dict[str, Any]:
    from engine_bridge.events import bab_summary
    from engine_bridge.execution import run_verification

    model = Path(req["model_path"])
    if req["method"] == "fuzz":
        from visual_bench.fuzzing import runner

        def send(kind: str, item: Any) -> None:
            progress.write(json.dumps({kind: dataclasses.asdict(item)}) + "\n")
            progress.flush()

        return runner.run(model, req, send, stop)
    outcome = run_verification(model, req["method"], float(req["time_budget_s"]),
                               domain=req.get("domain") or "interval")
    out: dict[str, Any] = {"outcome": dataclasses.asdict(outcome)}
    if outcome.method == "bab":
        out["bab_summary"] = bab_summary(outcome.metadata)
    return out


def main(request_path: str, output_path: str, progress_fd: int) -> int:
    stop = threading.Event()  # installed first, so a stop during ACT imports is still graceful
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    from engine_bridge.contracts import BridgeError
    from engine_bridge.inspection import interval_layer_states

    logging.disable(logging.WARNING)
    req = json.loads(Path(request_path).read_text())
    with os.fdopen(progress_fd, "w") as progress:
        try:
            out = _run(req, progress, stop)
            if not req.get("record_layers", True):
                out["layer_states_error"] = {"code": "capability_unavailable", "message":
                                             "The active ACT checkout fails the inspect.layer_bounds.interval API checks."}
            else:
                try:
                    out["layer_states"] = dataclasses.asdict(interval_layer_states(Path(req["model_path"])))
                except BridgeError as err:
                    out["layer_states_error"] = {"code": err.code, "message": err.message}
        except BridgeError as err:
            out = {"error": {"code": err.code, "message": err.message, "retryable": err.retryable}}
    tmp = Path(output_path + ".tmp")
    tmp.write_text(json.dumps(out))
    tmp.replace(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], int(sys.argv[3])))
