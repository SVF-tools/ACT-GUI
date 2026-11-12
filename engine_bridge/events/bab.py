"""Copy ACT's committed BaB waves while verify_bab_batched runs (EVT-02); no ACT object escapes the bridge.

ACT (act.pipeline.gui.bab_gui) emits one BaBWave per committed wave (the nodes it solved, the children it queued, the
frontier after the wave) and one BaBTerminal when the search ends, through the shared observation channel. The sink
copies them into the neutral contracts and reduces ACT's per-neuron node bounds to per-layer ranges and ReLU stability
counts. Other records on the channel (the propagation records of BaB's bounding passes) are not BaB search records
and are skipped.
"""
from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from engine_bridge.contracts import (BabBranch, BabChild, BabInterval, BabLayerBounds, BabNodeResult, BabPhase,
                                     BabTerminal, BabWave, ModelDescription, RunOutcome)
from engine_bridge.engine_session import act_imports
from engine_bridge.execution.verify import run_verification
from engine_bridge.model_spec.describe import describe_model

BabRecord = BabWave | BabTerminal


def _finite(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


class BabTreeSink:
    """Copy BaB search records synchronously; malformed ones are counted, never raised into ACT.

    A callback failure stops further copying and is kept in callback_error for the caller to report after the run,
    since ACT detaches a raising sink and the search itself must not be affected.
    """

    def __init__(self, callback: Callable[[BabRecord], None], model: ModelDescription | None = None,
                 start_ns: int | None = None) -> None:
        self.callback = callback
        self.start_ns = time.perf_counter_ns() if start_ns is None else start_ns
        self.ignored_records = 0
        self.callback_error: Exception | None = None
        layers = model.layers if model else ()
        self._kinds = {layer.layer_id: layer.kind for layer in layers}
        # A ReLU's split decision is about its input: the output bounds of its single predecessor.
        self._relu_inputs = {layer.layer_id: layer.preds[0] for layer in layers
                             if layer.kind == "RELU" and len(layer.preds) == 1}

    def __call__(self, record: Any) -> None:
        kind = type(record).__name__
        if kind not in ("BaBWave", "BaBTerminal") or self.callback_error is not None:
            return
        try:
            copied = self._wave(record) if kind == "BaBWave" else self._terminal(record)
        except (AttributeError, KeyError, TypeError, ValueError):
            self.ignored_records += 1
            return
        try:
            self.callback(copied)
        except Exception as exc:
            self.callback_error = exc

    def _t_ms(self, record: Any) -> float:
        now = getattr(record, "t_ns", None) or time.perf_counter_ns()
        return max(0.0, (now - self.start_ns) / 1_000_000)

    def _wave(self, record: Any) -> BabWave:
        return BabWave(seq=int(record.seq), wave=int(record.wave), t_ms=self._t_ms(record),
                       nodes=tuple(self._node(n) for n in record.nodes),
                       children=tuple(self._child(c) for c in record.children),
                       frontier_size=int(record.frontier_size),
                       evicted_node_ids=tuple(int(i) for i in record.evicted_node_ids))

    def _terminal(self, record: Any) -> BabTerminal:
        def optional(value: Any) -> int | None:
            return None if value is None else int(value)

        return BabTerminal(seq=int(record.seq), wave=int(record.wave), t_ms=self._t_ms(record),
                           status=str(record.status), reason=str(record.reason),
                           frontier_size=int(record.frontier_size), node_id=optional(record.node_id),
                           parent_id=optional(record.parent_id), depth=optional(record.depth))

    def _node(self, node: Mapping[str, Any]) -> BabNodeResult:
        return BabNodeResult(node_id=int(node["node_id"]), parent_id=int(node["parent_id"]), depth=int(node["depth"]),
                             solve_status=str(node["solve_status"]), outcome=str(node["outcome"]),
                             bound=_finite(node["bound"]), bound_kind=str(node["bound_kind"]),
                             layers=self._layers(node.get("layer_bounds"), node.get("layer_bound_summary")))

    def _layers(self, bounds: Mapping[int, Mapping[str, Any]] | None,
                summary: Mapping[int, Mapping[str, Any]] | None) -> tuple[BabLayerBounds, ...]:
        bounds, summary = bounds or {}, summary or {}
        out = []
        for layer_id in sorted({int(k) for k in (*bounds, *summary)}):
            own = summary.get(layer_id)
            if own is not None:  # ACT's own reduction of this layer's bounds
                neurons, lb_min, ub_max = int(own["neuron_count"]), _finite(own["lb_min"]), _finite(own["ub_max"])
            else:
                lb, ub = bounds[layer_id]["lb"], bounds[layer_id]["ub"]
                neurons = len(lb)
                lb_min = _finite(min(lb)) if lb and all(map(math.isfinite, lb)) else None
                ub_max = _finite(max(ub)) if ub and all(map(math.isfinite, ub)) else None
            stability: dict[str, int] = {}
            source = bounds.get(self._relu_inputs[layer_id]) if layer_id in self._relu_inputs else None
            if source is not None:
                active = [lo >= 0 for lo in source["lb"]]
                inactive = [not a and hi <= 0 for a, hi in zip(active, source["ub"])]
                stability = {"active": sum(active), "inactive": sum(inactive),
                             "unstable": len(active) - sum(active) - sum(inactive)}
            out.append(BabLayerBounds(layer_id=layer_id, kind=self._kinds.get(layer_id), neurons=neurons,
                                      lb_min=lb_min, ub_max=ub_max, **stability))
        return tuple(out)

    @staticmethod
    def _child(child: Mapping[str, Any]) -> BabChild:
        branch = child["branch"]
        phases: dict[tuple[int, int, int], list[int]] = {}
        for phase in branch.get("phases", ()):  # ACT lists a phase once per property row it applies to
            key = (int(phase["layer_id"]), int(phase["neuron"]), int(phase["sign"]))
            phases.setdefault(key, []).append(int(phase.get("spec_row", 0)))
        return BabChild(node_id=int(child["node_id"]), parent_id=int(child["parent_id"]), depth=int(child["depth"]),
                        branch=BabBranch(kind=str(branch["kind"]),
                                         phases=tuple(BabPhase(lid, neuron, sign, tuple(sorted(rows)))
                                                      for (lid, neuron, sign), rows in phases.items()),
                                         intervals=tuple(BabInterval(int(i["axis"]), _finite(i["lb"]), _finite(i["ub"]))
                                                         for i in branch.get("intervals", ()))),
                        frontier_state=str(child["frontier_state"]))


def run_observed_bab(model_path: Path, time_budget_s: float, callback: Callable[[BabRecord], None],
                     start_ns: int | None = None,
                     bab: Mapping[str, object] | None = None) -> tuple[RunOutcome, BabTreeSink]:
    """verify_bab_batched exactly as run_verification(method="bab", bab=bab) runs it, observed by a BabTreeSink."""
    sink = BabTreeSink(callback, describe_model(model_path), start_ns)
    with act_imports():
        from act.pipeline.gui.act_gui import observe

        with observe(sink):
            outcome = run_verification(model_path, "bab", time_budget_s, bab=bab)
    return outcome, sink
