"""Invoke a real ACT verification entry point and report ACT's verdict (EXE-01).

The bridge never computes a verdict: it maps ACT's VerifyStatus 1:1.
Runs are blocking; the workbench executes them inside a worker process.
"""
from __future__ import annotations

import dataclasses
import math
import time
from pathlib import Path
from typing import Any

from engine_bridge.contracts import DOMAINS, BridgeError, Domain, LaneOutcome, Method, RunOutcome, Verdict
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


# A batched net's property is the conjunction of its rows: any FALSIFIED row falsifies it, it is CERTIFIED only when
# every row is, and otherwise the first of these ACT statuses that some row reports wins.
_BATCH_PRECEDENCE: tuple[Verdict, ...] = ("falsified", "error", "timeout", "unknown", "certified")


def _batch_outcome(results: list[Any], elapsed: float, domain: Domain) -> RunOutcome:
    import torch

    rows = tuple(LaneOutcome(row=i, verdict=_STATUS_MAP.get(r.status.name) or "error", act_status=r.status.name)
                 for i, r in enumerate(results))  # verify_once returns one result per lane, in row order
    verdict: Verdict = next(v for v in _BATCH_PRECEDENCE if any(r.verdict == v for r in rows))
    ce_row = next((r.row for r in rows if r.verdict == "falsified" and results[r.row].counterexample is not None), None)
    ce = results[ce_row].counterexample if ce_row is not None else None
    counts: dict[str, object] = {f"rows_{v}": sum(r.verdict == v for r in rows) for v in _BATCH_PRECEDENCE}
    return RunOutcome(
        method="interval", verdict=verdict, act_status=verdict.upper(), elapsed_s=round(elapsed, 4),
        metadata={"batch": len(rows), **counts},
        counterexample=tuple(float(x) for x in ce.reshape(-1).tolist()) if ce is not None else None,
        device=str(torch.get_default_device()), domain=domain, rows=rows, counterexample_row=ce_row,
    )


def _with_output(outcome: RunOutcome, net: Any, x: Any) -> RunOutcome:
    """Add the network output at ACT's counterexample, from ACT's own rebuilt model (ACTToTorch, the converter
    ACT's BaB uses for concrete counterexample checks), so the counterexample exports as a VNN-COMP witness.

    The rebuilt model maps one lane per INPUT row, so x goes into its row of the full batch. A failure is
    reported on the outcome; it only disables the export, never the verdict or ACT's counterexample.
    """
    if x is None:
        return outcome
    import torch
    from act.front_end.verifiable_model import InputLayer, VerifiableModel
    from act.pipeline.verification.act2torch import ACTToTorch

    row = outcome.counterexample_row or 0
    try:
        model = ACTToTorch(net).run()
        full = next(c for c in model.children() if isinstance(c, InputLayer)).input_tensor.clone()
        full[row] = x.reshape(full[row].shape).to(device=full.device, dtype=full.dtype)
        strict = VerifiableModel.get_strict_mode()
        VerifiableModel.set_strict_mode(False)  # the property is violated here by construction
        try:
            with torch.no_grad():
                out = model(full)
        finally:
            VerifiableModel.set_strict_mode(strict)
        y = (out["output"] if isinstance(out, dict) else out)[row]
    except Exception as exc:  # noqa: BLE001 - reported on the outcome, see docstring
        return dataclasses.replace(outcome, counterexample_output_error=f"{type(exc).__name__}: {exc}")
    return dataclasses.replace(outcome, counterexample_output=tuple(float(v) for v in y.reshape(-1).tolist()))


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
            if not results:
                raise BridgeError("unsupported_batch", "ACT returned no input lane")
            if len(results) == 1:
                return _with_output(_outcome("interval", results[0], elapsed, domain), net, results[0].counterexample)
            out = _batch_outcome(results, elapsed, domain)
            return _with_output(out, net, None if out.counterexample_row is None
                                else results[out.counterexample_row].counterexample)
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
        return _with_output(_outcome("bab", result, time.perf_counter() - t), net, result.counterexample)
