"""Model sources (MSB-04): build ACT nets from a VNN-COMP instance or from an image classifier plus a chosen input and eps.

Both builders go through ACT's own front end (vnnlib_loader / onnx_converter, VerifiableModel,
TorchToACT) and write the result with ACT's save_net_to_file, so the workbench describes, verifies
and fuzzes a built net exactly like a catalog net.
"""
from __future__ import annotations

import ast
import contextlib
import csv
import io
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from engine_bridge.contracts import BridgeError, BuiltNet, ClassifierSource, DatasetSample, VnnlibInstance
from engine_bridge.engine_session import act_imports, act_root

_BAVERLY = "literature/code/BaVerLy/models/onnx_format"
# ONNX classifiers in the ACT checkout, fed raw [0, 1] pixels as ACT's mnist_cifar_smoke harness does.
# Clean accuracy on test images 0-199: MNIST models 93-100%; the CIFAR-10 model 36% (no tried
# normalization exceeds 44%), so many CIFAR instances are misclassified before any perturbation.
_CLASSIFIERS = (
    ClassifierSource("mnist_relu_5_100", "mnist", f"{_BAVERLY}/mnist_relu_5_100_pgd1_regl1.onnx", "MNIST 5x100 ReLU MLP (BaVerLy)"),
    ClassifierSource("mnist_relu_6_100", "mnist", f"{_BAVERLY}/mnist_relu_6_100_pgd1_regl1.onnx", "MNIST 6x100 ReLU MLP (BaVerLy)"),
    ClassifierSource("mnist_256x4", "mnist", "literature/code/EMSOFT2025/model/mnist-net_256x4.onnx", "MNIST 4x256 ReLU MLP (EMSOFT 2025)"),
    ClassifierSource("mnist_conv_small", "mnist", f"{_BAVERLY}/mnist_conv_small_relu_pgd2_l1reg.onnx", "MNIST conv-small ReLU CNN (BaVerLy)"),
    ClassifierSource("mnist_conv_med", "mnist", f"{_BAVERLY}/mnist_conv_med_relu_pgd2_l1reg.onnx", "MNIST conv-med ReLU CNN (BaVerLy)"),
    ClassifierSource("mnist_conv_big", "mnist", f"{_BAVERLY}/mnist_conv_big_relu_pgd2_l1reg.onnx", "MNIST conv-big ReLU CNN (BaVerLy)"),
    ClassifierSource("cifar10_conv_med", "cifar10", f"{_BAVERLY}/cifar10_conv_med_relu_pgd_regl1.onnx",
                     "CIFAR-10 conv-med ReLU CNN (BaVerLy; low clean accuracy on raw pixels)"),
)
_DATASET_DIRS = {"mnist": "MNIST", "cifar10": "CIFAR10"}
_lock = threading.Lock()  # ACT/torch global state (default device/dtype) is process-wide


def vnnlib_root() -> Path:
    return act_root() / "data" / "vnnlib"


def vnnlib_instances() -> tuple[VnnlibInstance, ...]:
    """Instances listed in ACT_ROOT/data/vnnlib/<benchmark>/instances.csv whose files exist."""
    out: list[VnnlibInstance] = []
    root = vnnlib_root()
    if not root.is_dir():
        return ()
    for csv_path in sorted(root.glob("*/instances.csv")):
        bench = csv_path.parent
        with csv_path.open(newline="") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                onnx, vnn = _onnx_field(row[0]), row[1].strip().removeprefix("./")
                if onnx and all((bench / p).is_file() for p in onnx.split(",")) and (bench / vnn).is_file():
                    out.append(VnnlibInstance(bench.name, onnx, vnn))
    return tuple(out)


def _onnx_field(field: str) -> str | None:
    """The ONNX column of instances.csv as the workbench names it: one path, or for a
    multi-network property VNN-COMP's ``[(role, path), ...]`` list as its paths joined by
    commas, in network order. None when the column cannot be read."""
    field = field.strip()
    if not field.startswith("["):
        return field.removeprefix("./")
    try:
        return ",".join(str(path).strip().removeprefix("./") for _role, path in ast.literal_eval(field))
    except (ValueError, SyntaxError, TypeError):
        return None


def _onnx_names(onnx: str) -> str:
    return ", ".join(Path(p).name for p in onnx.split(","))


def classifier_sources() -> tuple[ClassifierSource, ...]:
    root = act_root()
    return tuple(s for s in _CLASSIFIERS if (root / s.onnx).is_file()
                 and (root / "data" / "torchvision" / _DATASET_DIRS[s.dataset] / "raw").is_dir())


