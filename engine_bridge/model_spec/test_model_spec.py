"""Model description and model source parity tests against native ACT.

Expectations come from direct native ACT calls or from fixtures/catalog.json (recorded by
scripts/record_fixtures.py from direct ACT calls); no synthetic fixtures.
"""
from __future__ import annotations

import dataclasses

import pytest

from engine_bridge.contracts import BridgeError
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec import describe_model
from engine_bridge.testing import MODELS, model_path, native_net, require_sources


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

def test_classifier_source_builds_box_around_the_dataset_image(tmp_path):
    from engine_bridge.model_spec import sources

    require_sources()
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

    require_sources()
    sources.build_classifier_net("mnist_conv_small", 0, 0.05, tmp_path / "n.json", target="prediction")
    assert file_sha256(tmp_path / "n.json") == MODELS["mnist_conv_small"]["sha256"]

def test_vnnlib_source_matches_act_spec_creation(tmp_path):
    from engine_bridge.contracts import VnnlibInstance
    from engine_bridge.model_spec import sources

    require_sources()
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

def test_vnnlib_batch_merges_properties_of_one_network_through_act_synthesis(tmp_path):
    from engine_bridge.contracts import VnnlibInstance
    from engine_bridge.model_spec import sources

    require_sources()
    props = [f"vnnlib/mnist-img{k}.vnnlib" for k in range(3)]
    insts = [VnnlibInstance("cora_2024", "onnx/mnist-point.onnx", v) for v in props]
    built = sources.build_vnnlib_net(insts, tmp_path / "b.json")
    single_lbs = []
    for k, i in enumerate(insts):
        sources.build_vnnlib_net(i, tmp_path / f"s{k}.json")
        single_lbs += describe_model(tmp_path / f"s{k}.json").input_specs[0].lb
    d = describe_model(tmp_path / "b.json")
    assert (built.input_rows, built.params["vnnlibs"], d.input_specs[0].shape) == (3, ",".join(props), (3, 784))
    assert d.input_specs[0].lb == pytest.approx(single_lbs)

    mixed = [insts[0], VnnlibInstance("cora_2024", "onnx/mnist-relu.onnx", props[1])]
    with pytest.raises(BridgeError) as err:
        sources.build_vnnlib_net(mixed, tmp_path / "m.json")
    assert err.value.code == "invalid_instance"
    if not (sources.vnnlib_root() / "acasxu_2023").is_dir():
        pytest.skip("ACT checkout has no acasxu_2023 benchmark")
    # Same network, UNSAFE_LINEAR properties with 1 and 4 rows: no ACT synthesis merges them.
    props = [VnnlibInstance("acasxu_2023", "onnx/ACASXU_run2a_1_1_batch_2000.onnx", f"vnnlib/prop_{k}.vnnlib")
             for k in (1, 2)]
    with pytest.raises(BridgeError) as err:
        sources.build_vnnlib_net(props, tmp_path / "u.json")
    assert err.value.code == "incompatible_batch"
    assert not (tmp_path / "u.json").exists()

def test_multi_network_property_builds_one_net_over_the_combined_input(tmp_path):
    from engine_bridge.engine_session.parity import capability_available
    from engine_bridge.model_spec import sources

    require_sources()
    if not capability_available("source.vnnlib.multi_network"):
        pytest.skip("the active ACT cannot combine the networks of a multi-network property")
    inst = next((i for i in sources.vnnlib_instances()
                 if i.benchmark == "monotonic_acasxu_2026" and i.vnnlib == "vnnlib/instance_0.vnnlib"), None)
    if inst is None:
        pytest.skip("ACT checkout has no monotonic_acasxu_2026 benchmark")
    # instances.csv names one ACAS Xu network for f and g; the listing keeps both, in network order.
    assert inst.onnx.count(",") == 1 and len(set(inst.onnx.split(","))) == 1
    sources.build_vnnlib_net(inst, tmp_path / "m.json")
    d = describe_model(tmp_path / "m.json")
    # X_f and X_g share the four inputs the property ties with ==; X_g[0] <= X_f[0] stays a relation.
    assert (d.input_dim, d.output_dim) == (6, 10)
    assert [s.kind for s in d.input_specs] == ["BOX"]
    assert [l.kind for l in d.layers].count("INPUT_SPEC") == 2

def test_model_sources_reject_bad_instances(tmp_path):
    from engine_bridge.contracts import VnnlibInstance
    from engine_bridge.model_spec import sources

    require_sources()
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
