"""Bridge parity tests against the real pinned ACT checkout (not synthetic fixtures).

Each expectation comes from a direct native ACT call or from fixtures/catalog.json,
which scripts/record_fixtures.py recorded from direct ACT calls.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Any, cast

import pytest

from engine_bridge.contracts import BridgeError, Domain, Method
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


def test_image_spec_exposes_native_shape_center_dataset_and_true_class():
    net = native_net("cifar10_conv_med")
    d = describe_model(model_path("cifar10_conv_med"))
    spec = next(L for L in net.layers if L.kind == "INPUT_SPEC")
    s = d.input_specs[0]
    assert s.shape == tuple(spec.params["lb"].shape) == (1, 3, 32, 32)
    assert s.center == tuple(spec.params["center"].reshape(-1).tolist())
    assert s.dataset == next(L for L in net.layers if L.kind == "INPUT").params["dataset_name"]
    assrt = next(L for L in net.layers if L.kind == "ASSERT")
    assert d.output_spec is not None and d.output_spec.true_class == int(assrt.params["y_true"].item())
    plain = describe_model(model_path("bab_deep_mlp")).input_specs[0]
    assert (plain.center, plain.dataset) == (None, None)


def _require_sources() -> None:
    from engine_bridge.model_spec import sources

    if not sources.classifier_sources() or not sources.vnnlib_instances():
        pytest.skip("ACT checkout has no literature/ ONNX classifiers or data/vnnlib benchmarks")


def test_classifier_source_builds_box_around_the_dataset_image(tmp_path):
    from engine_bridge.model_spec import sources

    _require_sources()
    built = sources.build_classifier_net("mnist_conv_small", 3, 0.05, tmp_path / "n.json")
    sample = sources.dataset_sample("mnist", 3)
    d = describe_model(tmp_path / "n.json")
    spec = d.input_specs[0]
    assert (spec.shape, spec.dataset) == ((1, 1, 28, 28), "mnist")
    assert spec.center == pytest.approx(sample.pixels)
    assert spec.lb == pytest.approx([max(0.0, v - 0.05) for v in sample.pixels])
    assert spec.ub == pytest.approx([min(1.0, v + 0.05) for v in sample.pixels])
    assert d.output_spec is not None and d.output_spec.true_class == sample.label == built.params["label"]


def test_classifier_builder_reproduces_the_pinned_catalog_net(tmp_path):
    from engine_bridge.model_spec import file_sha256, sources

    _require_sources()
    sources.build_classifier_net("mnist_conv_small", 0, 0.05, tmp_path / "n.json", target="prediction")
    assert file_sha256(tmp_path / "n.json") == MODELS["mnist_conv_small"]["sha256"]


def test_vnnlib_source_matches_act_spec_creation(tmp_path):
    from engine_bridge.contracts import VnnlibInstance
    from engine_bridge.model_spec import sources

    _require_sources()
    inst = VnnlibInstance("cora_2024", "onnx/mnist-point.onnx", "vnnlib/mnist-img0.vnnlib")
    built = sources.build_vnnlib_net(inst, tmp_path / "v.json")
    with act_imports():
        from act.front_end.vnnlib_loader.create_specs import create_specs_from_paths
        bench = sources.vnnlib_root() / "cora_2024"
        _, _, _, _, pairs = create_specs_from_paths(bench / inst.onnx, bench / inst.vnnlib, category="cora_2024")
    in_spec, out_spec = pairs[0]
    d = describe_model(tmp_path / "v.json")
    assert d.input_specs[0].lb == pytest.approx(in_spec.lb.reshape(-1).tolist())
    assert d.input_specs[0].ub == pytest.approx(in_spec.ub.reshape(-1).tolist())
    assert d.output_spec is not None and d.output_spec.kind == out_spec.kind
    assert d.output_spec.true_class == int(out_spec.y_true.reshape(-1)[0].item())
    assert built.params["dataset"] == d.input_specs[0].dataset == "mnist"


def test_model_sources_reject_bad_instances(tmp_path):
    from engine_bridge.contracts import VnnlibInstance
    from engine_bridge.model_spec import sources

    _require_sources()
    cases = [
        (lambda: sources.build_classifier_net("nope", 0, 0.1, tmp_path / "a.json"), "source_not_found"),
        (lambda: sources.build_classifier_net("mnist_conv_small", 10_000, 0.1, tmp_path / "b.json"), "invalid_instance"),
        (lambda: sources.build_classifier_net("mnist_conv_small", 0, 1.5, tmp_path / "c.json"), "invalid_instance"),
        (lambda: sources.build_vnnlib_net(VnnlibInstance("cora_2024", "onnx/missing.onnx", "vnnlib/mnist-img0.vnnlib"),
                                          tmp_path / "d.json"), "source_not_found"),
        (lambda: sources.dataset_sample("imagenet", 0), "dataset_not_found"),
    ]
    for call, code in cases:
        with pytest.raises(BridgeError) as err:
            call()
        assert err.value.code == code


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
    assert all(lo <= x <= hi for f in out.frames for x, lo, hi in zip(f.input, box.lb, box.ub, strict=True))


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
