"""Native ACT fuzz control tests; optional on the pinned baseline without act.pipeline.gui.fuzzer_gui."""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from engine_bridge.contracts import BridgeError
from engine_bridge.engine_session import act_code_root
from engine_bridge.execution import FuzzRunControl, fuzzing_options, run_fuzzing
from engine_bridge.execution import fuzz
from engine_bridge.testing import model_path


@pytest.fixture
def native_net():
    if not fuzz._control_available():
        pytest.skip("ACT checkout has no fuzz.control API; run with ACT_CODE_ROOT=act-gui-match")
    return act_code_root() / "act/back_end/examples/nets/layer_testing_sub.json"


def test_options_match_native_metadata_and_defaults(native_net):
    from act.pipeline.gui.fuzzer_gui import fuzzing_options as native_options

    options = fuzzing_options()
    assert [o.name for o in options] == [o.option.name for o in native_options()]
    assert {o.name: o.default for o in options} == {o.option.name: o.default for o in native_options()}
    assert next(o for o in options if o.name == "perturb_scale").live
    assert not next(o for o in options if o.name == "coverage_strategy").live


@pytest.mark.parametrize("counterexamples", [False, True])
def test_public_observation_equals_legacy_for_fixed_seed(native_net, monkeypatch, counterexamples):
    path = model_path("unsafe_linear") if counterexamples else native_net
    observed = run_fuzzing(path, 30, 20, rng_seed=7)
    with monkeypatch.context() as legacy:
        legacy.setattr(fuzz, "_control_available", lambda: False)
        previous = run_fuzzing(path, 30, 20, rng_seed=7)
    assert observed.iterations == previous.iterations == 20
    assert observed.counterexample_count == previous.counterexample_count
    assert [c.input for c in observed.counterexamples] == [c.input for c in previous.counterexamples]
    assert observed.stop_reason == previous.stop_reason == "max_iterations"
    if counterexamples:
        assert observed.counterexample_count > 0


def test_update_applies_at_next_batch_and_reports_native_receipt(native_net):
    control, changes = FuzzRunControl(), []

    def progress(point):
        if point.iteration == 1:
            assert control.update({"perturb_scale": 0.2, "mutation_weights": {"random": 1}}) == {
                "perturb_scale": 0.2, "mutation_weights": {"random": 1.0}}

    out = run_fuzzing(native_net, 30, 5, control=control, on_progress=progress, on_control=changes.append)
    assert len(changes) == 1 and changes[0].iteration == 1 and changes[0].rejected == ""
    assert changes[0].requested == changes[0].applied
    assert out.config["perturb_scale"] == 0.2
    assert next(s for s in out.strategies if s.name == "random").selected >= 4
    assert out.stop_reason == "max_iterations"


@pytest.mark.parametrize("finish", ["resume", "stop"])
def test_pause_update_then_resume_or_stop(native_net, finish):
    control, applied, changes = FuzzRunControl(), threading.Event(), []
    control.pause()
    control.update({"max_iterations": 3, "perturb_scale": 0.3})

    def receipt(change):
        changes.append(change)
        applied.set()

    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(run_fuzzing, native_net, 30, 100, control=control, on_control=receipt)
        try:
            assert applied.wait(10), "ACT did not apply the update while paused"
            assert changes[0].iteration == 0 and changes[0].applied["max_iterations"] == 3
            assert not result.done(), "ACT must not fuzz a batch while paused"
            if finish == "resume":
                control.resume()
            else:
                control.request_stop()
            out = result.result(timeout=10)
        finally:
            control.request_stop()
    assert out.iterations == (3 if finish == "resume" else 0)
    assert out.stop_reason == ("max_iterations" if finish == "resume" else "stopped")
    assert out.stopped == (finish == "stop")


def test_timeout_and_first_violation_stop_reasons(native_net):
    timeout = run_fuzzing(native_net, 1e-9, 100)
    assert timeout.stop_reason == "timeout" and not timeout.stopped
    violation = run_fuzzing(model_path("unsafe_linear"), 30, 1000, rng_seed=0, stop_on_first=True)
    assert violation.stop_reason == "first_violation" and violation.counterexample_count == 1


@pytest.mark.parametrize("changes", [
    {"coverage_strategy": "BestInputCov"}, {"perturb_scale": 0}, {"perturb_scale": 2},
    {"max_iterations": 0}, {"pgd_restarts": 1.5}, {"mutation_weights": {"random": 0}},
    {"unknown": 1},
])
def test_live_validation_uses_native_act(native_net, changes):
    with pytest.raises(BridgeError) as exc:
        FuzzRunControl().update(changes)
    assert exc.value.code == "invalid_options"


def test_legacy_options_disable_controls_but_stop_remains_available(monkeypatch):
    monkeypatch.setattr(fuzz, "_control_available", lambda: False)
    options = fuzzing_options()
    assert {o.name for o in options} == fuzz.TUNABLE
    assert not any(o.live for o in options)
    assert {o.name: o.default for o in options} == fuzz.fuzzing_defaults()
    control = FuzzRunControl()
    for command in (control.pause, control.resume, lambda: control.update({"perturb_scale": 0.2})):
        with pytest.raises(BridgeError) as exc:
            command()
        assert exc.value.code == "capability_unavailable"
    control.request_stop()
    assert control.stop_requested
