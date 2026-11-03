"""Run worker: executes one ACT run in an isolated process (VER-02).

Invoked by the workbench as:  python -m visual_bench.verification.worker <request.json> <output.json>
ACT writes diagnostics to stdout/stderr, so results go to <output.json>, never stdout.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import sys
from pathlib import Path


def main(request_path: str, output_path: str) -> int:
    from engine_bridge.contracts import BridgeError
    from engine_bridge.events import bab_summary
    from engine_bridge.execution import run_verification
    from engine_bridge.inspection import interval_layer_states

    logging.disable(logging.WARNING)
    req = json.loads(Path(request_path).read_text())
    model = Path(req["model_path"])
    try:
        outcome = run_verification(model, req["method"], float(req["time_budget_s"]))
        out: dict = {"outcome": dataclasses.asdict(outcome)}
        if outcome.method == "bab":
            out["bab_summary"] = bab_summary(outcome.metadata)
        try:
            out["layer_states"] = dataclasses.asdict(interval_layer_states(model))
        except BridgeError as err:
            out["layer_states_error"] = {"code": err.code, "message": err.message}
    except BridgeError as err:
        out = {"error": {"code": err.code, "message": err.message, "retryable": err.retryable}}
    tmp = Path(output_path + ".tmp")
    tmp.write_text(json.dumps(out))
    tmp.replace(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
