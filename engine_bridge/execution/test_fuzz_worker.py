"""Real ACT worker pipe integration, run with ACT_CODE_ROOT pointing at act-gui-match.

This lives beside the native execution tests because collecting visual_bench/conftest.py imports
the default HTTP app and intentionally restores the pinned engine before tests execute.
"""
from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time

import pytest

from engine_bridge.engine_session import act_code_root
from engine_bridge.execution.fuzz import _control_available
from visual_bench.fuzzing.schemas import FuzzOptions


@pytest.mark.parametrize("stop_kind", ["pipe", "signal"])
def test_native_worker_pause_update_resume_and_stop(tmp_path, stop_kind):
    if not _control_available():
        pytest.skip("ACT checkout has no fuzz.control API; use ACT_CODE_ROOT=act-gui-match")
    model = act_code_root() / "act/back_end/examples/nets/layer_testing_sub.json"
    request, output = tmp_path / "request.json", tmp_path / "output.json"
    request.write_text(json.dumps({
        "method": "fuzz", "model_path": str(model), "time_budget_s": 30,
        "fuzz": FuzzOptions(max_iterations=1_000_000).model_dump(), "record_layers": False,
    }))
    read_fd, progress_fd = os.pipe()
    control_fd, write_fd = os.pipe()
    pending = b""
    messages = []

    def receive(predicate):
        nonlocal pending
        deadline = time.monotonic() + 20
        while True:
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                message = json.loads(line)
                messages.append(message)
                if predicate(message):
                    return message
            remaining = deadline - time.monotonic()
            assert remaining > 0 and select.select([read_fd], [], [], remaining)[0], messages
            chunk = os.read(read_fd, 65536)
            assert chunk, f"worker closed its progress pipe: {messages}"
            pending += chunk

    def send(action, changes=None):
        os.write(write_fd, (json.dumps({"action": action, "changes": changes}) + "\n").encode())

    with (tmp_path / "worker.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "visual_bench.verification.worker", str(request), str(output),
             str(progress_fd), str(control_fd)],
            pass_fds=(progress_fd, control_fd), stdout=log, stderr=log,
            env={**os.environ, "CUDA_VISIBLE_DEVICES": ""},
        )
        os.close(progress_fd)
        os.close(control_fd)
        try:
            receive(lambda m: "progress" in m)
            send("pause")
            receive(lambda m: m.get("control_state", {}).get("paused") is True)
            send("update", {"perturb_scale": 0.2})
            changed = receive(lambda m: "control" in m)["control"]
            assert changed["applied"] == {"perturb_scale": 0.2} and changed["rejected"] == ""
            send("resume")
            receive(lambda m: m.get("control_state", {}).get("paused") is False)
            send("pause")
            receive(lambda m: m.get("control_state", {}).get("paused") is True)
            if stop_kind == "pipe":
                send("stop")
            else:
                process.send_signal(signal.SIGTERM)
            receive(lambda m: "progress" in m and m["progress"]["iteration"] >= changed["iteration"])
            assert process.wait(timeout=20) == 0
            result = json.loads(output.read_text())
            assert "error" not in result, result
            assert result["fuzzing"]["stop_reason"] == "stopped" and result["fuzzing"]["stopped"]
            assert result["fuzzing"]["config"]["perturb_scale"] == 0.2
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            os.close(read_fd)
            os.close(write_fd)
