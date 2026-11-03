"""Invoke ACT's inference-based fuzzer (ACTFuzzer) on a JSON ACT net (EXE-04).

The model is rebuilt with ACT's own ACTToTorch (the converter ACT's BaB uses for
concrete counterexample checks); seeds are the net's INPUT rows; violations are
whatever ACT's PropertyChecker reports. The bridge only observes the fuzzer
between iterations and never decides a violation itself.

ACTFuzzer exposes no progress hook, so the adapter replaces the instance's
`_print_progress` (called after every iteration when report_interval == 1).
That private seam is pinned to the baseline in engine_session capabilities.
"""
from __future__ import annotations

import math
import random
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine_bridge.contracts import (
    BridgeError, FuzzCounterexample, FuzzOutcome, FuzzProgress, FuzzStrategyStats,
)
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec.describe import load_net

COUNTEREXAMPLE_LIMIT = 20
TIMELINE_LIMIT = 600
TIMELINE_EVERY_S = 0.2
PROGRESS_EVERY_S = 0.5


def _floats(t: Any) -> tuple[float, ...]:
    return tuple(float(x) for x in t.detach().reshape(-1).tolist())


def run_fuzzing(model_path: Path, time_budget_s: float, max_iterations: int, rng_seed: int = 0,
                stop_on_first: bool = False,
                on_progress: Callable[[FuzzProgress], None] | None = None) -> FuzzOutcome:
    if not (0 < time_budget_s <= 3600):
        raise BridgeError("invalid_budget", "time_budget_s must be in (0, 3600]")
    if not (1 <= max_iterations <= 10_000_000):
        raise BridgeError("invalid_budget", "max_iterations must be in [1, 10000000]")
    net = load_net(model_path)
    with act_imports():
        import numpy as np
        import torch
        from act.front_end.spec_creator_base import LabeledInputTensor
        from act.front_end.verifiable_model import InputLayer, VerifiableModel
        from act.pipeline.fuzzing.actfuzzer import ACTFuzzer, FuzzingConfig
        from act.pipeline.verification.act2torch import ACTToTorch

        try:
            model = ACTToTorch(net).run()
        except (ValueError, TypeError, NotImplementedError) as exc:
            raise BridgeError("unsupported_model", f"ACTToTorch cannot rebuild this net for fuzzing: {exc}") from exc
        input_layer = next(c for c in model.children() if isinstance(c, InputLayer))
        rows = input_layer.input_tensor
        seeds = [LabeledInputTensor(tensor=rows[i:i + 1].clone(), label=None) for i in range(rows.shape[0])]

        random.seed(rng_seed)
        np.random.seed(rng_seed)
        torch.manual_seed(rng_seed)
        strict = VerifiableModel.get_strict_mode()
        VerifiableModel.set_strict_mode(False)  # violations must reach PropertyChecker, not raise
        try:
            with tempfile.TemporaryDirectory(prefix="act-gui-fuzz-") as tmp:
                cfg = FuzzingConfig.from_yaml(
                    max_iterations=int(max_iterations), timeout_seconds=float(time_budget_s),
                    stop_on_first_violation=bool(stop_on_first), save_counterexamples=False,
                    output_dir=Path(tmp), report_interval=1, verbose=0, trace_level=0,
                )
                fuzzer = ACTFuzzer(wrapped_model=model, initial_seeds=seeds, config=cfg)
                return _fuzz(fuzzer, cfg, rng_seed, on_progress)
        finally:
            VerifiableModel.set_strict_mode(strict)


