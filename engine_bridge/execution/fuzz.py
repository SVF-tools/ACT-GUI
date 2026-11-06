"""Invoke ACT's inference-based fuzzer (ACTFuzzer) on a JSON ACT net (EXE-04).

The model is rebuilt with ACT's own ACTToTorch (the converter ACT's BaB uses for
concrete counterexample checks); seeds are the net's INPUT rows; violations are
whatever ACT's PropertyChecker reports. The bridge only observes the fuzzer
between iterations and never decides a violation itself.

ACTFuzzer exposes no progress hook, so the adapter replaces the instance's
`_print_progress` (called after every iteration when report_interval == 1).
To show mutated inputs it also wraps the instance's `mutation_engine.mutate`,
keeping a reference to the latest (seeds, mutated batch) and returning ACT's
result unchanged. Both seams are pinned to the baseline in engine_session capabilities.
"""
from __future__ import annotations

import dataclasses
import math
import random
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from engine_bridge.contracts import (
    DISPLAY_VALUES, BridgeError, FuzzCounterexample, FuzzFrame, FuzzOutcome, FuzzProgress, FuzzSeed, FuzzStrategyStats,
)
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec.describe import load_net

COUNTEREXAMPLE_LIMIT = 20
SEED_LIMIT = 64  # every row of the largest batch (model_spec.sources.BATCH_LIMIT)
TIMELINE_LIMIT = 600
TIMELINE_EVERY_S = 0.2
PROGRESS_EVERY_S = 0.5
FRAME_LIMIT = 16  # recorded mutated-input frames; each holds two full inputs
# FuzzingConfig fields a caller may override. Budget, early stop and seed have their own arguments;
# output, tracing and reporting stay owned by this adapter (it observes the loop through them).
TUNABLE = frozenset({"coverage_strategy", "activation_threshold", "mutation_weights", "perturb_mode",
                     "perturb_scale", "seed_selection_strategy", "pgd_restarts", "pgd_restarts_binarized"})
# Options that are run_fuzzing arguments rather than FuzzingConfig fields.
RUN_OPTIONS = ("max_iterations", "rng_seed", "stop_on_first")
# Where each part of a fuzzing record comes from, for the workbench to show next to the record.
PROVENANCE = {
    "act_call": "act.pipeline.fuzzing.ACTFuzzer(ACTToTorch(net)).fuzz()",
    "config": "ACT act/config/pipeline.yaml fuzzing section + options",
    "frames": "lane 0 of ACT's mutated batch, read between iterations (mutation_engine.mutate wrapper)",
}


def split_options(options: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split flat fuzz options into (run_fuzzing keyword arguments, FuzzingConfig hyperparameters)."""
    run = {k: options[k] for k in RUN_OPTIONS if k in options}
    return run, {k: v for k, v in options.items() if k not in RUN_OPTIONS}


def _floats(t: Any) -> tuple[float, ...]:
    return tuple(float(x) for x in t.detach().reshape(-1).tolist())


def _dedupe_large_hits(frames: list[FuzzFrame], ces: tuple[FuzzCounterexample, ...]) -> tuple[FuzzFrame, ...]:
    """Recorded frames drop a counterexample that is above DISPLAY_VALUES values and already in `ces`;
    the record keeps one copy of each large input (save and export read it from there)."""
    listed = {c.index for c in ces}
    return tuple(dataclasses.replace(fr, counterexample=None)
                 if fr.counterexample is not None and fr.counterexample.index in listed
                 and len(fr.counterexample.input) > DISPLAY_VALUES else fr for fr in frames)


def _shown(t: Any) -> tuple[float, ...] | None:
    """A display-only vector, omitted above DISPLAY_VALUES values."""
    return _floats(t) if t.numel() <= DISPLAY_VALUES else None


def fuzzing_defaults() -> dict[str, Any]:
    """The TUNABLE fields of the pinned ACT's pipeline.yaml fuzzing section."""
    with act_imports():
        from act.config.config import read_fuzzing_section

        section = read_fuzzing_section(None)
    return {k: section[k] for k in TUNABLE if k in section}


def run_fuzzing(model_path: Path, time_budget_s: float, max_iterations: int, rng_seed: int = 0,
                stop_on_first: bool = False, hyperparameters: Mapping[str, Any] | None = None,
                on_progress: Callable[[FuzzProgress], None] | None = None,
                on_frame: Callable[[FuzzFrame], None] | None = None,
                should_stop: Callable[[], bool] | None = None) -> FuzzOutcome:
    """should_stop is polled after every iteration; once true, ACTFuzzer's own timeout check ends the
    loop at the next iteration and the report covers the iterations run (FuzzOutcome.stopped).
    hyperparameters override TUNABLE FuzzingConfig fields; omitted ones keep ACT's pipeline.yaml values."""
    overrides = dict(hyperparameters or {})
    unknown = sorted(set(overrides) - TUNABLE)
    if unknown:
        raise BridgeError("invalid_options", f"not tunable ACTFuzzer settings: {', '.join(unknown)}")
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
                    output_dir=Path(tmp), report_interval=1, verbose=0, trace_level=0, **overrides,
                )
                try:
                    fuzzer = ACTFuzzer(wrapped_model=model, initial_seeds=seeds, config=cfg)
                except ValueError as exc:  # ACT rejects an invalid setting (e.g. weights summing to 0)
                    raise BridgeError("invalid_options", f"ACTFuzzer rejected the settings: {exc}") from exc
                return _fuzz(fuzzer, cfg, rng_seed, rows, on_progress, on_frame, should_stop)
        finally:
            VerifiableModel.set_strict_mode(strict)


