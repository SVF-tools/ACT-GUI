"""Load an ACT network snapshot and convert it to a neutral description (MSB-01..03)."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from engine_bridge.contracts import (
    BridgeError, InputSpec, LayerDescription, ModelDescription, OutputSpec, ParamInfo,
)
from engine_bridge.engine_session import act_imports

# Per input row of an INPUT_SPEC; whole tensor for ASSERT params. Sized for the largest VNN-COMP input in
# ACT's data (smart_turn_multimodal_2026: audio 80x800 plus video 3x32x112x112, packed by ACT into one row),
# so every listed benchmark instance can be described.
_MAX_SPEC_VALUES = 80 * 800 + 3 * 32 * 112 * 112
_MAX_SPEC_ROWS = 64  # rows of a batched INPUT_SPEC (model_spec.sources.BATCH_LIMIT)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_net(path: Path) -> Any:
    """Load an ACT Net (ACT object; stays inside engine_bridge)."""
    if not path.is_file():
        raise BridgeError("model_not_found", f"Model file not found: {path}")
    with act_imports():
        from act.back_end.serialization.serialization import load_net_from_file
        try:
            return load_net_from_file(str(path))
        except Exception as exc:
            raise BridgeError("model_load_failed", f"ACT could not load {path.name}: {exc}") from exc


def _flat(t: Any) -> tuple[float, ...]:
    return tuple(float(v) for v in t.detach().reshape(-1).cpu().tolist())


def _param(name: str, value: Any) -> ParamInfo:
    import torch

    if isinstance(value, torch.Tensor):
        return ParamInfo(name, tuple(int(s) for s in value.shape), None)
    text = repr(value)
    return ParamInfo(name, None, text if len(text) <= 80 else text[:77] + "...")


def _output_shape(layer: Any) -> tuple[int, ...] | None:
    # Current ACT stores layout in the schema parameters; older checkouts expose a method.
    shp = layer.params.get("output_shape")
    if shp is not None:
        return tuple(int(s) for s in shp)
    try:
        shp = layer.get_output_shape()
    except Exception:
        return None
    return tuple(int(s) for s in shp) if shp is not None else None


def _describe_assert(layer: Any) -> OutputSpec:
    import torch

    p = layer.params
    kind = str(p.get("kind"))
    C = p.get("C")
    thr = p.get("thresholds")
    matrix = None
    if isinstance(C, torch.Tensor) and C.numel() <= _MAX_SPEC_VALUES:
        matrix = tuple(tuple(float(v) for v in row) for row in C.detach().reshape(C.shape[0], -1).cpu().tolist())
    thresholds = _flat(thr) if isinstance(thr, torch.Tensor) and thr.numel() <= _MAX_SPEC_VALUES else None
    rows = int(C.shape[0]) if isinstance(C, torch.Tensor) else 0
    if matrix is not None and thresholds is not None and len(matrix) == len(thresholds):
        parts = []
        for row, t in zip(matrix, thresholds):
            terms = " + ".join(f"{c:g}*y{j}" for j, c in enumerate(row) if c != 0) or "0"
            parts.append(f"{terms} <= {t:g}")
        text = f"{kind}: property holds iff for every row, " + "; ".join(parts) + \
            "  (ACT certifies when the upper bound of C@y is below the threshold)"
    else:
        text = f"{kind} with {rows} constraint row(s)"
    y_true = p.get("y_true")
    true_class = int(y_true.reshape(-1)[0].item()) if isinstance(y_true, torch.Tensor) and y_true.numel() == 1 else None
    return OutputSpec(layer.id, kind, rows, matrix, thresholds, text, true_class)


def describe_model(path: Path) -> ModelDescription:
    import torch

    net = load_net(path)
    layers = []
    input_specs = []
    output_spec = None
    dataset = next((str(L.params["dataset_name"]) for L in net.layers
                    if L.kind == "INPUT" and L.params.get("dataset_name")), None)
    for layer in net.layers:
        layers.append(LayerDescription(
            layer_id=int(layer.id), kind=str(layer.kind),
            in_vars=len(layer.in_vars), out_vars=len(layer.out_vars),
            output_shape=_output_shape(layer),
            preds=tuple(int(x) for x in net.preds.get(layer.id, [])),
            succs=tuple(int(x) for x in net.succs.get(layer.id, [])),
            params=tuple(_param(k, v) for k, v in layer.params.items()),
        ))
        if layer.kind == "INPUT_SPEC":
            lb, ub = layer.params.get("lb"), layer.params.get("ub")
            rows = int(lb.shape[0]) if isinstance(lb, torch.Tensor) and lb.dim() >= 2 and lb.shape[0] > 0 else 1
            if (isinstance(lb, torch.Tensor) and isinstance(ub, torch.Tensor) and rows <= _MAX_SPEC_ROWS
                    and lb.numel() <= rows * _MAX_SPEC_VALUES):
                center = layer.params.get("center")
                center_vals = _flat(center) if isinstance(center, torch.Tensor) and center.numel() == lb.numel() else None
                input_specs.append(InputSpec(int(layer.id), str(layer.params.get("kind")), _flat(lb), _flat(ub),
                                             tuple(int(s) for s in lb.shape), center_vals, dataset))
            else:
                size = f" of shape {tuple(lb.shape)}" if isinstance(lb, torch.Tensor) else ""
                raise BridgeError("unsupported_spec", f"INPUT_SPEC layer {layer.id} has no box lb/ub this bridge can describe"
                                  f"{size} (at most {_MAX_SPEC_VALUES} values per input row, {_MAX_SPEC_ROWS} rows).")
        if layer.kind == "ASSERT":
            output_spec = _describe_assert(layer)
    with act_imports():
        from act.back_end.verifier import get_input_ids, get_output_ids
        in_dim, out_dim = len(get_input_ids(net)), len(get_output_ids(net))
    return ModelDescription(str(path), file_sha256(path), tuple(layers), tuple(input_specs), output_spec, in_dim, out_dim)
