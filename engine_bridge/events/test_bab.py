"""BaB tree sink: synthetic record copies, and native ACT parity on checkouts with act.pipeline.gui.bab_gui."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass, replace

import pytest

from engine_bridge.contracts import (BabBranch, BabInterval, BabLayerBounds, BabPhase, BabTerminal, BabWave,
                                     LayerDescription, ModelDescription)
from engine_bridge.engine_session import act_imports
from engine_bridge.engine_session.parity import capability_available
from engine_bridge.events import BabTreeSink, run_observed_bab
from engine_bridge.execution import run_verification
from engine_bridge.model_spec.describe import describe_model
from engine_bridge.testing import model_path


@dataclass(frozen=True)
class BaBWave:  # stand-ins named like ACT's records, carrying the fields ACT emits
    seq: int
    wave: int
    nodes: tuple[Mapping[str, object], ...]
    children: tuple[Mapping[str, object], ...]
    frontier_size: int
    evicted_node_ids: tuple[int, ...]
    t_ns: int = 0


@dataclass(frozen=True)
class BaBTerminal:
    seq: int
    wave: int
    status: str
    reason: str
    frontier_size: int
    node_id: int | None = None
    parent_id: int | None = None
    depth: int | None = None
    t_ns: int = 0


def _layer(layer_id: int, kind: str, preds: tuple[int, ...], width: int) -> LayerDescription:
    return LayerDescription(layer_id, kind, width, width, (1, width), preds, (), ())


MODEL = ModelDescription("net.json", "0" * 64, (_layer(0, "INPUT", (), 2), _layer(1, "DENSE", (0,), 3),
                                                 _layer(2, "RELU", (1,), 3), _layer(3, "DENSE", (2,), 1)),
                         (), None, 2, 1)


def _node(node_id: int, outcome: str, bound: float, **extra: object) -> dict[str, object]:
    return {"node_id": node_id, "parent_id": -1 if node_id == 0 else 0, "depth": 0 if node_id == 0 else 1,
            "solve_status": "SAT", "resolved_by_main_solver": False, "outcome": outcome, "bound": bound,
            "bound_kind": "certified_node_lower_bound", "layer_bounds": None, "layer_bound_summary": None, **extra}


def test_sink_copies_waves_with_split_decisions_and_relu_stability():
    records: list[object] = []
    sink = BabTreeSink(records.append, MODEL, start_ns=0)
    bounds = {1: {"lb": [-1.0, 0.5, -2.0], "ub": [1.0, 2.0, -0.5]}, 2: {"lb": [0.0, 0.5, 0.0], "ub": [1.0, 2.0, 0.0]}}
    summary = {1: {"lb_min": -2.0, "ub_max": 2.0, "neuron_count": 3}}
    root = _node(0, "branched", float("-inf"), layer_bounds=bounds, layer_bound_summary=summary)
    children = (
        {"node_id": 1, "parent_id": 0, "depth": 1, "frontier_state": "pending", "branch": {"kind": "neuron", "phases": [
            {"layer_id": 2, "spec_row": 1, "neuron": 0, "sign": 1}, {"layer_id": 2, "spec_row": 0, "neuron": 0, "sign": 1}]}},
        {"node_id": 2, "parent_id": 0, "depth": 1, "frontier_state": "evicted",
         "branch": {"kind": "input_axis", "intervals": [{"axis": 1, "lb": 0.0, "ub": float("inf")}]}},
    )
    sink(BaBWave(1, 1, (root,), children, 1, (), t_ns=2_000_000))
    sink(object())  # other producers on the shared channel are not BaB records
    sink(BaBTerminal(2, 1, "UNKNOWN", "budget_exhausted_with_unproven_subboxes", 1, t_ns=3_000_000))

    wave, end = records
    assert isinstance(wave, BabWave) and isinstance(end, BabTerminal) and sink.ignored_records == 0
    assert wave.t_ms == 2.0 and wave.frontier_size == 1
    node = wave.nodes[0]
    assert (node.node_id, node.parent_id, node.outcome, node.bound) == (0, -1, "branched", None)
    assert node.layers == (
        BabLayerBounds(1, "DENSE", 3, -2.0, 2.0),  # ACT's own summary wins over the copied bounds
        BabLayerBounds(2, "RELU", 3, 0.0, 2.0, active=1, inactive=1, unstable=1),  # from layer 1, its input
    )
    assert wave.children[0].branch == BabBranch("neuron", phases=(BabPhase(2, 0, 1, (0, 1)),))
    assert wave.children[1].branch == BabBranch("input_axis", intervals=(BabInterval(1, 0.0, None),))
    assert wave.children[1].frontier_state == "evicted"
    assert (end.status, end.node_id, end.t_ms) == ("UNKNOWN", None, 3.0)


def test_sink_counts_malformed_records_and_keeps_callback_failures_out_of_act():
    def fail(_: object) -> None:
        raise OSError("disk full")

    sink = BabTreeSink(fail)
    sink(BaBWave(1, 1, ({"node_id": 0},), (), 0, ()))  # a node without ACT's fields
    assert sink.ignored_records == 1 and sink.callback_error is None
    sink(BaBTerminal(2, 1, "CERTIFIED", "all_resolved_unsat", 0))
    sink(BaBTerminal(3, 1, "CERTIFIED", "all_resolved_unsat", 0))
    assert isinstance(sink.callback_error, OSError) and sink.ignored_records == 1


@pytest.fixture
def bab_records():
    if not capability_available("events.bab_nodes"):
        pytest.skip("ACT checkout has no act.pipeline.gui.bab_gui; run with ACT_CODE_ROOT at SVF-tools/ACT main >= 22693fb")


@pytest.mark.parametrize("model_id, status, terminal_node", [("bab_deep_mlp", "CERTIFIED", None),
                                                               ("unsafe_linear", "FALSIFIED", 0)])
def test_observed_bab_reports_acts_verdict_and_terminal(bab_records, model_id, status, terminal_node):
    records: list[BabWave | BabTerminal] = []
    outcome, sink = run_observed_bab(model_path(model_id), 15.0, records.append)
    assert outcome.act_status == run_verification(model_path(model_id), "bab", 15.0).act_status == status
    assert sink.ignored_records == 0 and sink.callback_error is None
    assert [r.seq for r in records] == list(range(1, len(records) + 1))
    end = records[-1]
    assert isinstance(end, BabTerminal) and end.status == status and end.node_id == terminal_node


def test_multi_wave_search_links_every_child_to_a_node_solved_in_its_wave(bab_records):
    path = model_path("bab_deep_mlp")
    with act_imports():
        import torch
        from act.back_end.bab.bab import verify_bab_batched
        from act.back_end.serialization.serialization import load_net_from_file
        from act.back_end.solver.solver_torchlp import TorchLPSolver
        from act.config.config import PipelineConfig
        from act.pipeline.gui.act_gui import observe

        pipeline = PipelineConfig.from_yaml()
        config = replace(pipeline.bab, solver_tier="dual", bounding="random", max_nodes=12, max_depth=6)

        def search(sink: BabTreeSink | None = None):
            torch.manual_seed(0)
            with observe(sink) if sink else nullcontext():
                return verify_bab_batched(load_net_from_file(str(path)), TorchLPSolver, config, max_batch_size=2,
                                          time_budget_s=20.0, dual_config=pipeline.dual)

        plain = search()
        records: list[BabWave | BabTerminal] = []
        observed = search(BabTreeSink(records.append, describe_model(path)))
    assert observed.status == plain.status and observed.metadata.get("nodes") == plain.metadata.get("nodes")
    waves = [r for r in records if isinstance(r, BabWave)]
    assert len(waves) >= 2 and isinstance(records[-1], BabTerminal)
    known = {0}
    for wave in waves:
        solved = {n.node_id for n in wave.nodes}
        assert solved <= known
        for child in wave.children:
            assert child.parent_id in solved and child.node_id not in known
            known.add(child.node_id)
    relu = [layer for wave in waves for node in wave.nodes for layer in node.layers if layer.kind == "RELU"]
    assert relu and all(sum(c or 0 for c in (layer.active, layer.inactive, layer.unstable)) == layer.neurons
                        and layer.unstable is not None for layer in relu)
