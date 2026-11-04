"""Fuzz method inside the run worker process: call ACTFuzzer through the bridge and shape the worker output.

Progress points and frames go to `send` as {"progress": ...} / {"frame": ...} JSON lines.
"""
from __future__ import annotations

import dataclasses
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

SUMMARY_KEYS = ("iterations", "counterexample_count", "neuron_coverage", "seeds_explored", "rng_seed", "stopped")


def run(model: Path, req: dict[str, Any], send: Callable[[str, Any], None], stop: threading.Event) -> dict[str, Any]:
    from engine_bridge.execution import run_fuzzing, split_options

    run_args, hyperparameters = split_options(req["fuzz"])
    fz = run_fuzzing(model, float(req["time_budget_s"]), int(run_args["max_iterations"]),
                     rng_seed=int(run_args["rng_seed"]), stop_on_first=bool(run_args["stop_on_first"]),
                     hyperparameters=hyperparameters, on_progress=lambda p: send("progress", p),
                     on_frame=lambda fr: send("frame", fr), should_stop=stop.is_set)
    first = fz.counterexamples[0].input if fz.counterexamples else None
    return {
        "outcome": {"method": "fuzz", "verdict": fz.verdict, "act_status": fz.act_status, "elapsed_s": fz.elapsed_s,
                    "metadata": {k: getattr(fz, k) for k in SUMMARY_KEYS}, "counterexample": first,
                    "device": fz.device},
        "fuzzing": dataclasses.asdict(fz),
    }