def _fuzz(fuzzer: Any, cfg: Any, rng_seed: int, on_progress: Callable[[FuzzProgress], None] | None) -> FuzzOutcome:
    weights = {str(k): float(v) for k, v in cfg.mutation_weights.items()}
    selected = dict.fromkeys(weights, 0)
    violations = dict.fromkeys(weights, 0)
    found: list[tuple[int, float, str | None]] = []
    timeline: list[FuzzProgress] = []
    done = ces_seen = 0
    last_point = last_emit = -math.inf

    def point(iteration: int) -> FuzzProgress:
        return FuzzProgress(iteration=iteration, elapsed_s=round(time.time() - fuzzer.start_time, 4),
                            coverage=float(fuzzer.coverage_tracker.get_coverage()),
                            counterexamples=len(fuzzer.counterexamples), corpus=len(fuzzer.seed_corpus))

    def observe(iteration: int, final: bool = False) -> None:
        nonlocal done, ces_seen, last_point, last_emit
        if iteration > done:
            strategy = fuzzer.mutation_engine.last_strategy
            name = str(strategy) if strategy is not None else "unknown"
            selected[name] = selected.get(name, 0) + 1
            new = len(fuzzer.counterexamples) - ces_seen
            violations[name] = violations.get(name, 0) + new
            elapsed = time.time() - fuzzer.start_time
            found.extend((iteration, elapsed, name) for _ in range(min(new, COUNTEREXAMPLE_LIMIT - len(found))))
            first_ce = ces_seen == 0 and new > 0
            done, ces_seen = iteration, len(fuzzer.counterexamples)
        else:
            first_ce = False
        now = time.monotonic()
        if final or first_ce or now - last_point >= TIMELINE_EVERY_S:
            p = point(iteration)
            last_point = now
            timeline.append(p)
            if len(timeline) > TIMELINE_LIMIT:
                del timeline[1:-1:2]
            if on_progress and (final or first_ce or now - last_emit >= PROGRESS_EVERY_S):
                last_emit = now
                on_progress(p)

    fuzzer._print_progress = observe  # baseline seam, see module docstring
    report = fuzzer.fuzz()
    observe(report.total_iterations, final=True)

    ces = tuple(
        FuzzCounterexample(
            index=i, iteration=found[i][0], elapsed_s=round(found[i][1], 4), strategy=found[i][2],
            kind=str(getattr(ce.kind, "value", ce.kind)), spec_row=int(ce.spec_row), severity=float(ce.severity),
            true_class=ce.true_class, input=_floats(ce.input), output=_floats(ce.output),
            seed_input=_floats(ce.seed_input),
        )
        for i, ce in enumerate(report.counterexamples[:COUNTEREXAMPLE_LIMIT])
    )
    n = len(report.counterexamples)
    config: dict[str, object] = {
        "max_iterations": cfg.max_iterations, "timeout_seconds": cfg.timeout_seconds,
        "coverage_strategy": cfg.coverage_strategy, "activation_threshold": cfg.activation_threshold,
        "perturb_mode": cfg.perturb_mode, "perturb_scale": cfg.perturb_scale,
        "seed_selection_strategy": cfg.seed_selection_strategy, "pgd_restarts": cfg.pgd_restarts,
        "stop_on_first_violation": cfg.stop_on_first_violation, "batch_size": fuzzer.batch_size,
    }
    return FuzzOutcome(
        verdict="falsified" if n else "unknown",
        act_status="COUNTEREXAMPLE_FOUND" if n else "NO_COUNTEREXAMPLE",
        iterations=int(report.total_iterations), elapsed_s=round(float(report.total_time), 4),
        neuron_coverage=float(report.neuron_coverage), coverage_strategy=str(cfg.coverage_strategy),
        seeds_explored=int(report.seeds_explored), total_mutations=int(report.total_mutations),
        counterexample_count=n, never_activated_count=int(report.num_of_never_activated_neurons),
        never_activated_sample=tuple(f"{layer}[{idx}]" for layer, idx in report.never_activated_neurons),
        counterexamples=ces, timeline=tuple(timeline),
        strategies=tuple(FuzzStrategyStats(name=k, weight=weights.get(k, 0.0), selected=selected[k],
                                           violations=violations[k]) for k in selected),
        config=config, rng_seed=rng_seed, device=str(fuzzer.device),
    )