def _classifier(source_id: str) -> ClassifierSource:
    for s in classifier_sources():
        if s.source_id == source_id:
            return s
    raise BridgeError("source_not_found", f"Unknown or unavailable classifier source {source_id!r}")


def _dataset(dataset: str) -> Any:
    from torchvision import datasets, transforms

    raw = act_root() / "data" / "torchvision" / _DATASET_DIRS[dataset] / "raw"
    cls = datasets.MNIST if dataset == "mnist" else datasets.CIFAR10
    try:
        return cls(root=str(raw), train=False, download=False, transform=transforms.ToTensor())
    except RuntimeError as exc:
        raise BridgeError("dataset_missing", f"{dataset} test set not found under {raw}: {exc}") from exc


def dataset_sample(dataset: str, index: int) -> DatasetSample:
    if dataset not in _DATASET_DIRS:
        raise BridgeError("dataset_not_found", f"Unknown dataset {dataset!r}")
    with act_imports():
        ds = _dataset(dataset)
        if not 0 <= index < len(ds):
            raise BridgeError("invalid_instance", f"{dataset} test index {index} is outside 0..{len(ds) - 1}")
        x, label = ds[index]
        return DatasetSample(dataset, index, len(ds), int(label), tuple(int(s) for s in x.shape),
                             tuple(float(v) for v in x.reshape(-1).tolist()))


def _dataset_hint(name: str) -> str | None:
    n = name.lower()
    if "cifar100" in n:
        return None
    return "mnist" if "mnist" in n else "cifar10" if "cifar" in n else "svhn" if "svhn" in n else None


def _wrap_to_net(model: Any, center: Any, label: Any, input_spec: Any, output_spec: Any, dataset: str) -> Any:
    from act.front_end.model_synthesis import infer_layout_from_tensor
    from act.front_end.spec_creator_base import LabeledInputTensor
    from act.front_end.verifiable_model import InputLayer, InputSpecLayer, OutputSpecLayer, VerifiableModel
    from act.pipeline.verification.torch2act import TorchToACT

    wrapped = VerifiableModel(
        input_layer=InputLayer(LabeledInputTensor(center, label), center.shape, center.dtype,
                               layout=infer_layout_from_tensor(center), dataset_name=dataset),
        input_spec=InputSpecLayer(spec=input_spec),
        model=model,
        output_spec=OutputSpecLayer(spec=output_spec),
    ).to(device=center.device, dtype=center.dtype)
    return TorchToACT(wrapped, sample_input=center).run()


BATCH_LIMIT = 64


