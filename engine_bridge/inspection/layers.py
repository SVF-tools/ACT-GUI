"""Read per-layer interval states for a fixed model/spec snapshot (INSP-01, first version).

ACT's interval analysis produces an 'after' Fact per layer; a layer's 'before'
state is the 'after' state of its predecessor(s) in the DAG, so it is referenced
by layer id rather than copied. Bounds are ACT's numbers, unchanged.
"""
from __future__ import annotations

from pathlib import Path

from engine_bridge.contracts import BridgeError, LayerState, LayerStates
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec.describe import load_net

MAX_VALUES_PER_LAYER = 65536


def interval_layer_states(model_path: Path) -> LayerStates:
    net = load_net(model_path)
    with act_imports():
        from act.back_end.analyze import analyze
        from act.back_end.core import ConSet, Fact
        from act.back_end.transfer_functions import set_solver_mode, set_transfer_function_mode
        from act.back_end.verifier import (
            _setup_verify_context, add_all_input_specs, find_entry_layer_id, get_input_ids,
        )

        # Explicit, not ensure_active_tf: a hybridz run in this process must not leak its TF into interval states.
        set_solver_mode(None)
        set_transfer_function_mode("interval")
        spec_layers, seed_bounds, batch = _setup_verify_context(net)
        if batch != 1:
            raise BridgeError("unsupported_batch", f"Layer inspection supports one input lane; spec has {batch}")
        entry_fact = Fact(bounds=seed_bounds, cons=ConSet())
        add_all_input_specs(entry_fact.cons, get_input_ids(net), spec_layers)
        _before, after, _cons = analyze(net, find_entry_layer_id(net), entry_fact)
    states = []
    for layer in net.layers:
        fact = after.get(layer.id)
        if fact is None:
            continue  # ACT produced no state for this layer; caller reports it as not_recorded
        lb, ub = fact.bounds.lb, fact.bounds.ub
        if lb.numel() > MAX_VALUES_PER_LAYER:
            raise BridgeError("too_large", f"Layer {layer.id} has {lb.numel()} values; paging not implemented")
        shape = tuple(int(s) for s in lb.shape[1:]) if lb.dim() > 1 else tuple(int(s) for s in lb.shape)
        states.append(LayerState(
            layer_id=int(layer.id), kind=str(layer.kind), stage="after",
            lb=tuple(float(v) for v in lb.reshape(-1).tolist()),
            ub=tuple(float(v) for v in ub.reshape(-1).tolist()),
            shape=shape, before_layer_ids=tuple(int(p) for p in net.preds.get(layer.id, [])),
        ))
    return LayerStates(method="interval", availability="available", layers=tuple(states),
                       provenance={"act_call": "act.back_end.analyze.analyze", "transfer_function": "interval"})
