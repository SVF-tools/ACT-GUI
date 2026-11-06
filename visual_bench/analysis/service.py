"""Per-layer interval bounds of a completed run (AN-01): reads the layers.json artifact the run worker recorded."""
from __future__ import annotations

import math
from typing import Any, Callable

from engine_bridge.inspection.layers import MAX_VALUES_PER_LAYER
from visual_bench.analysis import schemas as S
from visual_bench.errors import AppError
from visual_bench.records import RecordStore
from visual_bench.verification.service import RunService
from visual_bench.wire import wire_numbers


class AnalysisService:
    def __init__(self, runs: RunService, records: RecordStore) -> None:
        self.runs = runs
        self.records = records

    def layer_states(self, run_id: str) -> S.LayerStatesOut:
        run = self.runs.get(run_id)
        if run.status != "completed":
            return S.LayerStatesOut(run_id=run_id, availability="pending" if run.status != "failed" else "not_recorded",
                                    method=None, layers=[], provenance={})
        raw = self.records.artifact(run_id, "layers.json")
        if raw is None:
            return S.LayerStatesOut(run_id=run_id, availability="not_recorded", method=None, layers=[], provenance={})
        layers = [S.LayerStateOut(layer_id=l["layer_id"], kind=l["kind"], stage=l["stage"], shape=l["shape"],
                                  lb=wire_numbers(l["lb"]), ub=wire_numbers(l["ub"]),
                                  before_layer_ids=l["before_layer_ids"]) for l in raw["layers"]]
        prov = dict(raw.get("provenance", {}))
        prov["recorded"] = "computed by the run worker on the run's pinned model snapshot"
        return S.LayerStatesOut(run_id=run_id, availability=raw["availability"], method=raw["method"], layers=layers,
                                provenance=prov)

    def propagation(self, run_id: str) -> S.PropagationIndexOut:
        run = self.runs.get(run_id)
        if getattr(run, "error", None) is not None and run.error.code == "record_corrupt":
            raise AppError(409, "record_corrupt", run.error.message)
        try:
            raw = self.records.propagation_index(run_id, sealed=run.status == "completed"
                                                or self.records.hashes(run_id) is not None)
        except (OSError, ValueError) as exc:
            raise AppError(409, "record_corrupt", f"Propagation index could not be verified: {exc}") from exc
        if raw is None:
            availability = "pending" if run.status in ("queued", "running") else "not_recorded"
            if run.method != "interval":
                availability = "unavailable"
            return S.PropagationIndexOut(run_id=run_id, domain=run.domain, availability=availability,
                                         complete=False, records=[], phases=[], layers=[], ignored_records=0,
                                         value_limit=MAX_VALUES_PER_LAYER)
        summaries: dict[tuple[Any, ...], dict[str, Any]] = {}
        try:
            for record in raw["records"]:
                key = record["key"]
                if key["domain"] != run.domain:
                    raise ValueError("Propagation record domain differs from its run")
                identity = tuple(key[f] for f in ("scope", "domain", "pass_", "layer_id", "stage"))
                summary = summaries.setdefault(identity, {
                    "key": key, "layer_kind": record["layer_kind"], "output_shape": record["output_shape"],
                    "latest_record_id": record["record_id"], "record_count": 0, "counts": {},
                })
                summary["record_count"] += 1
                if key["version"] >= summary["key"]["version"]:
                    summary.update(key=key, latest_record_id=record["record_id"])
                    if record["counts"]:
                        summary["counts"] = record["counts"]
                if record["layer_kind"]:
                    summary["layer_kind"] = record["layer_kind"]
            return S.PropagationIndexOut(run_id=run_id, domain=run.domain, layers=list(summaries.values()),
                                         value_limit=MAX_VALUES_PER_LAYER, **{k: v for k, v in raw.items() if k != "domain"})
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError(409, "record_corrupt", f"Invalid propagation index: {exc}") from exc

    def propagation_layer(self, run_id: str, layer_id: int, scope: str = "root",
                          pass_: str | None = None, stage: str | None = None,
                          version: int | None = None, fields: list[str] | None = None,
                          neuron: int | None = None) -> S.PropagationLayerOut:
        """fields keeps only the named tensors; neuron keeps one neuron of every tensor whose trailing axes are the
        layer's neurons (its shape keeps that axis with size 1), so large layers stay inside the value limit."""
        index = self.propagation(run_id)
        selected: dict[tuple[str, str, str], S.PropagationRecordOut] = {}
        for record in index.records:
            key = record.key
            if key is None or key.layer_id != layer_id or key.scope != scope:
                continue
            if ((pass_ is not None and key.pass_ != pass_) or (stage is not None and key.stage != stage)
                    or (version is not None and key.version != version)):
                continue
            identity = (record.kind, key.pass_, key.stage)
            previous = selected.get(identity)
            if previous is None or key.version >= previous.key.version:
                selected[identity] = record
        picks = {rid: _pick(record, fields, neuron) for rid, record in
                 ((r.record_id, r) for r in selected.values())}
        picks = {rid: p for rid, p in picks.items() if p}
        selected = {i: r for i, r in selected.items() if r.record_id in picks}
        count = sum(math.prod(shape) for p in picks.values() for shape, _ in p.values())
        if count > MAX_VALUES_PER_LAYER:
            raise AppError(413, "too_large", f"Selected propagation records contain {count} values; limit is "
                           f"{MAX_VALUES_PER_LAYER}. Select pass_, stage, and version to narrow the request.")
        sealed = self.runs.get(run_id).status == "completed" or self.records.hashes(run_id) is not None
        records = []
        try:
            for record in sorted(selected.values(), key=lambda r: r.record_id):
                values, tensors = {}, {}
                for name, (shape, take) in picks[record.record_id].items():
                    tensor = record.tensors[name]
                    flat = self.records.propagation_tensor(run_id, tensor.model_dump(), sealed)
                    values[name] = wire_numbers(take(flat))
                    tensors[name] = tensor.model_copy(update={"shape": shape})
                data = record.model_dump()
                data["tensors"] = {name: tensor.model_dump() for name, tensor in tensors.items()}
                records.append(S.PropagationLayerRecordOut(**data, values=values))
        except (OSError, ValueError, KeyError) as exc:
            raise AppError(409, "record_corrupt", f"Propagation tensor could not be verified: {exc}") from exc
        availability = index.availability if records or index.availability != "available" else "not_recorded"
        return S.PropagationLayerOut(run_id=run_id, layer_id=layer_id, domain=index.domain,
                                     availability=availability, output_shape=records[0].output_shape if records else [],
                                     records=records, value_limit=MAX_VALUES_PER_LAYER, neuron=neuron)


def _pick(record: S.PropagationRecordOut, fields: list[str] | None,
          neuron: int | None) -> dict[str, tuple[list[int], Callable[[list[float]], list[float]]]]:
    """Per tensor of record: (shape after selection, function from the flat stored values to the selected ones)."""
    width = math.prod(record.output_shape) if record.output_shape else 0
    out: dict[str, tuple[list[int], Callable[[list[float]], list[float]]]] = {}
    for name, tensor in record.tensors.items():
        if fields is not None and name not in fields:
            continue
        shape = list(tensor.shape)
        if neuron is None:
            out[name] = (shape, lambda flat: flat)
            continue
        cut = next((i for i in range(1, len(shape)) if width and math.prod(shape[i:]) == width), None)
        if cut is None:
            out[name] = (shape, lambda flat: flat)  # not indexed by this layer's neurons, e.g. spec margins
        elif neuron >= width:
            raise AppError(422, "invalid_neuron", f"Neuron {neuron} is outside this layer's {width} neurons.")
        else:
            out[name] = ([*shape[:cut], 1], lambda flat, w=width: flat[neuron::w])
    return out
