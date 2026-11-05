"""ACT branch checkouts (ES-05): list a remote's branches and stage one branch head as an importable checkout.

A staged checkout is a shallow clone of one commit under <engines_root>/<remote slug>/<commit>. ACT's
git-ignored data/ and literature/ directories are linked from the baseline checkout, so ACT code that
resolves paths from its own project root still finds them. Which checkout is active is the caller's
choice: point ACT_CODE_ROOT at the returned path (see session.act_code_root).
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from engine_bridge.contracts import BridgeError

GIT_TIMEOUT_S = 600.0
_LINKED_ASSETS = ("data", "literature")


@dataclass(frozen=True)
class Checkout:
    url: str
    branch: str
    commit: str
    path: Path


def _git(*args: str, cwd: Path | None = None, timeout: float = GIT_TIMEOUT_S) -> str:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")  # never wait for credentials on a private remote
    try:
        out = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise BridgeError("git_failed", f"git {args[0]} did not finish within {timeout:.0f}s.", retryable=True) from exc
    if out.returncode != 0:
        tail = " | ".join(out.stderr.strip().splitlines()[-3:])
        raise BridgeError("git_failed", f"git {args[0]} failed: {tail}", retryable=True)
    return out.stdout


def _remote_dir(url: str, engines_root: Path) -> Path:
    return engines_root / hashlib.sha256(url.encode()).hexdigest()[:12]


def remove_checkouts(url: str, engines_root: Path, keep: Path | None = None) -> None:
    """Delete every staged checkout of url except keep (the active one, if it belongs to url)."""
    remote_dir = _remote_dir(url, engines_root)
    for path in remote_dir.iterdir() if remote_dir.is_dir() else ():
        if keep is None or path.resolve() != keep.resolve():
            shutil.rmtree(path, ignore_errors=True)
    if remote_dir.is_dir() and not any(remote_dir.iterdir()):
        remote_dir.rmdir()


def list_branches(url: str) -> tuple[str, ...]:
    out = _git("ls-remote", "--heads", url, timeout=60.0)
    return tuple(sorted(line.split("refs/heads/", 1)[1] for line in out.splitlines() if "refs/heads/" in line))


def fetch_checkout(url: str, branch: str, engines_root: Path, assets_root: Path) -> Checkout:
    """Stage the current head of url's branch (reusing an existing checkout of the same commit)."""
    if branch not in list_branches(url):
        raise BridgeError("branch_not_found", f"{url} has no branch {branch!r}.")
    remote_dir = _remote_dir(url, engines_root)
    remote_dir.mkdir(parents=True, exist_ok=True)
    tmp = remote_dir / f".fetch-{uuid.uuid4().hex[:8]}"
    try:
        _git("init", "-q", str(tmp))
        _git("fetch", "-q", "--depth", "1", url, f"refs/heads/{branch}", cwd=tmp)
        commit = _git("rev-parse", "FETCH_HEAD", cwd=tmp).strip()
        dest = remote_dir / commit
        if not (dest / ".git").is_dir():
            _git("-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD", cwd=tmp)
            tmp.rename(dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name in _LINKED_ASSETS:
        src, link = assets_root / name, dest / name
        if src.exists() and not link.exists() and not link.is_symlink():
            link.symlink_to(src.resolve(), target_is_directory=True)
    return Checkout(url=url, branch=branch, commit=commit, path=dest)