def build_vnnlib_net(inst: VnnlibInstance | Sequence[VnnlibInstance], out_path: Path) -> BuiltNet:
    """ONNX + VNN-LIB through ACT's create_specs_from_paths; the first query of each property becomes its spec.

    A sequence of properties on one network (same benchmark and ONNX file) builds one net with a row per
    property, merged by ACT's own model synthesis (synthesize_models_and_seeds_from_specs), which ACTFuzzer
    fuzzes as one batch. ACT merges properties with the same input/output kind and output constraint
    (cd_group="shape": UNSAFE_LINEAR properties that differ only in their thresholds d, as ACT's fuzzing
    pipeline groups them); others, or per-property thresholds on an ACT engine whose encode_linear
    cannot take them, raise incompatible_batch.
    """
    insts = [inst] if isinstance(inst, VnnlibInstance) else list(inst)
    if not 1 <= len(insts) <= BATCH_LIMIT or len({i.vnnlib for i in insts}) != len(insts):
        raise BridgeError("invalid_instance", f"a batch holds 1..{BATCH_LIMIT} distinct VNN-LIB properties, got {len(insts)}")
    first = insts[0]
    if any((i.benchmark, i.onnx) != (first.benchmark, first.onnx) for i in insts):
        raise BridgeError("invalid_instance", "every property of a batch must use the same network (benchmark and ONNX file)")
    bench = vnnlib_root() / first.benchmark
    for i in insts:
        if not (all((bench / p).is_file() for p in i.onnx.split(",")) and (bench / i.vnnlib).is_file()):
            raise BridgeError("source_not_found", f"VNN-LIB instance files missing: {i.benchmark}/{i.onnx}, {i.vnnlib}")
    dataset = (_dataset_hint(Path(first.onnx.split(",")[0]).stem) or _dataset_hint(Path(first.vnnlib).stem)
               or first.benchmark)
    with _lock, act_imports():
        from act.back_end.serialization.serialization import save_net_to_file
        from act.front_end.spec_creator_base import LabeledInputTensor
        from act.front_end.vnnlib_loader.create_specs import create_specs_from_paths
        from act.util.device_manager import get_default_device, get_default_dtype

        device, dtype = get_default_device(), get_default_dtype()
        parsed = []
        for i in insts:
            # One ONNX file per network of a multi-network property, in network order.
            onnx_paths = [bench / p for p in i.onnx.split(",")]
            try:
                _cat, _name, model, labeled, pairs = create_specs_from_paths(
                    onnx_paths if len(onnx_paths) > 1 else onnx_paths[0], bench / i.vnnlib, category=i.benchmark)
            except SystemExit as exc:  # ACT's single-instance entry point exits on unsupported specs
                raise BridgeError("unsupported_spec", f"{i.vnnlib}: {exc}") from exc
            except Exception as exc:
                raise BridgeError("model_load_failed", f"ACT could not load {i.onnx} / {i.vnnlib}: {exc}") from exc
            lt = labeled[0]
            input_spec, output_spec = pairs[0]
            for spec in (input_spec, output_spec):
                for attr, value in vars(spec).items():
                    if hasattr(value, "to") and hasattr(value, "dtype"):
                        integral = not value.dtype.is_floating_point
                        setattr(spec, attr, value.to(device=device) if integral else value.to(device=device, dtype=dtype))
            parsed.append((model, LabeledInputTensor(lt.tensor.to(device=device, dtype=dtype),
                                                     lt.label.to(device=device) if lt.label is not None else None),
                           input_spec, output_spec, len(pairs)))
        model = parsed[0][0].eval().to(device=device, dtype=dtype)
        if len(parsed) == 1:
            _, lt, input_spec, output_spec, _ = parsed[0]
            net = _wrap_to_net(model, lt.tensor, lt.label, input_spec, output_spec, dataset)
        else:
            net = _merge_vnnlib_batch(model, parsed, insts, dataset, device, dtype)
        save_net_to_file(net, str(out_path))
    queries = [p[4] for p in parsed]
    params: dict[str, str | int | float] = {"benchmark": first.benchmark, "onnx": first.onnx, "vnnlib": first.vnnlib,
                                            "queries": queries[0], "dataset": dataset}
    if len(insts) == 1:
        return BuiltNet(f"VNN-LIB {first.benchmark}: {_onnx_names(first.onnx)} + {Path(first.vnnlib).name}"
                        + (f" (query 1 of {queries[0]})" if queries[0] > 1 else ""), params)
    params |= {"batch": len(insts), "vnnlibs": ",".join(i.vnnlib for i in insts)}
    multi = sum(q > 1 for q in queries)
    return BuiltNet(f"VNN-LIB {first.benchmark}: {_onnx_names(first.onnx)}, batch of {len(insts)} properties"
                    + (f" (query 1 of each; {multi} have more)" if multi else ""), params, input_rows=len(insts))


def _merge_vnnlib_batch(model: Any, parsed: list[tuple[Any, ...]], insts: Sequence[VnnlibInstance], dataset: str,
                        device: Any, dtype: Any) -> Any:
    """One batched ACT net from per-property specs on one model, grouped and merged by ACT's model synthesis."""
    from act.front_end.model_synthesis import synthesize_models_and_seeds_from_specs
    from act.pipeline.verification.torch2act import TorchToACT

    # One model object for every property: ACT groups specs by model identity.
    spec_results = [(dataset, Path(i.vnnlib).stem, model, [lt], [(in_spec, out_spec)])
                    for i, (_, lt, in_spec, out_spec, _) in zip(insts, parsed, strict=True)]
    with contextlib.redirect_stdout(io.StringIO()):  # synthesis prints a progress summary
        models, seeds = synthesize_models_and_seeds_from_specs(spec_results, cd_group="shape")
    if len(models) != 1:
        owner = {id(p[1]): Path(i.vnnlib).stem for i, p in zip(insts, parsed, strict=True)}
        groups = "; ".join(", ".join(owner[id(lt)] for lt in group) for group in seeds.values())
        raise BridgeError("incompatible_batch",
                          f"ACT batches only properties with the same input kind, output kind and output constraint; "
                          f"these {len(insts)} properties form {len(models)} groups: {groups}")
    vm = next(iter(models.values())).to(device=device, dtype=dtype)
    try:
        return TorchToACT(vm, sample_input=vm.input_layer.input_tensor).run()
    except ValueError as exc:  # e.g. an ACT whose encode_linear takes only thresholds shared by every lane
        raise BridgeError("incompatible_batch", f"this ACT engine cannot encode the batch as one net: {exc}") from exc


