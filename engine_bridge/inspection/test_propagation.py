"""Synthetic record-copy tests and separately gated native ACT parity."""
from __future__ import annotations

import time
from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch

from engine_bridge.engine_session import act_imports
from engine_bridge.engine_session.parity import _check, requirements
from engine_bridge.execution.verify import run_verification, select_domain
from engine_bridge.inspection.propagation import PropagationSink, run_observed_verification
from engine_bridge.inspection.testing import observation_api
from engine_bridge.testing import model_path, native_net
from engine_bridge.contracts import LayerDescription, ModelDescription
from engine_bridge.model_spec.describe import _output_shape


def test_sink_copies_full_tensors_identity_relaxations_and_final_versions():
    obs = observation_api()
    records = []
    start = time.perf_counter_ns()
    sink = PropagationSink(records.append, start_ns=start)
    key = obs.RecordKey("dual", "forward", 3, stage="pre", version=2, scope="child", parent="root", origin="inherited")
    lb = torch.tensor([[-2., 0., 1.]], dtype=torch.float64)
    ub = torch.tensor([[3., 0., 2.]], dtype=torch.float64)
    with obs.observe(sink):
        obs.emit(obs.PhaseEvent("verify_once", "start", t_ns=start))
        obs.emit(obs.LayerBounds(key, "RELU", lb, ub, t_ns=start + 1_000_000))
        obs.emit(obs.Relaxation(key, torch.tensor([[-1, 0, 1]], dtype=torch.int8), "linear",
                                lower_slope=torch.zeros_like(lb), upper_slope=torch.ones_like(lb),
                                extra={"generators": torch.ones_like(lb), "note": "synthetic"}))
        obs.emit(obs.DualBackward(replace(key, pass_="backward"), lb[:, None, :], False, nu=ub))
        obs.emit(obs.SpecBound(replace(key, layer_id=9, pass_="backward"), lb, ub, 0, "n_iters"))
        obs.emit(object())
        obs.emit(obs.LayerBounds(replace(key, version=1), "RELU", ub, ub, t_ns=start))
    lb.fill_(99)
    assert sink.wants_relaxation and sink.ignored_records == 1
    bound = records[1]
    assert bound.key.parent == "root" and bound.key.origin == "inherited" and bound.t_ms == 1
    assert bound.tensors["lb"].values() == (-2., 0., 1.)
    assert bound.tensors["lb"].dtype == "float32" and bound.tensors["lb"].shape == (1, 3)
    assert records[2].counts == {"n_active": 1, "n_inactive": 1, "n_unstable": 1}
    assert records[3].tensors["alpha"].shape == (1, 1, 3)
    assert records[3].metadata["alpha_optimized"] is False
    assert next(iter(sink.final_bounds.values())).key.version == 2
    assert sink.layer_states("dual").layers == ()  # child scope is never substituted for root


def test_sink_isolates_malformed_records_and_callback_failures():
    obs = observation_api()
    def fail(_):
        raise OSError("synthetic storage failure")
    sink = PropagationSink(fail)
    with obs.observe(sink):
        obs.emit(obs.LayerBounds(obs.RecordKey("interval", "forward", 1), "LINEAR", None, None, t_ns=0))
        obs.emit(obs.PhaseEvent("verify_once", "start"))
    assert sink.ignored_records == 1
    assert isinstance(sink.callback_error, OSError)


def test_output_shape_preserves_convolution_axes_without_batch():
    obs = observation_api()
    shape = _output_shape(SimpleNamespace(params={"output_shape": [2, 3, 4, 5]}))
    layer = LayerDescription(3, "CONV2D", 60, 60, shape, (), (), ())
    assertion = LayerDescription(9, "ASSERT", 5, 5, None, (), (), ())
    model = ModelDescription("synthetic", "synthetic", (layer, assertion), (), None, 60, 5)
    records = []
    sink = PropagationSink(records.append, model)
    with obs.observe(sink):
        obs.emit(obs.LayerBounds(obs.RecordKey("interval", "forward", 3), "CONV2D", torch.zeros(2, 60),
                                torch.ones(2, 60)))
        obs.emit(obs.SpecBound(obs.RecordKey("dual", "backward", 9), torch.ones(2, 3), torch.ones(2), 0, "n_iters"))
    assert records[0].output_shape == (3, 4, 5)
    assert records[0].tensors["lb"].shape == (2, 60)
    assert records[1].output_shape == (5,)  # specification rows are not output neurons


def require_observer():
    with act_imports():
        problems = [_check(r) for r in requirements()["observe.propagation"]]
    if any(problems):
        pytest.skip("active ACT lacks observe.propagation")


@pytest.mark.parametrize("domain", ["interval", "hybridz", "dual"])
def test_real_act_observed_verdict_and_final_domain_bounds(domain):
    require_observer()
    records = []
    expected = run_verification(model_path("bab_deep_mlp"), "interval", 30, domain)
    actual, sink = run_observed_verification(model_path("bab_deep_mlp"), 30, domain, records.append)
    assert actual.verdict == expected.verdict and actual.act_status == expected.act_status
    assert records and sink.ignored_records == 0
    assert {r.key.domain for r in records if r.key} == {domain}
    assert sink.layer_states(domain).method == domain
    assert sink.layer_states(domain).layers
    with act_imports():
        from act.back_end.verifier import verify_once
        select_domain(domain)
        _, facts = verify_once(native_net("bab_deep_mlp"), collect_facts=True)
    if domain != "dual":
        for record in sink.final_bounds.values():
            if record.key.stage != "out":
                continue
            fact = facts[record.key.layer_id]
            assert record.tensors["lb"].values() == tuple(fact.bounds.lb.float().reshape(-1).tolist())
            assert record.tensors["ub"].values() == tuple(fact.bounds.ub.float().reshape(-1).tolist())
    else:
        assert any(r.kind == "DualBackward" for r in records)
        assert any(r.kind == "SpecBound" for r in records)
        assert any(r.key and r.key.stage == "pre" for r in records)
        assert sink.layer_states(domain).provenance["bounds"] == "forward pre-activation bounds"
