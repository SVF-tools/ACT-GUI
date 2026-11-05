"""ACT engine status, ACT branch selection and solver licenses (VER-05, VER-08).

Every other service calls require_engine() before it asks the bridge to touch ACT.
The selected ACT source is restored from active.json at start and exported as ACT_CODE_ROOT, so
the service and its run workers import ACT from it. A process cannot re-import ACT from another
checkout, so a switch is checked in a separate probe process, persisted, and then the service
restarts itself (restart_service) after its response is sent.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from dataclasses import asdict
from functools import cached_property
from pathlib import Path
from typing import Callable

from engine_bridge.contracts import BridgeError, EngineInfo
from engine_bridge.engine_session import (act_root, fetch_checkout, list_branches, probe, probe_isolated,
                                          remove_checkouts)
from visual_bench.engine import schemas as S
from visual_bench.engine.solver_license import GurobiLicense
from visual_bench.errors import AppError, bridge_error
from visual_bench.records.store import now_iso

BASELINE = S.EngineSourceOut(kind="baseline")
MAX_CUSTOM_REMOTES = 10  # remembered user-entered repositories, not counting protected owners

# https only, no credentials, query or fragment: rules out file://, ssh and git's ext:: command transport.
_REPO_URL = re.compile(r"https://(?P<host>[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)(?::\d{1,5})?(?P<path>(?:/[A-Za-z0-9._~-]+)+)/?")


def custom_remote(url: str) -> tuple[str, str]:
    """(display name, url) of a user-entered repository URL; 422 unless it is a plain https git URL."""
    url = url.strip()
    m = _REPO_URL.fullmatch(url)
    if (m is None or any(seg in (".", "..") for seg in m["path"].split("/"))
            or re.fullmatch(r"[\d.]+", m["host"])):  # IP literals would let visitors aim git at internal hosts
        raise AppError(422, "invalid_remote_url",
                       "Enter an https:// git repository URL without credentials, e.g. https://github.com/<owner>/ACT.git")
    return f"{m['host'].lower()}{m['path'].removesuffix('.git')}", url


def _owner(url: str) -> str | None:
    """host/owner of an https repository URL, e.g. github.com/guanqin-123."""
    m = _REPO_URL.fullmatch(url.strip())
    return f"{m['host']}/{m['path'].split('/')[1]}".lower() if m else None


def restart_service() -> None:
    """Replace this process with a fresh interpreter running the same command (same PID and port)."""
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, *sys.orig_argv[1:]])


class EngineService:
    def __init__(self, expected_commit: str, secrets_root: Path, engines_root: Path, remotes: dict[str, str],
                 allow_custom: bool = True) -> None:
        self.expected_commit = expected_commit
        self.gurobi = GurobiLicense(secrets_root)
        self.engines_root = engines_root
        self.remotes = remotes
        self.allow_custom = allow_custom
        self._switch_lock = threading.Lock()
        self.active_runs: Callable[[], int] = lambda: 0  # set by the Workbench once RunService exists
        self.restart_pending = False
        self.source = self._restore()

    @cached_property
    def info(self) -> EngineInfo:
        return probe(self.expected_commit)

    def engine_out(self) -> S.EngineInfoOut:
        return self._out(self.info, self.source)

    def require_engine(self) -> None:
        if self.restart_pending:
            raise AppError(503, "restart_pending", "The service is restarting onto another ACT source.", retryable=True)
        if not self.info.usable:
            first = next(d for d in self.info.diagnostics if d.severity == "error")
            raise AppError(503, first.code, first.message)

    def capability_available(self, name: str) -> bool:
        return any(c.name == name and c.availability == "available" for c in self.info.capabilities)

    def require_capability(self, name: str) -> None:
        """Gate an ACT feature on its API checks (parity.py), after require_engine."""
        self.require_engine()
        cap = next((c for c in self.info.capabilities if c.name == name), None)
        if cap is None or cap.availability != "available":
            reason = cap.source if cap else "not declared by the bridge"
            raise AppError(422, "capability_unavailable", f"The active ACT checkout lacks {name}: {reason}")

    # -- ACT source selection (VER-08) ---------------------------------------
    @property
    def _state_file(self) -> Path:
        return self.engines_root / "active.json"

    def _restore(self) -> S.EngineSourceOut:
        try:
            state = json.loads(self._state_file.read_text())
        except FileNotFoundError:
            state = None
        if state and Path(state["path"]).is_dir():
            os.environ["ACT_CODE_ROOT"] = state["path"]
            return S.EngineSourceOut.model_validate(state["source"])
        os.environ.pop("ACT_CODE_ROOT", None)
        return BASELINE

    @property
    def _custom_file(self) -> Path:
        return self.engines_root / "remotes.json"

    def _saved(self) -> dict[str, dict[str, str]]:
        """remotes.json: name -> {url, used_at}, least recently used first."""
        try:
            raw = json.loads(self._custom_file.read_text())
        except FileNotFoundError:
            return {}
        return {n: e if isinstance(e, dict) else {"url": e, "used_at": ""} for n, e in raw.items()}

    def _custom_remotes(self) -> dict[str, str]:
        """User-entered repositories that imported as ACT at least once (shared by every user), newest first."""
        if not self.allow_custom:
            return {}
        return {n: e["url"] for n, e in reversed(self._saved().items()) if n not in self.remotes}

    def _protected(self, url: str) -> bool:
        """Repositories of a configured remote's owner (e.g. github.com/guanqin-123/...) are never evicted."""
        owner = _owner(url)
        return owner is not None and owner in {_owner(u) for u in self.remotes.values()}

    def _remember(self, name: str, url: str) -> None:
        """Mark name as just used; beyond MAX_CUSTOM_REMOTES unprotected ones, forget the least recently used."""
        saved = self._saved()
        saved.pop(name, None)
        saved[name] = {"url": url, "used_at": now_iso()}
        evictable = [n for n, e in saved.items() if not self._protected(e["url"])]
        active = os.environ.get("ACT_CODE_ROOT")
        for old in evictable[:max(0, len(evictable) - MAX_CUSTOM_REMOTES)]:
            remove_checkouts(saved.pop(old)["url"], self.engines_root, Path(active) if active else None)
        self.engines_root.mkdir(parents=True, exist_ok=True)
        self._custom_file.write_text(json.dumps(saved, indent=2))

    def sources(self) -> S.EngineSourcesOut:
        remotes = [S.EngineRemoteOut(name=n, url=u, custom=False) for n, u in self.remotes.items()]
        remotes += [S.EngineRemoteOut(name=n, url=u, custom=True) for n, u in self._custom_remotes().items()]
        return S.EngineSourcesOut(active=self.source, remotes=remotes, custom_allowed=self.allow_custom)

    def _resolve(self, remote: str | None, url: str | None) -> tuple[str, str, bool]:
        """(name, url, custom) of a listed remote name or a user-entered URL."""
        if (remote is None) == (url is None):
            raise AppError(422, "invalid_request", "give either remote or url")
        if url is not None:
            if not self.allow_custom:
                raise AppError(403, "custom_remotes_disabled", "This workbench only offers its configured ACT repositories.")
            name, url = custom_remote(url)
            configured = next((n for n, u in self.remotes.items() if u == url), None)
            return (configured, url, False) if configured else (name, url, True)
        listed = {**self._custom_remotes(), **self.remotes}
        if remote not in listed:
            raise AppError(404, "unknown_remote", f"Unknown ACT repository {remote!r}.")
        return remote, listed[remote], remote not in self.remotes

    def branches(self, remote: str | None, url: str | None) -> S.EngineBranchesOut:
        name, url, _custom = self._resolve(remote, url)
        try:
            return S.EngineBranchesOut(remote=name, url=url, branches=list(list_branches(url)))
        except BridgeError as err:
            raise bridge_error(err, 502) from err

    def switch(self, req: S.EngineSwitchRequest) -> S.EngineInfoOut:
        """Select the baseline or a remote branch head for the next service start (restart_service).

        Nothing changes when runs are active or the checkout fails its probe; the returned info is
        that probe's result for the selected checkout.
        """
        with self._switch_lock:
            self._require_idle()
            path, source, info = self._candidate(req)
            if not info.usable:
                first = next(d for d in info.diagnostics if d.severity == "error")
                raise AppError(422, "engine_unusable", f"{source.remote}/{source.branch} was not activated: {first.message}")
            self._require_idle()  # a run may have started while the branch was fetched and probed
            self.engines_root.mkdir(parents=True, exist_ok=True)
            if path is None:
                self._state_file.unlink(missing_ok=True)
            else:
                self._state_file.write_text(json.dumps({"path": path, "source": source.model_dump()}, indent=2))
            self.source = source
            self.restart_pending = True
            return self._out(info, source)

    def _require_idle(self) -> None:
        if self.restart_pending:
            raise AppError(409, "restart_pending", "The service is restarting onto another ACT source.")
        if self.active_runs():
            raise AppError(409, "runs_active", "Stop or wait for the active runs before switching ACT.")

    def check(self, req: S.EngineSwitchRequest) -> S.EngineInfoOut:
        """Probe and API-check a candidate source without switching to it."""
        _path, source, info = self._candidate(req)
        return self._out(info, source.model_copy(update={"switched_at": None}))

    def _candidate(self, req: S.EngineSwitchRequest) -> tuple[str | None, S.EngineSourceOut, EngineInfo]:
        if req.remote is None and req.url is None:
            return None, BASELINE, probe_isolated(self.expected_commit, act_root())
        name, url, custom = self._resolve(req.remote, req.url)
        if not req.branch:
            raise AppError(422, "invalid_request", "branch is required with a repository")
        try:
            co = fetch_checkout(url, req.branch, self.engines_root, act_root())
        except BridgeError as err:
            raise bridge_error(err, 404 if err.code == "branch_not_found" else 502) from err
        source = S.EngineSourceOut(kind="branch", remote=name, url=co.url, branch=co.branch, commit=co.commit,
                                   switched_at=now_iso())
        info = probe_isolated(self.expected_commit, co.path)
        if custom and info.usable:  # offer it to every user from now on
            self._remember(name, url)
        return str(co.path), source, info

    @staticmethod
    def _out(info: EngineInfo, source: S.EngineSourceOut) -> S.EngineInfoOut:
        d = asdict(info)
        d["usable"] = info.usable
        d["source"] = source
        return S.EngineInfoOut.model_validate(d)
