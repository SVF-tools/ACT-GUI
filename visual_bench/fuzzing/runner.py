"""Fuzz method inside the run worker process: call ACTFuzzer through the bridge and shape the worker output.

Progress, frames, applied controls, and pause state go to `send` as JSON lines.
An inherited control pipe carries commands from the supervisor to a reader thread.
"""
from __future__ import annotations

import dataclasses
import json
import os
import select
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine_bridge.execution import FuzzRunControl

SUMMARY_KEYS = ("iterations", "counterexample_count", "neuron_coverage", "seeds_explored", "rng_seed", "stopped", "stop_reason")


def run(model: Path, req: dict[str, Any], send: Callable[[str, Any], None], stop: threading.Event,
        control: FuzzRunControl | None = None, control_fd: int | None = None) -> dict[str, Any]:
    from engine_bridge.execution import run_fuzzing, split_options

    control = control or FuzzRunControl()
    finished = threading.Event()

    def read_controls() -> None:
        # Read bytes instead of a buffered text iterator: select must see every queued line,
        # including several commands delivered by one write.
        pending = b""
        while not finished.is_set():
            ready, _, _ = select.select([control_fd], [], [], 0.1)
            if not ready:
                continue
            data = os.read(control_fd, 65536)
            if not data:
                return
            pending += data
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                command = json.loads(line)
                action = command["action"]
                if action == "update":
                    control.update(command["changes"])
                elif action == "stop":
                    stop.set()
                    control.request_stop()
                elif action in ("pause", "resume"):
                    getattr(control, action)()
                    send("control_state", {"paused": action == "pause"})

    reader = None
    if control_fd is not None:
        reader = threading.Thread(target=read_controls, name="fuzz-control", daemon=True)
        reader.start()
    run_args, hyperparameters = split_options(req["fuzz"])
    try:
        fz = run_fuzzing(model, float(req["time_budget_s"]), int(run_args["max_iterations"]),
                         rng_seed=int(run_args["rng_seed"]), stop_on_first=bool(run_args["stop_on_first"]),
                         hyperparameters=hyperparameters, on_progress=lambda p: send("progress", p),
                         on_frame=lambda fr: send("frame", fr), should_stop=stop.is_set,
                         control=control, on_control=lambda change: send("control", change))
    finally:
        finished.set()
        if reader is not None:
            reader.join()
        if control_fd is not None:
            os.close(control_fd)
    first = fz.counterexamples[0].input if fz.counterexamples else None
    return {
        "outcome": {"method": "fuzz", "verdict": fz.verdict, "act_status": fz.act_status, "elapsed_s": fz.elapsed_s,
                    "metadata": {k: getattr(fz, k) for k in SUMMARY_KEYS}, "counterexample": first,
                    "device": fz.device},
        "fuzzing": dataclasses.asdict(fz),
    }
