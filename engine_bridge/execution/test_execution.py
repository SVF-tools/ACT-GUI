"""Verification and fuzzing invocation parity tests against native ACT.

Expectations come from direct native ACT calls or from fixtures/catalog.json (recorded by
scripts/record_fixtures.py from direct ACT calls); no synthetic fixtures.
"""
from __future__ import annotations

from typing import Any, cast

import pytest

from engine_bridge.contracts import BridgeError, Domain, Method
from engine_bridge.engine_session import act_imports
from engine_bridge.execution import run_fuzzing, run_verification
from engine_bridge.model_spec import describe_model
from engine_bridge.testing import CATALOG, MODELS, model_path, native_net


@pytest.mark.parametrize("model_id,method", [(m["id"], meth) for m in CATALOG["models"] for meth in m["methods"]])
def test_run_verdict_matches_recorded_native_act(model_id, method):
    import torch

    out = run_verification(model_path(model_id), method, CATALOG["environment"]["bab_budget_s"])
    assert out.act_status == MODELS[model_id]["native"][method]["status"]
    assert out.device == ("cuda:0" if torch.cuda.is_available() else "cpu")

def native_domain_status(model_id: str, domain: str) -> str:
    """Direct ACT call with the solver/TF selection of act/config/pipeline_cli.py."""
    with act_imports():
        from act.back_end.transfer_functions import set_solver_mode, set_transfer_function_mode
        from act.back_end.verifier import verify_once
        from act.config.config import BackendConfig

        set_solver_mode(None if domain == "interval" else domain)
        set_transfer_function_mode("hybridz" if domain == "hybridz" else "interval",
                                   BackendConfig.from_yaml().hybridz if domain == "hybridz" else None)
        kw: dict[str, Any] = {"timelimit": 30.0, "hybridz_tolerance": 1e-7} if domain == "hybridz" else {}
        status = verify_once(native_net(model_id), **kw)[0].status.name
        set_solver_mode(None)
        set_transfer_function_mode("interval")
        return status

@pytest.mark.parametrize("model_id", ["bab_deep_mlp", "unsafe_linear", "mnist_relu_6_100"])
@pytest.mark.parametrize("domain", ["interval", "dual", "hybridz"])
def test_domain_verdict_matches_native_verify_once(model_id, domain):
    out = run_verification(model_path(model_id), "interval", 30.0, domain=domain)
    assert out.domain == domain
    assert out.act_status == native_domain_status(model_id, domain)

def test_domains_reach_act_verdicts_interval_cannot():
    # Recorded native statuses: interval is UNKNOWN on both; dual / hybridz decide them.
    assert run_verification(model_path("mnist_relu_6_100"), "interval", 30.0, domain="dual").verdict == "certified"
    assert run_verification(model_path("bab_deep_mlp"), "interval", 30.0, domain="hybridz").verdict == "certified"

def test_fuzzing_reports_act_counterexample_inside_the_input_box():
    progress, live = [], []
    out = run_fuzzing(model_path("unsafe_linear"), 10.0, 1000, rng_seed=0, stop_on_first=True,
                      on_progress=progress.append, on_frame=live.append)
    assert (out.verdict, out.act_status) == ("falsified", "COUNTEREXAMPLE_FOUND")
    assert out.counterexample_count == len(out.counterexamples) == 1
    ce = out.counterexamples[0]
    box = describe_model(model_path("unsafe_linear")).input_specs[0]
    assert all(lo <= x <= hi for x, lo, hi in zip(ce.input, box.lb, box.ub, strict=True))
    assert ce.iteration == out.iterations and ce.strategy in {s.name for s in out.strategies}
    assert out.seeds and out.seeds[0].row == 0 and len(out.seeds[0].input) == len(ce.input)
    assert len(ce.seed_output) == len(ce.output) == len(out.seeds[0].output)
    assert progress and progress[-1] == out.timeline[-1] and progress[-1].counterexamples == 1
    # Frames: the mutated batch of the violating iteration is ACT's counterexample input.
    assert live and live[-1] == out.frames[-1] and out.frames[-1].violation
    assert out.frames[-1].input == ce.input and out.frames[-1].seed_input == out.seeds[0].input
    hit = out.frames[-1].counterexample  # ACT's own counterexample rides on the violating frame
    assert hit is not None and (hit.index, hit.iteration, hit.input, hit.seed_input) == (0, ce.iteration, ce.input, ce.seed_input)
    assert not out.stopped
    assert all(lo <= x <= hi for f in out.frames for x, lo, hi in zip(f.input, box.lb, box.ub, strict=True))

def test_fuzzing_stop_request_ends_act_loop_with_a_report():
    out = run_fuzzing(model_path("bab_deep_mlp"), 60.0, 200, rng_seed=0, should_stop=lambda: True)
    assert out.stopped and out.verdict == "unknown"
    assert 1 <= out.iterations < 200 and out.timeline[-1].iteration == out.iterations

def test_fuzzing_never_falsifies_a_property_act_certifies():
    assert MODELS["bab_deep_mlp"]["native"]["bab"]["status"] == "CERTIFIED"
    out = run_fuzzing(model_path("bab_deep_mlp"), 60.0, 200, rng_seed=0)
    assert (out.verdict, out.iterations, out.counterexample_count) == ("unknown", 200, 0)
    assert sum(s.selected for s in out.strategies) == out.iterations  # batch size 1: one strategy per sample
    iters = [p.iteration for p in out.timeline]
    assert iters == sorted(iters) and iters[-1] == 200

def test_invalid_inputs_raise_structured_errors(tmp_path):
    with pytest.raises(BridgeError) as e1:
        run_verification(model_path("bab_deep_mlp"), cast(Method, cast(object, "magic")), 5)
    assert e1.value.code == "unsupported_method"
    with pytest.raises(BridgeError) as e4:
        run_verification(model_path("bab_deep_mlp"), "interval", 5, domain=cast(Domain, cast(object, "zonotope")))
    assert e4.value.code == "unsupported_domain"
    with pytest.raises(BridgeError) as e2:
        describe_model(tmp_path / "missing.json")
    assert e2.value.code == "model_not_found"
    with pytest.raises(BridgeError) as e3:
        run_fuzzing(model_path("bab_deep_mlp"), 5, 0)
    assert e3.value.code == "invalid_budget"
    with pytest.raises(BridgeError) as e5:
        run_fuzzing(model_path("bab_deep_mlp"), 5, 10, hyperparameters={"output_dir": "/tmp"})
    assert e5.value.code == "invalid_options"
    with pytest.raises(BridgeError) as e6:
        run_fuzzing(model_path("bab_deep_mlp"), 5, 10, hyperparameters={"perturb_mode": "huge"})
    assert e6.value.code == "invalid_options"
