"""Input provenance (MSB-07): what a VNN-LIB property was built from, read through ACT's provenance API.

ACT owns the sidecar and how its entries were matched (act.pipeline.gui.provenance_gui, capability
source.provenance); this adapter copies ACT's records into neutral contracts. A point of the model input space is
never turned into text here: it is only ranked against the benchmark's known examples.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from engine_bridge.contracts import (BridgeError, InputNeighbour, InputProvenance, ProvenanceTask, TextVariant,
                                     VnnlibInstance)
from engine_bridge.engine_session import act_imports
from engine_bridge.model_spec import sources

SIDECAR_MANIFEST = Path("provenance") / "manifest.json"


def has_provenance(benchmark: str) -> bool:
    """Whether the benchmark directory carries a provenance sidecar, checked before any ACT call."""
    return (sources.vnnlib_root() / benchmark / SIDECAR_MANIFEST).is_file()


def _instance_path(inst: VnnlibInstance) -> Path:
    return sources.vnnlib_root() / inst.benchmark / inst.vnnlib


def input_provenance(inst: VnnlibInstance) -> InputProvenance | None:
    with act_imports():
        from act.pipeline.gui.provenance_gui import input_provenance as act_input_provenance

        p = act_input_provenance(_instance_path(inst))
    if p is None:
        return None
    t = p.task
    return InputProvenance(
        benchmark=p.benchmark, key=p.key, modality=p.modality, representation=p.representation,
        task=ProvenanceTask(name=t.name, title=t.title, description=t.description, class_names=tuple(t.class_names),
                            dataset=t.dataset, dataset_url=t.dataset_url),
        family=p.family, family_title=p.family_title, family_index=p.family_index, example_id=p.example_id,
        text=p.text, label=p.label, split=p.split,
        anchor=tuple(float(x) for x in p.anchor.tolist()) if p.anchor is not None else None,
        variants=tuple(TextVariant(text=v.text, kind=v.kind, kept=v.kept, cosine=v.cosine) for v in p.variants),
        variants_status=p.variants_status, match_status=p.match_status, match_detail=p.match_detail,
        sources=tuple(dict(s) for s in p.sources))


def nearest_inputs(inst: VnnlibInstance, point: Sequence[float], k: int = 3) -> tuple[InputNeighbour, ...]:
    with act_imports():
        from act.pipeline.gui.provenance_gui import nearest_inputs as act_nearest_inputs

        try:
            found = act_nearest_inputs(_instance_path(inst), [float(x) for x in point], k=k)
        except ValueError as exc:
            raise BridgeError("invalid_point", str(exc)) from exc
    return tuple(InputNeighbour(example_id=n.example_id, text=n.text, label=n.label, split=n.split,
                                distance=float(n.distance)) for n in found)
