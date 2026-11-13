"""Filesystem run records (REC-01..03, first version).

Layout per run (var/records/<run_id>/):
  manifest.json   immutable: request, model snapshot hash, ACT commit, created_at
  events.jsonl    append-only ordered lifecycle events (seq starts at 1)
  result.json     final ACT result (written once, then hashed)
  layers.json     interval layer states computed by the worker for the run snapshot
  bab.jsonl       BaB runs: one line per committed ACT wave and the terminal record, appended by the worker
  artifacts.json  sha256 of each artifact; written last, so its presence marks a complete record
  saved_counterexamples.json  user annotation: counterexamples the user saved (mutable, not sealed)
  diagnostics.json, act_stdout.log, worker_stderr.log
                  what the worker captured while driving ACT (warnings, logs, error location, engine);
                  written once when the run ends, for failed runs too, so they are not sealed

Writes go to a temp file then os.replace, so a crash never leaves a partial
artifact visible. Paths inside a record are relative; no client paths are stored.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import struct
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_RUN_ID = re.compile(r"^run-[0-9a-f]{12}$")
ARTIFACTS = ("manifest.json", "result.json", "layers.json", "fuzzing.json", "propagation.json", "bab.jsonl")
# User annotations may be written before or after sealing; they never change a sealed artifact.
ANNOTATIONS = ("saved_counterexamples.json", "fuzz_control_requests.json")
DIAGNOSTICS = ("diagnostics.json", "act_stdout.log", "worker_stderr.log")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RecordStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._changed = threading.Condition(self._lock)

    # -- paths -------------------------------------------------------------
    def run_dir(self, run_id: str) -> Path:
        if not _RUN_ID.match(run_id):
            raise KeyError(run_id)
        return self.root / run_id

    def exists(self, run_id: str) -> bool:
        try:
            return (self.run_dir(run_id) / "manifest.json").is_file()
        except KeyError:
            return False

    def run_ids(self) -> list[str]:
        ids = [p.name for p in self.root.iterdir() if _RUN_ID.match(p.name) and (p / "manifest.json").is_file()]
        return sorted(ids, key=lambda r: self.manifest(r)["created_at"], reverse=True)

    # -- writes ------------------------------------------------------------
    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def create(self, run_id: str, manifest: dict[str, Any]) -> None:
        d = self.run_dir(run_id)
        d.mkdir(parents=True, exist_ok=False)
        self._atomic_write(d / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode())

    def append_event(self, run_id: str, kind: str, status: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._changed:
            events = self.events(run_id)
            ev = {"run_id": run_id, "seq": len(events) + 1, "kind": kind, "at": now_iso(),
                  "status": status, "payload": payload or {}}
            # Rewrite committed prefix + new event atomically: a torn tail left by a crash is
            # dropped instead of being glued to the new line.
            lines = [json.dumps(e, sort_keys=True) for e in (*events, ev)]
            self._atomic_write(self.run_dir(run_id) / "events.jsonl", ("\n".join(lines) + "\n").encode())
            self._changed.notify_all()
            return ev

    def write_artifact(self, run_id: str, name: str, obj: Any) -> None:
        if name not in ARTIFACTS or name == "manifest.json":
            raise ValueError(name)
        self._atomic_write(self.run_dir(run_id) / name, json.dumps(obj, sort_keys=True).encode())

    def write_annotation(self, run_id: str, name: str, obj: Any) -> None:
        if name not in ANNOTATIONS:
            raise ValueError(name)
        self._atomic_write(self.run_dir(run_id) / name, json.dumps(obj, indent=2, sort_keys=True).encode())

    def write_diagnostic(self, run_id: str, name: str, data: bytes) -> None:
        if name not in DIAGNOSTICS:
            raise ValueError(name)
        self._atomic_write(self.run_dir(run_id) / name, data)

    def seal(self, run_id: str) -> dict[str, str]:
        d = self.run_dir(run_id)
        hashes = {n: _sha256((d / n).read_bytes()) for n in ARTIFACTS if (d / n).is_file()}
        for path in (d / "blobs").glob("*.f32"):
            hashes[path.relative_to(d).as_posix()] = _sha256(path.read_bytes())
        self._atomic_write(d / "artifacts.json", json.dumps(hashes, indent=2, sort_keys=True).encode())
        return hashes

    # -- reads -------------------------------------------------------------
    def manifest(self, run_id: str) -> dict[str, Any]:
        return json.loads((self.run_dir(run_id) / "manifest.json").read_text())

    def events(self, run_id: str, after_seq: int = 0) -> list[dict[str, Any]]:
        path = self.run_dir(run_id) / "events.jsonl"
        if not path.is_file():
            return []
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                break  # torn final line after a crash: keep the committed prefix only
            if ev["seq"] != len(out) + 1:
                break  # gap or duplicate: stop at the last consistent event
            out.append(ev)
        return [e for e in out if e["seq"] > after_seq]

    def wait_for_events(self, run_id: str, after_seq: int, timeout: float) -> list[dict[str, Any]]:
        with self._changed:
            evs = self.events(run_id, after_seq)
            if not evs:
                self._changed.wait(timeout)
                evs = self.events(run_id, after_seq)
            return evs

    def artifact(self, run_id: str, name: str) -> Any | None:
        """Return a sealed artifact, or None when it is not (yet) recorded or fails its hash."""
        d = self.run_dir(run_id)
        sealed = d / "artifacts.json"
        if not sealed.is_file() or not (d / name).is_file():
            return None
        expected = json.loads(sealed.read_text()).get(name)
        data = (d / name).read_bytes()
        if expected is None or _sha256(data) != expected:
            return None
        return json.loads(data)

    def annotation(self, run_id: str, name: str) -> Any | None:
        if name not in ANNOTATIONS:
            raise ValueError(name)
        p = self.run_dir(run_id) / name
        return json.loads(p.read_text()) if p.is_file() else None

    def propagation_index(self, run_id: str, sealed: bool) -> Any | None:
        """Completed runs require the seal; active/failed runs expose atomic partial observations."""
        path = self.run_dir(run_id) / "propagation.json"
        expected = (self.hashes(run_id) or {}).get("propagation.json") if sealed else None
        if not path.is_file() and expected is None:
            return None
        if sealed:
            value = self.artifact(run_id, "propagation.json")
            if value is None:
                raise ValueError("propagation.json failed its seal check")
            return value
        return json.loads(path.read_text())

    def propagation_tensor(self, run_id: str, reference: dict[str, Any], sealed: bool) -> list[float]:
        digest = reference["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid propagation blob hash")
        name = f"blobs/{digest}.f32"
        data = (self.run_dir(run_id) / name).read_bytes()
        if _sha256(data) != digest:
            raise ValueError(f"{name} failed its content hash")
        if sealed and (self.hashes(run_id) or {}).get(name) != digest:
            raise ValueError(f"{name} failed its seal check")
        header, raw = data.split(b"\n", 1)
        meta = json.loads(header)
        if meta != {"dtype": reference["dtype"], "shape": reference["shape"]}:
            raise ValueError(f"{name} has inconsistent tensor metadata")
        import math

        count = math.prod(meta["shape"])
        if meta["dtype"] != "float32" or len(raw) != count * 4:
            raise ValueError(f"{name} has invalid float32 data")
        return list(struct.unpack(f"<{count}f", raw))

    def bab_log(self, run_id: str, offset: int = 0, sealed: bool = False) -> tuple[list[dict[str, Any]], int] | None:
        """The complete lines of bab.jsonl after byte `offset`, and the offset after the last one; None when the run
        has no log. A torn final line (no newline yet) is left for a later read. A sealed log must match its hash."""
        path = self.run_dir(run_id) / "bab.jsonl"
        if not path.is_file():
            return None
        if sealed:
            data = path.read_bytes()
            if (self.hashes(run_id) or {}).get("bab.jsonl") != _sha256(data):
                raise ValueError("bab.jsonl failed its seal check")
            data = data[offset:]
        else:
            with open(path, "rb") as f:
                f.seek(offset)
                data = f.read()
        complete = data[:data.rfind(b"\n") + 1]
        return [json.loads(line) for line in complete.splitlines() if line.strip()], offset + len(complete)

    def diagnostics(self, run_id: str) -> Any | None:
        p = self.run_dir(run_id) / "diagnostics.json"
        return json.loads(p.read_text()) if p.is_file() else None

    def hashes(self, run_id: str) -> dict[str, str] | None:
        p = self.run_dir(run_id) / "artifacts.json"
        return json.loads(p.read_text()) if p.is_file() else None

    def export_zip(self, run_id: str) -> bytes:
        """Bundle a sealed record: artifacts, events, and hashes, under relative paths only."""
        d = self.run_dir(run_id)
        if self.hashes(run_id) is None:
            raise FileNotFoundError("record is not sealed")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name in (*ARTIFACTS, "events.jsonl", "artifacts.json", *ANNOTATIONS, *DIAGNOSTICS,
                         *(p.relative_to(d).as_posix() for p in (d / "blobs").glob("*.f32"))):
                if (d / name).is_file():
                    z.write(d / name, arcname=f"{run_id}/{name}")
        return buf.getvalue()
