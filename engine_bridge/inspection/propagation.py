"""Copy ACT observations while verify_once runs; no ACT tensors escape the bridge."""
from __future__ import annotations

import struct
import time
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine_bridge.contracts import BridgeError, Domain, LayerState, LayerStates, ModelDescription, RunOutcome
from engine_bridge.engine_session import act_imports
from engine_bridge.execution.verify import run_verification
from engine_bridge.inspection.layers import MAX_VALUES_PER_LAYER
from engine_bridge.model_spec.describe import describe_model


@dataclass(frozen=True)
class PropagationKey:
    scope: str
    parent: str | None
    domain: str
    pass_: str
    layer_id: int
    stage: str
    version: int
    origin: str


@dataclass(frozen=True)
class TensorData:
    """Owned CPU float32 little-endian bytes, in ACT's original tensor layout."""
    shape: tuple[int, ...]
    data: bytes
    dtype: str = "float32"

    def values(self) -> tuple[float, ...]:
        return struct.unpack(f"<{len(self.data) // 4}f", self.data)


@dataclass(frozen=True)
class PropagationRecord:
    kind: str
    t_ms: float
    key: PropagationKey | None = None
    layer_kind: str | None = None
    output_shape: tuple[int, ...] = ()
    tensors: dict[str, TensorData] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)