def build_classifier_net(source_id: str, index: int | Sequence[int], eps: float, out_path: Path,
                         target: str = "label") -> BuiltNet:
    """L-inf box of radius eps around test image `index` (clipped to [0, 1]) with a TOP1_ROBUST assertion.

    A sequence of indices builds one net with a row per image (ACT's batched INPUT / spec rows), which
    ACTFuzzer fuzzes as one batch; ACT's verify_once does not accept such a net.
    target="label" asserts the dataset label (ACT TorchVision convention); "prediction" asserts the
    model's own prediction on the clean image (used for the pinned catalog nets).
    """
    indices = [index] if isinstance(index, int) else list(index)
    if not 1 <= len(indices) <= BATCH_LIMIT or len(set(indices)) != len(indices):
        raise BridgeError("invalid_instance", f"a batch holds 1..{BATCH_LIMIT} distinct test images, got {indices}")
    if not 0.0 <= eps <= 1.0:
        raise BridgeError("invalid_instance", f"eps must lie in [0, 1], got {eps}")
    src = _classifier(source_id)
    with _lock, act_imports():
        import torch

        from act.back_end.serialization.serialization import save_net_to_file
        from act.front_end.specs import InKind, InputSpec, OutKind, OutputSpec
        from act.front_end.vnnlib_loader.onnx_converter import convert_onnx_to_pytorch, get_onnx_input_shape
        from act.util.device_manager import get_default_device, get_default_dtype

        device, dtype = get_default_device(), get_default_dtype()
        onnx = act_root() / src.onnx
        model = convert_onnx_to_pytorch(onnx, simplify=True).eval()
        ds = _dataset(src.dataset)
        bad = [i for i in indices if not 0 <= i < len(ds)]
        if bad:
            raise BridgeError("invalid_instance", f"{src.dataset} test index {bad[0]} is outside 0..{len(ds) - 1}")
        samples = [ds[i] for i in indices]
        labels = [int(label) for _, label in samples]
        n = len(indices)
        model = model.to(device=device, dtype=dtype)
        center = torch.stack([image for image, _ in samples]).to(device=device, dtype=dtype)
        shape = get_onnx_input_shape(onnx)
        if shape is not None:
            dims = tuple(1 if d is None or int(d) <= 0 else int(d) for d in shape)[1:]
            if n * int(torch.tensor(dims).prod()) == center.numel():
                center = center.reshape(n, *dims)
        with torch.no_grad():
            preds = [int(p) for p in torch.argmax(model(center).reshape(n, -1), dim=1).tolist()]
        ys = labels if target == "label" else preds
        y_true = torch.tensor(ys, device=device)
        input_spec = InputSpec(kind=InKind.BOX, lb=torch.clamp(center - eps, 0.0, 1.0),
                               ub=torch.clamp(center + eps, 0.0, 1.0), center=center,
                               eps=torch.full((n,), eps, device=device, dtype=dtype))
        output_spec = OutputSpec(kind=OutKind.TOP1_ROBUST, y_true=y_true)
        net = _wrap_to_net(model, center, y_true, input_spec, output_spec, src.dataset)
        save_net_to_file(net, str(out_path))
    params: dict[str, str | int | float] = {"source_id": src.source_id, "dataset": src.dataset, "index": indices[0],
                                            "eps": eps}
    if n == 1:
        params |= {"label": labels[0], "predicted": preds[0], "target": ys[0]}
        return BuiltNet(f"{src.description}, {src.dataset} test image {indices[0]} (label {labels[0]}), L-inf eps={eps:g}",
                        params)
    def joined(xs: Sequence[int]) -> str:
        return ",".join(str(x) for x in xs)

    params |= {"batch": n, "indices": joined(indices), "labels": joined(labels), "predictions": joined(preds),
               "targets": joined(ys), "misclassified": sum(p != y for p, y in zip(preds, labels, strict=True))}
    return BuiltNet(f"{src.description}, batch of {n} {src.dataset} test images {index_ranges(indices)}, L-inf eps={eps:g}",
                    params, input_rows=n)


def index_ranges(indices: Sequence[int]) -> str:
    """Batch order kept, consecutive runs of 3+ folded: [4024, 1, 9873, 3, 4, 5] -> "4024, 1, 9873, 3-5"."""
    parts: list[str] = []
    i = 0
    while i < len(indices):
        j = i
        while j + 1 < len(indices) and indices[j + 1] == indices[j] + 1:
            j += 1
        parts.append(f"{indices[i]}-{indices[j]}" if j - i >= 2 else ", ".join(str(x) for x in indices[i:j + 1]))
        i = j + 1
    return ", ".join(parts)

