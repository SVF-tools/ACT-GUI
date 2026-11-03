"""Invoke a real ACT verification entry point and report ACT's verdict (EXE-01).

The bridge never computes a verdict: it maps ACT's VerifyStatus 1:1.
Runs are blocking; the workbench executes them inside a worker process.
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

from engine_bridge.contracts import DOMAINS, BridgeError, Domain, Method, RunOutcome, Verdict
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec.describe import load_net

_STATUS_MAP: dict[str, Verdict] = {
    "CERTIFIED": "certified", "FALSIFIED": "falsified", "UNKNOWN": "unknown", "TIMEOUT": "timeout",
}


def _jsonable(meta: dict[str, Any]) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in meta.items():
        if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
            out[str(k)] = v
        elif isinstance(v, float):
            out[str(k)] = v if math.isfinite(v) else str(v)
        # tensors, lists, nested dicts are omitted from the summary (not copied out of ACT)
    return out


def _outcome(method: Method, result: Any, elapsed: float, domain: Domain | None = None) -> RunOutcome:
    import torch

    name = result.status.name
    ce = result.counterexample
    return RunOutcome(
        method=method, verdict=_STATUS_MAP.get(name, "error"), act_status=name, elapsed_s=round(elapsed, 4),
        metadata=_jsonable(dict(result.metadata or {})),
        counterexample=tuple(float(x) for x in ce.reshape(-1).tolist()) if ce is not None else None,
        device=str(torch.get_default_device()), domain=domain,
    )


def select_domain(domain: Domain) -> None:
    """Set ACT's process-global solver and transfer-function modes the way act/config/pipeline_cli.py does.

    Always sets both, so a previous selection in this process cannot leak into the next ACT call.
    """
    from act.back_end.transfer_functions import set_solver_mode, set_transfer_function_mode

    set_solver_mode(None if domain == "interval" else domain)
    if domain == "hybridz":
        from act.config.config import BackendConfig

        set_transfer_function_mode("hybridz", BackendConfig.from_yaml().hybridz)
    else:  # dual is a solver, not a TF; it builds its own forward bounds
        set_transfer_function_mode("interval")


def run_verification(model_path: Path, method: Method, time_budget_s: float,
                     domain: Domain = "interval") -> RunOutcome:
    if method not in ("interval", "bab"):
        raise BridgeError("unsupported_method", f"Unknown method {method!r}")
    if domain not in DOMAINS:
        raise BridgeError("unsupported_domain", f"Unknown abstract domain {domain!r}; use one of {DOMAINS}")
    if not (0 < time_budget_s <= 3600):
        raise BridgeError("invalid_budget", "time_budget_s must be in (0, 3600]")
    net = load_net(model_path)
    with act_imports():
        if method == "interval":
            from act.back_end.verifier import verify_once

            select_domain(domain)
            # HybridZ's MILP verdict solver takes the run budget as its time limit (as pipeline_cli --timeout).
            kwargs: dict[str, Any] = (
                {"timelimit": float(time_budget_s), "hybridz_tolerance": 1e-7} if domain == "hybridz" else {})
            t = time.perf_counter()
            results = verify_once(net, **kwargs)
            elapsed = time.perf_counter() - t
            if len(results) != 1:
                raise BridgeError("unsupported_batch", f"Expected one input lane, ACT returned {len(results)}")
            return _outcome("interval", results[0], elapsed, domain)
        select_domain("interval")  # BaB keeps its own bounding path; reset any earlier selection
        from act.back_end.bab.bab import verify_bab_batched
        from act.back_end.solver.solver_torchlp import TorchLPSolver
        from act.config.config import BackendConfig, PipelineConfig

        pc = PipelineConfig.from_yaml()
        t = time.perf_counter()
        result = verify_bab_batched(
            net=net, solver_factory=TorchLPSolver, config=pc.bab,
            max_batch_size=BackendConfig.from_yaml().bab_max_batch_size,
            time_budget_s=float(time_budget_s), dual_config=pc.dual,
        )
        return _outcome("bab", result, time.perf_counter() - t)
