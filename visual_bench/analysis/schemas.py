"""Per-layer bound payloads of a completed run (/api/runs/{id}/layers)."""
from __future__ import annotations

from typing import Literal

__all__ = ['LayerStateOut', 'LayerStatesOut']


from visual_bench.wire import WireNumber, Availability, Wire


class LayerStateOut(Wire):
    layer_id: int
    kind: str
    stage: Literal["after"]
    shape: list[int]
    lb: list[WireNumber]
    ub: list[WireNumber]
    before_layer_ids: list[int]

class LayerStatesOut(Wire):
    run_id: str
    availability: Availability
    method: Literal["interval"] | None
    layers: list[LayerStateOut]
    provenance: dict[str, str]
