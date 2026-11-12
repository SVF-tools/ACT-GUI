"""Engine binding: locate ACT, make it importable, probe version and capabilities (ES-01)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from engine_bridge.contracts import ApiCheck, BridgeError, Capability, Diagnostic, EngineInfo, SolverStatus

DEFAULT_ACT_ROOT = "/data1/guanqin/ACT"


def act_root() -> Path:
    """The baseline ACT checkout: catalog nets, data/ and literature/ are read from here."""
    return Path(os.environ.get("ACT_ROOT", DEFAULT_ACT_ROOT)).resolve()


def act_code_root() -> Path:
    """The checkout whose ACT code is imported: ACT_CODE_ROOT (a switched branch) or else ACT_ROOT."""
    code = os.environ.get("ACT_CODE_ROOT")
    return Path(code).resolve() if code else act_root()


@contextmanager
def act_imports(root: Path | None = None) -> Iterator[Path]:
    """Ensure the active ACT checkout is importable; raise act_missing otherwise.

    A process imports ACT from one checkout only: ACT modules register ONNX converters in global
    third-party registries, so they cannot be re-imported from another checkout in the same process.
    """
    root = root or act_code_root()
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


# What each capability calls. Those with API requirements (parity.py) are advertised only when the
# imported checkout passes them; the unsupported ones need ACT hooks that no adapter calls yet.
_BASELINE_CAPABILITIES = (
    Capability("model.load_json", "available", "act.back_end.serialization.serialization.load_net_from_file"),
    Capability("spec.read", "available", "INPUT_SPEC / ASSERT layer params"),
    Capability("verify.interval", "available", "act.back_end.verifier.verify_once"),
    Capability("verify.dual", "available", "act.back_end.verifier.verify_once with set_solver_mode('dual') (DualSolver)"),
    Capability("verify.dual.options", "available", "act.back_end.verifier.verify_once(dual_iters, dual_config, dual_refresh_forward): DualSolver alpha optimization and DualConfig policy (ACT-07)"),
    Capability("verify.hybridz", "available", "act.back_end.verifier.verify_once with solver+TF mode 'hybridz' (HybridzTF + HZSolver)"),
    Capability("verify.bab", "available", "act.back_end.bab.bab.verify_bab_batched + TorchLPSolver (as act/config/pipeline_cli.py)"),
    Capability("verify.bab.options", "available", "act.pipeline.gui.bab_gui.bab_options / bab_run_config: every BaBConfig and DualConfig setting of verify_bab_batched, validated by ACT (ACT-09)"),
    Capability("fuzz.actfuzzer", "available", "act.pipeline.fuzzing.ACTFuzzer on ACTToTorch(net); progress via the instance's _print_progress seam; mutated-input frames via a wrapper on the instance's mutation_engine.mutate"),
    Capability("fuzz.control", "available", "act.pipeline.gui.fuzzer_gui options, observation records and FuzzControl at ACTFuzzer batch boundaries"),
    Capability("inspect.layer_bounds.interval", "available", "act.back_end.analyze.analyze after-facts"),
    Capability("observe.propagation", "available", "act.pipeline.gui.verifier_gui records during verify_once (ACT-06)"),
    Capability("source.vnnlib", "available", "act.front_end.vnnlib_loader.create_specs.create_specs_from_paths + TorchToACT"),
    Capability("source.onnx_classifier", "available", "act.front_end.vnnlib_loader.onnx_converter.convert_onnx_to_pytorch + TorchToACT"),
    Capability("events.bab_nodes", "available", "act.pipeline.gui.bab_gui BaBWave/BaBTerminal records of each committed BaB wave during verify_bab_batched (ACT-03)"),
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
    root = root or act_code_root()
    diags: list[Diagnostic] = []
    torch_v: str | None = None
    cuda: bool | None = None
    commit = None
    dirty = None
    try:
        with act_imports(root):
            import torch

            from engine_bridge.engine_session.parity import check_api

            torch_v = torch.__version__
            cuda = bool(torch.cuda.is_available())
            checks = check_api()
        commit = _git(root, "rev-parse", "HEAD")
        status = _git(root, "status", "--porcelain", "--untracked-files=no")
        dirty = None if status is None else bool(status)
        if expected_commit and commit and commit != expected_commit:
            diags.append(Diagnostic("version_mismatch", "warning",
                                    f"ACT at {commit[:12]} differs from pinned baseline {expected_commit[:12]}; results are not baseline-certified."))
        if dirty:
            diags.append(Diagnostic("tracked_changes", "warning", "ACT checkout has modified tracked files."))
        caps = tuple(_checked(c, checks, baseline=not diags) for c in _BASELINE_CAPABILITIES)
        failed = sorted({c.capability for c in checks if not c.ok})
        if failed:
            diags.append(Diagnostic("api_mismatch", "warning",
                                    f"ACT API checks failed; unavailable here: {', '.join(failed)}."))
    except BridgeError as err:
        diags.append(Diagnostic(err.code, "error", err.message))
        caps = tuple(Capability(c.name, "unsupported", f"ACT unavailable: {err.code}") for c in _BASELINE_CAPABILITIES)
        checks = ()
    return EngineInfo(
        act_root=str(root), commit=commit, expected_commit=expected_commit, tracked_changes=dirty,
        python=sys.version.split()[0], torch=torch_v, cuda_available=cuda,
        capabilities=caps, diagnostics=tuple(diags), api_checks=checks,
    )


def _checked(cap: Capability, checks: tuple[ApiCheck, ...], baseline: bool) -> Capability:
    mine = [c for c in checks if c.capability == cap.name]
    if cap.availability != "available" or not mine:
        return cap
    bad = next((c for c in mine if not c.ok), None)
    if bad is not None:
        return Capability(cap.name, "unsupported", f"API check failed: {bad.detail}")
    return Capability(cap.name, "available", cap.source + ("" if baseline else " (API checked; results not baseline-certified)"))


_PROBE_SCRIPT = """
import json, sys
from dataclasses import asdict
from pathlib import Path
from engine_bridge.engine_session.session import probe
print('@@RESULT ' + json.dumps(asdict(probe(sys.argv[1] or None, Path(sys.argv[2])))), flush=True)
"""


def probe_isolated(expected_commit: str | None, root: Path, timeout_s: float = 300.0) -> EngineInfo:
    """probe() in a fresh interpreter, for a checkout this process must not import."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[2]), env.get("PYTHONPATH")]))
    try:
        proc = subprocess.run([sys.executable, "-c", _PROBE_SCRIPT, expected_commit or "", str(root)], env=env,
                              capture_output=True, text=True, timeout=timeout_s)
        line = next((l for l in proc.stdout.splitlines() if l.startswith("@@RESULT ")), None)
        failure = None if line else f"exit code {proc.returncode}: {' | '.join(proc.stderr.strip().splitlines()[-3:])}"
    except subprocess.TimeoutExpired:
        line, failure = None, f"did not finish within {timeout_s:.0f}s"
    if line is None:
        return EngineInfo(act_root=str(root), commit=None, expected_commit=expected_commit, tracked_changes=None,
                          python=sys.version.split()[0], torch=None, cuda_available=None, capabilities=(),
                          diagnostics=(Diagnostic("probe_failed", "error", f"ACT probe {failure}"),))
    d = json.loads(line[len("@@RESULT "):])
    return EngineInfo(act_root=d["act_root"], commit=d["commit"], expected_commit=d["expected_commit"],
                      tracked_changes=d["tracked_changes"], python=d["python"], torch=d["torch"],
                      cuda_available=d["cuda_available"],
                      capabilities=tuple(Capability(**c) for c in d["capabilities"]),
                      diagnostics=tuple(Diagnostic(**g) for g in d["diagnostics"]),
                      api_checks=tuple(ApiCheck(**a) for a in d["api_checks"]))
