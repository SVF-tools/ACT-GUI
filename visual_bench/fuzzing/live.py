"""Live display state of running fuzz runs: the latest mutated input and the ACT counterexamples seen so far.

Fed by the run supervisor with each JSON line the worker writes to its progress pipe. Frames are
kept in memory only; progress points are returned to the supervisor to be committed as events.
"""
from __future__ import annotations

import threading
from typing import Any

LIVE_HIT_LIMIT = 200  # ACT counterexamples kept in memory per running fuzz run (from violating frames)


class FuzzLive:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frames: dict[str, dict[str, Any]] = {}
        self._hits: dict[str, dict[int, dict[str, Any]]] = {}

    def observe(self, run_id: str, msg: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
        """Keep a frame in memory, or return a progress point as the (kind, payload) event to commit."""
        if "progress" in msg:
            return "fuzz.progress", msg["progress"]
        if "control" in msg:
            return "fuzz.control", msg["control"]
        if "control_state" in msg:
            state = msg["control_state"]
            return ("fuzz.paused" if state["paused"] else "fuzz.resumed"), state
        frame = msg["frame"]
        with self._lock:
            self._frames[run_id] = frame
            ce = frame.get("counterexample")
            hits = self._hits.setdefault(run_id, {})
            if ce is not None and len(hits) < LIVE_HIT_LIMIT:
                hits[ce["index"]] = ce
        return None

    def forget(self, run_id: str) -> None:
        with self._lock:
            self._frames.pop(run_id, None)
            self._hits.pop(run_id, None)

    def snapshot(self, run_id: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        with self._lock:
            return self._frames.get(run_id), sorted(self._hits.get(run_id, {}).values(), key=lambda c: c["index"])

    def hit(self, run_id: str, index: int) -> dict[str, Any] | None:
        with self._lock:
            return self._hits.get(run_id, {}).get(index)
