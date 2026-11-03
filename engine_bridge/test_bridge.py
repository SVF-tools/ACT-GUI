"""Bridge parity tests against the real pinned ACT checkout (not synthetic fixtures).

Each expectation comes from a direct native ACT call or from fixtures/catalog.json,
which scripts/record_fixtures.py recorded from direct ACT calls.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import cast

import pytest

from engine_bridge.contracts import BridgeError, Method
from engine_bridge.engine_session import act_imports, act_root, probe, probe_gurobi
from engine_bridge.execution import run_fuzzing, run_verification
from engine_bridge.inspection import interval_layer_states
from engine_bridge.model_spec import describe_model

logging.disable(logging.WARNING)
CATALOG = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "catalog.json").read_text())
MODELS = {m["id"]: m for m in CATALOG["models"]}


def model_path(model_id: str) -> Path:
    return act_root() / MODELS[model_id]["act_path"]


def native_net(model_id: str):
    with act_imports():
        from act.back_end.serialization.serialization import load_net_from_file
        return load_net_from_file(str(model_path(model_id)))


def test_probe_reports_pinned_commit_and_unsupported_hooks():
    info = probe(CATALOG["act"]["commit"])
    assert info.usable and info.commit == CATALOG["act"]["commit"]
    caps = {c.name: c.availability for c in info.capabilities}
    assert caps["verify.bab"] == "available"
    assert caps["events.bab_nodes"] == "unsupported"


def test_probe_missing_act_is_a_deterministic_error(tmp_path):
    info = probe(CATALOG["act"]["commit"], root=tmp_path / "no-act")
    assert not info.usable
    assert [d.code for d in info.diagnostics] == ["act_missing"]
    assert all(c.availability == "unsupported" for c in info.capabilities)


def test_probe_version_mismatch_is_a_warning():
    info = probe("0" * 40)
    assert info.usable
    assert [d.code for d in info.diagnostics] == ["version_mismatch"]


@pytest.mark.parametrize("model_id", list(MODELS))
def test_description_matches_native_dag_and_is_stable(model_id):
    net = native_net(model_id)
    d1, d2 = describe_model(model_path(model_id)), describe_model(model_path(model_id))
    assert d1 == d2
    assert d1.sha256 == MODELS[model_id]["sha256"]
    assert [(l.layer_id, l.kind, l.in_vars, l.out_vars) for l in d1.layers] == \
        [(L.id, L.kind, len(L.in_vars), len(L.out_vars)) for L in net.layers]
    assert {l.layer_id: l.preds for l in d1.layers} == {L.id: tuple(net.preds.get(L.id, [])) for L in net.layers}
    # No mutable ACT/tensor object escapes: every leaf is a primitive.
    def leaves(x):
        if dataclasses.is_dataclass(x):
            for f in dataclasses.fields(x):
                yield from leaves(getattr(x, f.name))
        elif isinstance(x, (tuple, list)):
            for v in x:
                yield from leaves(v)
        else:
            yield x
    assert all(v is None or isinstance(v, (int, float, str, bool)) for v in leaves(d1))


def test_spec_mapping_matches_native_input_box_and_assert():
    net = native_net("bab_deep_mlp")
    d = describe_model(model_path("bab_deep_mlp"))
    spec = next(L for L in net.layers if L.kind == "INPUT_SPEC")
    assert d.input_specs[0].lb == tuple(spec.params["lb"].reshape(-1).tolist())
    assert d.input_specs[0].ub == tuple(spec.params["ub"].reshape(-1).tolist())
    assrt = next(L for L in net.layers if L.kind == "ASSERT")
    assert d.output_spec is not None
    assert d.output_spec.kind == assrt.params["kind"]
    assert d.output_spec.thresholds == tuple(assrt.params["thresholds"].reshape(-1).tolist())


@pytest.mark.parametrize("model_id,method", [(m["id"], meth) for m in CATALOG["models"] for meth in m["methods"]])
def test_run_verdict_matches_recorded_native_act(model_id, method):
    import torch

    out = run_verification(model_path(model_id), method, CATALOG["environment"]["bab_budget_s"])
    assert out.act_status == MODELS[model_id]["native"][method]["status"]
    assert out.device == ("cuda:0" if torch.cuda.is_available() else "cpu")


def test_interval_layer_states_match_native_verify_once_facts():
    with act_imports():
        from act.back_end.verifier import verify_once
        _, facts = verify_once(native_net("bab_deep_mlp"), collect_facts=True)
    states = interval_layer_states(model_path("bab_deep_mlp"))
    assert [s.layer_id for s in states.layers] == sorted(facts)
    for s in states.layers:
        assert s.lb == tuple(facts[s.layer_id].bounds.lb.reshape(-1).tolist())
        assert s.ub == tuple(facts[s.layer_id].bounds.ub.reshape(-1).tolist())


def test_fuzzing_reports_act_counterexample_inside_the_input_box():
    progress = []
    out = run_fuzzing(model_path("unsafe_linear"), 10.0, 1000, rng_seed=0, stop_on_first=True,
                      on_progress=progress.append)
    assert (out.verdict, out.act_status) == ("falsified", "COUNTEREXAMPLE_FOUND")
    assert out.counterexample_count == len(out.counterexamples) == 1
    ce = out.counterexamples[0]
    box = describe_model(model_path("unsafe_linear")).input_specs[0]
    assert all(lo <= x <= hi for x, lo, hi in zip(ce.input, box.lb, box.ub, strict=True))
    assert ce.iteration == out.iterations and ce.strategy in {s.name for s in out.strategies}
    assert out.seeds and out.seeds[0].row == 0 and len(out.seeds[0].input) == len(ce.input)
    assert len(ce.seed_output) == len(ce.output) == len(out.seeds[0].output)
    assert progress and progress[-1] == out.timeline[-1] and progress[-1].counterexamples == 1


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
    with pytest.raises(BridgeError) as e2:
        describe_model(tmp_path / "missing.json")
    assert e2.value.code == "model_not_found"
    with pytest.raises(BridgeError) as e3:
        run_fuzzing(model_path("bab_deep_mlp"), 5, 0)
    assert e3.value.code == "invalid_budget"


def test_gurobi_probe_reports_gurobi_license_rejection(tmp_path):
    lic = tmp_path / "gurobi.lic"
    lic.write_text("TYPE=ACADEMIC\nVERSION=13\nHOSTID=deadbeef\nUSERNAME=nobody\nKEY=ABCDEFGH\n")
    status = probe_gurobi(lic)
    if status.license_state == "not_installed":
        pytest.skip("gurobipy is not installed in this environment")
    assert status.license_state == "invalid" and "HostID mismatch" in status.message
    assert status.version is not None
    missing = probe_gurobi(tmp_path / "absent.lic")
    assert missing.license_state == "invalid" and "absent.lic" in missing.message