class PropagationSink:
    """Copy known records synchronously, retaining only final bounds in memory.

    Unsupported/malformed observations are counted, never raised into ACT. Callback
    failures are retained separately and reported after verification, since ACT
    deliberately isolates observer exceptions from its scientific computation.
    """
    wants_relaxation = True

    def __init__(self, callback: Callable[[PropagationRecord], None], model: ModelDescription | None = None,
                 start_ns: int | None = None) -> None:
        self.callback = callback
        self.model = model
        self.start_ns = time.perf_counter_ns() if start_ns is None else start_ns
        self.ignored_records = 0
        self.callback_error: Exception | None = None
        self.final_bounds: dict[tuple[str, str, str, int, str], PropagationRecord] = {}
        self._layers = {l.layer_id: l for l in model.layers} if model else {}
        self._output_shapes = {}
        for layer in self._layers.values():
            shape = layer.output_shape
            if shape:
                self._output_shapes[layer.layer_id] = (
                    shape[1:] if len(shape) > 1 and math.prod(shape[1:]) == layer.out_vars else shape)
            else:
                self._output_shapes[layer.layer_id] = (layer.out_vars,)
        if model:
            for spec in model.input_specs:
                if spec.shape:
                    self._output_shapes[spec.layer_id] = spec.shape[1:]
                    for predecessor in self._layers[spec.layer_id].preds:
                        if self._layers[predecessor].kind == "INPUT":
                            self._output_shapes[predecessor] = spec.shape[1:]

    @staticmethod
    def _tensor(value: Any) -> TensorData:
        import torch

        cpu = value.detach().to(device="cpu", dtype=torch.float32).contiguous()
        return TensorData(tuple(cpu.shape), cpu.numpy().astype("<f4", copy=False).tobytes())

    def __call__(self, record: Any) -> None:
        try:
            copied = self._copy(record)
        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            self.ignored_records += 1
            return
        if copied is None:
            self.ignored_records += 1
            return
        key = copied.key
        if copied.kind == "LayerBounds" and key is not None:
            identity = (key.scope, key.domain, key.pass_, key.layer_id, key.stage)
            previous = self.final_bounds.get(identity)
            if previous is None or previous.key.version <= key.version:
                self.final_bounds[identity] = copied
        if self.callback_error is None:
            try:
                self.callback(copied)
            except Exception as exc:
                self.callback_error = exc

    def _copy(self, record: Any) -> PropagationRecord | None:
        kind = type(record).__name__
        now = getattr(record, "t_ns", None) or time.perf_counter_ns()
        t_ms = max(0.0, (now - self.start_ns) / 1_000_000)
        if kind == "PhaseEvent":
            meta = {str(k): v for k, v in record.meta.items()
                    if v is None or isinstance(v, (str, int, float, bool))}
            return PropagationRecord(kind, t_ms, metadata={**meta, "phase": record.phase, "status": record.status})
        tensor_fields = {
            "LayerBounds": ("lb", "ub"),
            "Relaxation": ("status", "lower_slope", "lower_intercept", "upper_slope", "upper_intercept"),
            "DualBackward": ("alpha", "nu"),
            "SpecBound": ("margins", "slack"),
        }
        if kind not in tensor_fields:
            return None
        key = PropagationKey(**{name: getattr(record.key, name) for name in PropagationKey.__dataclass_fields__})
        if (not all(isinstance(getattr(key, name), str) for name in ("scope", "domain", "pass_", "stage", "origin"))
                or not isinstance(key.layer_id, int) or not isinstance(key.version, int)
                or (key.parent is not None and not isinstance(key.parent, str))):
            raise ValueError("Unsupported record key")
        tensors = {name: self._tensor(getattr(record, name)) for name in tensor_fields[kind]
                   if getattr(record, name, None) is not None}
        required = {"LayerBounds": ("lb", "ub"), "Relaxation": ("status",), "SpecBound": ("margins", "slack")}
        if any(name not in tensors for name in required.get(kind, ())):
            raise ValueError("Missing required observation tensor")
        meta: dict[str, str | int | float | bool | None] = {}
        counts = {}
        if kind == "Relaxation":
            import torch

            meta["form"] = record.form
            for name, value in record.extra.items():
                if isinstance(value, torch.Tensor):
                    tensors[f"extra.{name}"] = self._tensor(value)
                elif value is None or isinstance(value, (str, int, float, bool)):
                    meta[f"extra.{name}"] = value
            statuses = tensors["status"].values()
            counts = {"n_active": statuses.count(1), "n_inactive": statuses.count(0), "n_unstable": statuses.count(-1)}
        elif kind == "DualBackward":
            meta["alpha_optimized"] = bool(record.alpha_optimized)
        elif kind == "SpecBound":
            meta.update(iterations=int(record.iterations), stop_reason=str(record.stop_reason))
        elif kind == "LayerBounds":
            meta["changed"] = bool(record.changed)
        layer = self._layers.get(key.layer_id)
        tensor = next(iter(tensors.values()), None)
        # Without a model description, the first record of a layer (its forward bounds) fixes the neuron shape,
        # so later records whose tensors carry spec rows (DualBackward alpha) do not redefine it.
        shape = self._output_shapes.setdefault(key.layer_id, tensor.shape[1:] if tensor else ())
        return PropagationRecord(kind, t_ms, key, str(record.kind) if kind == "LayerBounds" else
                                 (layer.kind if layer else None), shape, tensors, counts, meta)

    def layer_states(self, domain: Domain) -> LayerStates:
        """INSP-01 projection of the run's own final forward records; no recomputation."""
        states = []
        for identity, rec in sorted(self.final_bounds.items()):
            scope, recorded_domain, pass_, layer_id, stage = identity
            if scope != "root" or recorded_domain != domain or pass_ != "forward":
                continue
            # If a producer reports both, the output is the legacy layer-state projection.
            if stage == "pre" and (scope, domain, pass_, layer_id, "out") in self.final_bounds:
                continue
            lb, ub = rec.tensors["lb"], rec.tensors["ub"]
            if len(lb.data) // 4 > MAX_VALUES_PER_LAYER:
                raise BridgeError("too_large", f"Layer {layer_id} exceeds {MAX_VALUES_PER_LAYER} values; use propagation inspection")
            if lb.shape and lb.shape[0] != 1:
                raise BridgeError("unsupported_batch", "Legacy layer inspection supports one input lane; use propagation inspection")
            layer = self._layers.get(layer_id)
            states.append(LayerState(layer_id, rec.layer_kind or "", "pre" if stage == "pre" else "after",
                                     lb.values(), ub.values(), rec.output_shape, layer.preds if layer else ()))
        return LayerStates(method=domain, availability="available" if states else "not_recorded",
                           layers=tuple(states), provenance={
                               "act_call": "act.back_end.verifier.verify_once under act.back_end.observe.observe",
                               "domain": domain, "pass": "forward",
                               "bounds": "forward pre-activation bounds" if domain == "dual" else "committed layer output bounds",
                           })


def run_observed_verification(model_path: Path, time_budget_s: float, domain: Domain,
                              callback: Callable[[PropagationRecord], None],
                              start_ns: int | None = None) -> tuple[RunOutcome, PropagationSink]:
    model = describe_model(model_path)
    sink = PropagationSink(callback, model, start_ns)
    with act_imports():
        from act.back_end.observe import observe

        with observe(sink):
            outcome = run_verification(model_path, "interval", time_budget_s, domain)
    if sink.callback_error is not None:
        raise BridgeError("propagation_recording_failed", str(sink.callback_error)) from sink.callback_error
    return outcome, sink
