"""Complete propagation storage with bounded live notifications (VER-13).

Each blob is canonical JSON dtype/shape metadata, a newline, then little-endian
float32 bytes. Its SHA256 covers that entire envelope. Publication order is
blobs -> atomic index -> progress notification, so a live reader never sees a
reference to an unfinished tensor. The final index and all blobs are sealed.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from engine_bridge.inspection.propagation import PropagationRecord
from visual_bench.records.store import RecordStore
from visual_bench.wire import wire_number

MAX_PROPAGATION_LINES_PER_SECOND = 10


class PropagationWriter:
    def __init__(self, directory: Path, domain: str, send: Callable[[dict[str, Any]], None]) -> None:
        self.directory = directory
        self.blobs = directory / "blobs"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.send = send
        self.index: dict[str, Any] = {
            "domain": domain, "availability": "available", "complete": False,
            "records": [], "phases": [], "ignored_records": 0,
        }
        self._last_sent = float("-inf")
        self._pending: dict[str, Any] | None = None
        self._count = 0
        self.publish()

    def __call__(self, record: PropagationRecord) -> None:
        tensors = {}
        for name, tensor in record.tensors.items():
            metadata = {"dtype": tensor.dtype, "shape": list(tensor.shape)}
            data = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode() + b"\n" + tensor.data
            digest = hashlib.sha256(data).hexdigest()
            path = self.blobs / f"{digest}.f32"
            if not path.exists():
                RecordStore._atomic_write(path, data)
            tensors[name] = {"sha256": digest, **metadata}
        entry = {
            "record_id": self._count, "kind": record.kind,
            "key": asdict(record.key) if record.key else None, "t_ms": record.t_ms,
            "layer_kind": record.layer_kind, "output_shape": list(record.output_shape),
            "shape": next((t["shape"] for t in tensors.values()), []),
            "tensors": tensors, "counts": record.counts,
            "metadata": {k: wire_number(v) if isinstance(v, float) else v for k, v in record.metadata.items()},
        }
        self._count += 1
        self.index["phases" if record.kind == "PhaseEvent" else "records"].append(entry)
        self._pending = entry
        now = time.monotonic()
        if now - self._last_sent >= 1 / MAX_PROPAGATION_LINES_PER_SECOND:
            self.publish()
            self.send(entry)
            self._pending = None
            self._last_sent = now

    def publish(self) -> None:
        RecordStore._atomic_write(self.directory / "propagation.json",
                                  json.dumps(self.index, sort_keys=True, allow_nan=False).encode())

    def finish(self, ignored_records: int) -> None:
        self.index.update(complete=True, ignored_records=ignored_records)
        self.publish()
        if self._pending is not None:
            self.send(self._pending)
            self._pending = None
