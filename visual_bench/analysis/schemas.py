"""Per-layer bound payloads of a completed run (/api/runs/{id}/layers)."""
from __future__ import annotations

from typing import Literal

__all__ = ['LayerStateOut', 'LayerStatesOut', 'PropagationKeyOut', 'PropagationTensorOut',
           'PropagationRecordOut', 'PropagationLayerSummaryOut', 'PropagationIndexOut',
           'PropagationLayerRecordOut', 'PropagationLayerOut']


from visual_bench.wire import WireNumber, Availability, Domain, Scalar, Wire


class LayerStateOut(Wire):
    layer_id: int
    kind: str
    stage: Literal["after", "pre"]
    shape: list[int]
    lb: list[WireNumber]
    ub: list[WireNumber]
    before_layer_ids: list[int]

class LayerStatesOut(Wire):
    run_id: str
    availability: Availability
    method: Domain | None
    layers: list[LayerStateOut]
    provenance: dict[str, str]


class PropagationKeyOut(Wire):
    scope: str
    parent: str | None
    domain: Domain
    pass_: str
    layer_id: int
    stage: str
    version: int
    origin: str


class PropagationTensorOut(Wire):
    sha256: str
    dtype: Literal["float32"]
    shape: list[int]  # ACT layout, including batch lane and (for alpha) spec rows


class PropagationRecordOut(Wire):
    record_id: int  # monotonic within this run, shared by phases and tensor records
    kind: Literal["PhaseEvent", "LayerBounds", "Relaxation", "DualBackward", "SpecBound"]
    key: PropagationKeyOut | None  # phases have no layer key
    t_ms: float  # monotonic time since worker verification started
    layer_kind: str | None
    shape: list[int]  # first tensor's full shape; each tensor also declares its own shape
    output_shape: list[int]  # layer output axes, excluding batch, for neuron -> C/H/W mapping
    tensors: dict[str, PropagationTensorOut]
    counts: dict[str, int]  # Relaxation: n_active, n_inactive, n_unstable (all batch lanes)
    metadata: dict[str, Scalar]  # form, alpha_optimized, iterations, stop_reason, changed; phases: phase/status


class PropagationLayerSummaryOut(Wire):
    key: PropagationKeyOut
    layer_kind: str | None
    output_shape: list[int]
    latest_record_id: int
    record_count: int
    counts: dict[str, int]  # latest relaxation at this scope/domain/pass/layer/stage


class PropagationIndexOut(Wire):
    run_id: str
    domain: Domain | None
    availability: Literal["available", "pending", "unavailable", "not_recorded"]
    complete: bool  # false while running or for a failed/interrupted partial recording
    phases: list[PropagationRecordOut]
    records: list[PropagationRecordOut]
    layers: list[PropagationLayerSummaryOut]
    ignored_records: int
    value_limit: int  # per layer-detail response; exceeding it returns 413, never silently truncates


class PropagationLayerRecordOut(PropagationRecordOut):
    values: dict[str, list[WireNumber]]  # flattened tensors; reshape using tensors[name].shape


class PropagationLayerOut(Wire):
    run_id: str
    layer_id: int
    domain: Domain | None
    availability: Literal["available", "pending", "unavailable", "not_recorded"]
    output_shape: list[int]
    records: list[PropagationLayerRecordOut]
    value_limit: int
    neuron: int | None = None  # set when values were sliced to one neuron (that axis has size 1 in tensors[name].shape)
