"""Engine binding: locate ACT, make it importable, probe version and capabilities (ES-01)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from engine_bridge.contracts import BridgeError, Capability, Diagnostic, EngineInfo, SolverStatus

DEFAULT_ACT_ROOT = "/data1/guanqin/ACT"


def act_root() -> Path:
    return Path(os.environ.get("ACT_ROOT", DEFAULT_ACT_ROOT)).resolve()


@contextmanager
def act_imports(root: Path | None = None) -> Iterator[Path]:
    """Ensure the pinned ACT checkout is importable; raise act_missing otherwise."""
    root = root or act_root()
    if not (root / "act" / "__init__.py").exists() and not (root / "act").is_dir():
        raise BridgeError("act_missing", f"ACT checkout not found at {root} (set ACT_ROOT).")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import act  # noqa: F401
    except Exception as exc:  # import failure is an environment diagnostic, not a verdict
        raise BridgeError("act_import_failed", f"Cannot import ACT from {root}: {exc}") from exc
    yield root


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


# Capabilities established against the pinned baseline (see engine_bridge/engine_session/README.md).
_BASELINE_CAPABILITIES = (
    Capability("model.load_json", "available", "act.back_end.serialization.serialization.load_net_from_file"),
    Capability("spec.read", "available", "INPUT_SPEC / ASSERT layer params"),
    Capability("verify.interval", "available", "act.back_end.verifier.verify_once"),
    Capability("verify.bab", "available", "act.back_end.bab.bab.verify_bab_batched + TorchLPSolver (as act/config/pipeline_cli.py)"),
    Capability("inspect.layer_bounds.interval", "available", "act.back_end.analyze.analyze after-facts"),
    Capability("events.bab_nodes", "unsupported", "no BaB observer hook in baseline (plan ACT-03)"),
    Capability("events.bab_summary", "available", "VerifyResult.metadata after completion"),
    Capability("control.pause_step_split", "unsupported", "no safe control boundary in baseline (plan ACT-05)"),
    Capability("geometry.projection", "unsupported", "no projection export in baseline (plan ACT-04)"),
)


_GUROBI_PROBE = """
import json
try:
    import gurobipy as gp
except ImportError as exc:
    print('@@RESULT ' + json.dumps({'installed': False, 'error': str(exc)}), flush=True)
    raise SystemExit(0)
version = '.'.join(map(str, gp.gurobi.version()))
try:
    gp.Env().dispose()
    print('@@RESULT ' + json.dumps({'installed': True, 'version': version, 'error': None}), flush=True)
except gp.GurobiError as exc:
    print('@@RESULT ' + json.dumps({'installed': True, 'version': version, 'error': f'{exc.errno}: {exc}'}), flush=True)
"""


def probe_gurobi(license_file: Path | None = None, timeout_s: float = 60.0) -> SolverStatus:
    """Start a Gurobi environment in a fresh process and report Gurobi's own license verdict.

    license_file overrides GRB_LICENSE_FILE for this check only; None keeps the inherited
    environment. A separate process is required because Gurobi reads the license once per process.
    """
    env = dict(os.environ)
    if license_file is not None:
        env["GRB_LICENSE_FILE"] = str(license_file)
    try:
        proc = subprocess.run([sys.executable, "-c", _GUROBI_PROBE], env=env, capture_output=True, text=True,
                              timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return SolverStatus("gurobi", None, "invalid", f"License check did not finish within {timeout_s:.0f}s.")
    lines = (proc.stdout + proc.stderr).splitlines()
    result = next((json.loads(l[len("@@RESULT "):]) for l in lines if l.startswith("@@RESULT ")), None)
    if result is None:
        tail = " | ".join(lines[-3:])
        return SolverStatus("gurobi", None, "invalid", f"License check exited with code {proc.returncode}: {tail}")
    if not result["installed"]:
        return SolverStatus("gurobi", None, "not_installed", result["error"])
    # Gurobi echoes parameter names (never values for secrets) and its license banner.
    banner = [l for l in lines if not l.startswith("@@RESULT ") and "license" in l.lower()]
    if result["error"]:
        return SolverStatus("gurobi", result["version"], "invalid", result["error"])
    restricted = any(l.startswith("Restricted license") for l in banner)
    return SolverStatus("gurobi", result["version"], "restricted" if restricted else "licensed",
                        "; ".join(banner) or "Gurobi environment started.")


def probe(expected_commit: str | None = None, root: Path | None = None) -> EngineInfo:
    root = root or act_root()
    diags: list[Diagnostic] = []
    torch_v: str | None = None
    cuda: bool | None = None
    commit = None
    dirty = None
    try:
        with act_imports(root):
            import torch

            torch_v = torch.__version__
            cuda = bool(torch.cuda.is_available())
        commit = _git(root, "rev-parse", "HEAD")
        status = _git(root, "status", "--porcelain", "--untracked-files=no")
        dirty = None if status is None else bool(status)
        if expected_commit and commit and commit != expected_commit:
            diags.append(Diagnostic("version_mismatch", "warning",
                                    f"ACT at {commit[:12]} differs from pinned baseline {expected_commit[:12]}; results are not baseline-certified."))
        if dirty:
            diags.append(Diagnostic("tracked_changes", "warning", "ACT checkout has modified tracked files."))
        caps = _BASELINE_CAPABILITIES if not diags else tuple(
            Capability(c.name, c.availability, c.source + " (baseline claim; current checkout differs)") for c in _BASELINE_CAPABILITIES)
    except BridgeError as err:
        diags.append(Diagnostic(err.code, "error", err.message))
        caps = tuple(Capability(c.name, "unsupported", f"ACT unavailable: {err.code}") for c in _BASELINE_CAPABILITIES)
    return EngineInfo(
        act_root=str(root), commit=commit, expected_commit=expected_commit, tracked_changes=dirty,
        python=sys.version.split()[0], torch=torch_v, cuda_available=cuda,
        capabilities=caps, diagnostics=tuple(diags),
    )