def _fuzz(fuzzer: Any, cfg: Any, rng_seed: int, rows: Any,
          on_progress: Callable[[FuzzProgress], None] | None,
          on_frame: Callable[[FuzzFrame], None] | None,
          should_stop: Callable[[], bool] | None = None) -> FuzzOutcome:
    import torch

    def forward(x: Any) -> Any:
        # ACT's own rebuilt model on a full batch (one lane per spec row), the same forward ACTFuzzer checks;
        # display only, no verdict. Its OUTPUT spec maps lanes onto spec rows, so it needs every row.
        with torch.no_grad():
            out = fuzzer.model(x.to(fuzzer.device))
        return (out["output"] if isinstance(out, dict) else out).detach().cpu()  # as ACTFuzzer unpacks it

    def forward_at(x: Any, row: int) -> Any:
        # Output for input x placed in lane `row`; the other lanes hold the INPUT rows.
        full = rows.clone()
        full[row] = x.to(device=full.device, dtype=full.dtype)
        return forward(full)[row]

    weights = {str(k): float(v) for k, v in cfg.mutation_weights.items()}
    selected = dict.fromkeys(weights, 0)
    violations = dict.fromkeys(weights, 0)
    found: list[tuple[int, float, str | None]] = []
    timeline: list[FuzzProgress] = []
    frames: list[FuzzFrame] = []
    batch: dict[str, Any] = {}
    done = ces_seen = 0
    stopped = False
    last_point = last_emit = -math.inf

    engine = fuzzer.mutation_engine
    act_mutate = engine.mutate

    def mutate(seeds: Any) -> Any:
        out = act_mutate(seeds)
        batch["seeds"], batch["inputs"] = seeds, out  # references only; ACT's tensors are not modified
        return out

    engine.mutate = mutate  # instance seam, see module docstring

    def to_ce(i: int, ce: Any, at: tuple[int, float, str | None], seed_out: Any) -> FuzzCounterexample:
        return FuzzCounterexample(
            index=i, iteration=at[0], elapsed_s=round(at[1], 4), strategy=at[2],
            kind=str(getattr(ce.kind, "value", ce.kind)), spec_row=int(ce.spec_row), severity=float(ce.severity),
            true_class=ce.true_class, input=_floats(ce.input), output=_floats(ce.output),
            seed_input=_shown(ce.seed_input), seed_output=_floats(seed_out),
        )

    def frame(iteration: int, violation: bool) -> FuzzFrame | None:
        if not batch:
            return None
        s, x = batch["seeds"], batch["inputs"]
        strategy = engine.last_strategy
        name = str(strategy) if strategy is not None else None
        elapsed = time.time() - fuzzer.start_time
        hit = None
        if violation and fuzzer.counterexamples:
            i = len(fuzzer.counterexamples) - 1
            ce = fuzzer.counterexamples[i]
            hit = to_ce(i, ce, found[i] if i < len(found) else (iteration, elapsed, name),
                        forward_at(ce.seed_input, int(ce.spec_row)))
        return FuzzFrame(iteration=iteration, elapsed_s=round(elapsed, 4), strategy=name,
                         seed_row=int(s.original_index[0]), depth=int(s.depth[0]) + 1, violation=violation,
                         input=_shown(x[0]), seed_input=_shown(s.original_tensor[0]), counterexample=hit)

    def keep_frame(fr: FuzzFrame) -> None:
        frames.append(fr)
        if len(frames) > FRAME_LIMIT:  # thin evenly, keeping the ends and violating frames
            frames[:] = [f for i, f in enumerate(frames) if i % 2 == 0 or f.violation or i == len(frames) - 1]
            if len(frames) > FRAME_LIMIT:
                del frames[1:-1:2]

    def point(iteration: int) -> FuzzProgress:
        return FuzzProgress(iteration=iteration, elapsed_s=round(time.time() - fuzzer.start_time, 4),
                            coverage=float(fuzzer.coverage_tracker.get_coverage()),
                            counterexamples=len(fuzzer.counterexamples), corpus=len(fuzzer.seed_corpus))

    def observe(iteration: int, final: bool = False) -> None:
        nonlocal done, ces_seen, last_point, last_emit, stopped
        if not stopped and should_stop is not None and should_stop():
            stopped = True
            fuzzer.config.timeout_seconds = 0.0  # ACT's loop checks its timeout before every iteration
        if iteration > done:
            strategy = fuzzer.mutation_engine.last_strategy
            name = str(strategy) if strategy is not None else "unknown"
            selected[name] = selected.get(name, 0) + 1
            new = len(fuzzer.counterexamples) - ces_seen
            violations[name] = violations.get(name, 0) + new
            elapsed = time.time() - fuzzer.start_time
            found.extend((iteration, elapsed, name) for _ in range(min(new, COUNTEREXAMPLE_LIMIT - len(found))))
            first_ce = ces_seen == 0 and new > 0
            hit = new > 0
            done, ces_seen = iteration, len(fuzzer.counterexamples)
        else:
            first_ce = hit = False
        now = time.monotonic()
        if final or first_ce or now - last_point >= TIMELINE_EVERY_S:
            p = point(iteration)
            last_point = now
            timeline.append(p)
            if len(timeline) > TIMELINE_LIMIT:
                del timeline[1:-1:2]
            if final or first_ce or now - last_emit >= PROGRESS_EVERY_S:
                last_emit = now
                fr = frame(iteration, hit) if not frames or frames[-1].iteration != iteration else None
                if fr is not None:
                    keep_frame(fr)
                    if on_frame:
                        on_frame(fr)
                if on_progress:
                    on_progress(p)

    fuzzer._print_progress = observe  # baseline seam, see module docstring
    report = fuzzer.fuzz()
    observe(report.total_iterations, final=True)

    kept = report.counterexamples[:COUNTEREXAMPLE_LIMIT]
    seed_outs = [forward_at(ce.seed_input, int(ce.spec_row)) for ce in kept]
    seed_rows = rows[:SEED_LIMIT]
    seeds = tuple(FuzzSeed(row=i, input=_shown(x), output=_floats(y))
                  for i, (x, y) in enumerate(zip(seed_rows, forward(rows)[:SEED_LIMIT], strict=True)))
    ces = tuple(to_ce(i, ce, found[i], seed_outs[i]) for i, ce in enumerate(kept))
    n = len(report.counterexamples)
    config: dict[str, object] = {
        "max_iterations": cfg.max_iterations, "timeout_seconds": cfg.timeout_seconds,
        "coverage_strategy": cfg.coverage_strategy, "activation_threshold": cfg.activation_threshold,
        "perturb_mode": cfg.perturb_mode, "perturb_scale": cfg.perturb_scale,
        "seed_selection_strategy": cfg.seed_selection_strategy, "pgd_restarts": cfg.pgd_restarts,
        "pgd_restarts_binarized": cfg.pgd_restarts_binarized,  # mutation weights: FuzzOutcome.strategies
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
        counterexamples=ces, seeds=seeds, frames=_dedupe_large_hits(frames, ces), timeline=tuple(timeline),
        strategies=tuple(FuzzStrategyStats(name=k, weight=weights.get(k, 0.0), selected=selected[k],
                                           violations=violations[k]) for k in selected),
        config=config, rng_seed=rng_seed, device=str(fuzzer.device), stopped=stopped,
    )
