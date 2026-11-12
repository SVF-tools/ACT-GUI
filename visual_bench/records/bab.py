"""BaB tree log with bounded live notifications (REC-06, VER-17).

The run worker appends one JSON line per committed ACT record (a wave, then the terminal) to bab.jsonl in the run
directory and flushes it before it notifies the supervisor, so a notification never runs ahead of its data. A last
"end" line says the recording finished and how many records the bridge could not read. Notifications carry only
counters and are coalesced to MAX_BAB_LINES_PER_SECOND plus a final one; the log itself stays complete.
"""
from __future__ import annotations

import dataclasses
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine_bridge.events import BabRecord
from engine_bridge.contracts import BabTerminal

MAX_BAB_LINES_PER_SECOND = 2
LOG = "bab.jsonl"


class BabWriter:
    def __init__(self, directory: Path, send: Callable[[dict[str, Any]], None]) -> None:
        self.send = send
        self._file = open(directory / LOG, "w", encoding="utf-8")
        self.counters: dict[str, Any] = {"seq": 0, "wave": 0, "waves": 0, "nodes": 1, "solved": 0, "frontier": 1,
                                         "terminal": None}
        self._last_sent = float("-inf")
        self._unsent = False

    def __call__(self, record: BabRecord) -> None:
        kind = "terminal" if isinstance(record, BabTerminal) else "wave"
        self._write({"kind": kind, **dataclasses.asdict(record)})
        c = self.counters
        c.update(seq=record.seq, wave=record.wave, frontier=record.frontier_size)
        if isinstance(record, BabTerminal):
            c["terminal"] = record.status
        else:
            c.update(waves=c["waves"] + 1, nodes=c["nodes"] + len(record.children), solved=c["solved"] + len(record.nodes))
        self._unsent = True
        now = time.monotonic()
        if kind == "terminal" or now - self._last_sent >= 1 / MAX_BAB_LINES_PER_SECOND:
            self._notify(now)

    def finish(self, ignored_records: int, error: str | None) -> None:
        self._write({"kind": "end", "ignored_records": ignored_records, "error": error})
        self._file.close()
        if self._unsent:
            self._notify(time.monotonic())

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def _write(self, line: dict[str, Any]) -> None:
        self._file.write(json.dumps(line, allow_nan=False, separators=(",", ":")) + "\n")
        self._file.flush()

    def _notify(self, now: float) -> None:
        self.send(dict(self.counters))
        self._last_sent = now
        self._unsent = False
