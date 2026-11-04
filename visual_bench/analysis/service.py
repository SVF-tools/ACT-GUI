"""Per-layer interval bounds of a completed run (AN-01): reads the layers.json artifact the run worker recorded."""
from __future__ import annotations

from visual_bench.analysis import schemas as S
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
