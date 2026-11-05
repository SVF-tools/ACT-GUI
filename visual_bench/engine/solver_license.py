"""User-supplied Gurobi license: upload, removal, status, and hand-off to run workers (VER-05).

Two sources, in precedence order:
1. uploaded: written through the workbench into <secrets>/gurobi.lic (mode 0600);
2. environment: GRB_LICENSE_FILE set by the operator, e.g. a mounted Docker secret.

The license text never leaves the service: status reports only source, fingerprint, and
Gurobi's own check result (engine_bridge.engine_session.probe_gurobi).
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from engine_bridge.engine_session import probe_gurobi
from visual_bench.engine import schemas as S
from visual_bench.wire import Method

LicenseSource = Literal["uploaded", "environment", "none"]

# Keys that identify a Gurobi license file: node-locked/academic (KEY, HOSTID), WLS, token server, cloud.
_IDENTIFYING_KEYS = {"KEY", "HOSTID", "LICENSEID", "WLSACCESSID", "TOKENSERVER", "CLOUDACCESSID", "CSMANAGER"}
_LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
# The workbench's current methods use ACT's TorchLPSolver; no method needs Gurobi yet.
USED_BY_METHODS: list[Method] = []


class LicenseRejected(ValueError):
    pass


def validate_license_text(content: str) -> str:
    """Accept only text shaped like a Gurobi license file; return it with normalized line endings."""
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    keys: set[str] = set()
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.isprintable():
            raise LicenseRejected("License file contains non-printable characters.")
        m = _LINE.match(line)
        if not m:
            raise LicenseRejected("Every non-comment line of a Gurobi license file must be KEY=VALUE.")
        keys.add(m.group(1))
    if not keys & _IDENTIFYING_KEYS:
        raise LicenseRejected(f"Not a Gurobi license file: expected one of {sorted(_IDENTIFYING_KEYS)}.")
    return text if text.endswith("\n") else text + "\n"


class GurobiLicense:
    def __init__(self, secrets_root: Path) -> None:
        self.secrets_root = secrets_root
        self.uploaded_path = secrets_root / "gurobi.lic"
        self._lock = threading.Lock()
        self._cache: tuple[tuple[object, ...], S.SolverStatusOut] | None = None

    def active(self) -> tuple[Path | None, LicenseSource]:
        if self.uploaded_path.is_file():
            return self.uploaded_path, "uploaded"
        env_file = os.environ.get("GRB_LICENSE_FILE")
        if env_file:
            return Path(env_file), "environment"
        return None, "none"

    def worker_env(self, env: dict[str, str]) -> LicenseSource:
        """Point a run worker at the active license; return the source for run provenance."""
        path, source = self.active()
        if source == "uploaded":
            env["GRB_LICENSE_FILE"] = str(path)
        return source

    def upload(self, content: str) -> S.SolverStatusOut:
        text = validate_license_text(content)
        with self._lock:
            self.secrets_root.mkdir(parents=True, exist_ok=True)
            os.chmod(self.secrets_root, 0o700)
            tmp = self.uploaded_path.with_suffix(".tmp")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(text)
            tmp.replace(self.uploaded_path)
            self._cache = None
        return self.status()

    def remove(self) -> S.SolverStatusOut:
        with self._lock:
            self.uploaded_path.unlink(missing_ok=True)
            self._cache = None
        return self.status()

    def status(self) -> S.SolverStatusOut:
        path, source = self.active()
        stat = path.stat() if path is not None and path.is_file() else None
        key = (source, str(path), stat.st_mtime_ns if stat else None, stat.st_size if stat else None)
        with self._lock:
            if self._cache and self._cache[0] == key:
                return self._cache[1]
        checked = probe_gurobi(path)
        out = S.SolverStatusOut(
            solver="gurobi", version=checked.version, license_source=source,
            license_fingerprint=hashlib.sha256(path.read_bytes()).hexdigest()[:12] if stat and path else None,
            license_updated_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")
            if stat else None,
            license_state=checked.license_state, message=checked.message, used_by_methods=USED_BY_METHODS,
        )
        with self._lock:
            self._cache = (key, out)
        return out
