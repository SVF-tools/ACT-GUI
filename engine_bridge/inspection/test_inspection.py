"""Layer-state inspection parity tests against native ACT verify_once facts.

Expectations come from direct native ACT calls or from fixtures/catalog.json (recorded by
scripts/record_fixtures.py from direct ACT calls); no synthetic fixtures.
"""
from __future__ import annotations

from engine_bridge.engine_session import act_imports
from engine_bridge.execution import run_verification
from engine_bridge.inspection import interval_layer_states
from engine_bridge.testing import model_path, native_net


def test_layer_states_stay_interval_after_a_hybridz_run():
    run_verification(model_path("bab_deep_mlp"), "interval", 30.0, domain="hybridz")  # same process as the worker
    test_interval_layer_states_match_native_verify_once_facts()

def test_interval_layer_states_match_native_verify_once_facts():
    with act_imports():
        from act.back_end.transfer_functions import set_solver_mode, set_transfer_function_mode
        from act.back_end.verifier import verify_once
        set_solver_mode(None)
        set_transfer_function_mode("interval")
        _, facts = verify_once(native_net("bab_deep_mlp"), collect_facts=True)
    states = interval_layer_states(model_path("bab_deep_mlp"))
    assert [s.layer_id for s in states.layers] == sorted(facts)
    for s in states.layers:
        assert s.lb == tuple(facts[s.layer_id].bounds.lb.reshape(-1).tolist())
        assert s.ub == tuple(facts[s.layer_id].bounds.ub.reshape(-1).tolist())
