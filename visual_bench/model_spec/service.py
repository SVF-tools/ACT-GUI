"""Model catalog, model sources, and model descriptions (MS-01..04): the workbench side of engine_bridge.model_spec.

- Catalog: real ACT models pinned by fixtures/catalog.json (commit + sha256, recorded native verdicts).
- Built models: nets the bridge builds from VNN-LIB / classifier sources, stored content-addressed
  as <models_root>/<kind>-<sha12>.json + .meta.json; the same content returns the same model.
"""
from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine_bridge.contracts import BridgeError, VnnlibInstance
from engine_bridge.engine_session import act_root
from engine_bridge.execution import UNIVERSAL_METHODS, verify_methods
from engine_bridge.model_spec import describe_model, file_sha256
from engine_bridge.model_spec import sources as model_sources
from visual_bench.engine.service import EngineService
from visual_bench.errors import AppError, bridge_error
from visual_bench.model_spec import schemas as S
from visual_bench.wire import Method, wire_numbers


class ModelService:
    def __init__(self, catalog: dict[str, Any], models_root: Path, engine: EngineService) -> None:
        self.catalog = catalog
        self.models_root = models_root
        self.engine = engine
        self._lock = threading.Lock()
        self._derived: dict[str, dict[str, Any]] = {}
        for meta in sorted(models_root.glob("*.meta.json")) if models_root.is_dir() else ():
            entry = json.loads(meta.read_text())
            self._derived[entry["id"]] = entry

    # -- catalog -------------------------------------------------------------
    def entry(self, model_id: str) -> dict[str, Any]:
        for m in self.catalog["models"]:
            if m["id"] == model_id:
                return m
        if model_id in self._derived:
            return self._derived[model_id]
        raise AppError(404, "model_not_found", f"Unknown model_id {model_id!r}")

    def path(self, model_id: str) -> Path:
        """The model's ACT net file, checked against its pinned sha256."""
        entry = self.entry(model_id)
        path = self.models_root / f"{model_id}.json" if model_id in self._derived else act_root() / entry["act_path"]
        if not path.is_file():
            raise AppError(503, "model_missing", f"{entry['act_path']} is missing from the ACT checkout")
        if file_sha256(path) != entry["sha256"]:
            raise AppError(409, "snapshot_mismatch", f"{entry['act_path']} does not match the pinned sha256")
        return path

    @staticmethod
    def methods(entry: dict[str, Any]) -> list[Method]:
        return [*entry["methods"], *UNIVERSAL_METHODS]

    def native(self, model_id: str, method: Method) -> dict[str, Any] | None:
        """Recorded native ACT result of a catalog model (interval domain only); None for built models."""
        return self.entry(model_id)["native"].get(method)

    def models(self) -> list[S.ModelSummary]:
        return [S.ModelSummary(model_id=m["id"], description=m["description"], act_path=m["act_path"],
                               sha256=m["sha256"], methods=self.methods(m), native=m["native"],
                               source=m.get("source", "catalog"), params=m.get("params", {}))
                for m in [*self.catalog["models"], *self._derived.values()]]

    # -- model sources (MSB-04) ----------------------------------------------
    def sources(self) -> S.SourcesOut:
        self.engine.require_engine()
        groups: dict[str, list[S.VnnlibInstanceOut]] = {}
        for inst in model_sources.vnnlib_instances():
            groups.setdefault(inst.benchmark, []).append(S.VnnlibInstanceOut(onnx=inst.onnx, vnnlib=inst.vnnlib))
        return S.SourcesOut(
            vnnlib=[S.VnnlibBenchmarkOut(benchmark=b, instances=i) for b, i in groups.items()],
            classifiers=[S.ClassifierSourceOut(source_id=c.source_id, dataset=c.dataset, onnx=c.onnx,
                                               description=c.description)
                         for c in model_sources.classifier_sources()],
            vnnlib_root=str(model_sources.vnnlib_root()))

    def sample(self, dataset: str, index: int) -> S.SampleOut:
        self.engine.require_engine()
        try:
            s = model_sources.dataset_sample(dataset, index)
        except BridgeError as err:
            raise bridge_error(err, 404 if err.code == "dataset_not_found" else 422) from err
        return S.SampleOut(dataset=s.dataset, index=s.index, size=s.size, label=s.label, shape=list(s.shape),
                           pixels=list(s.pixels))

    def load(self, req: S.LoadVnnlibRequest | S.LoadTorchRequest) -> tuple[S.ModelSummary, bool]:
        """Build a net from a source; the same content returns the existing model (idempotent by sha256)."""
        self.engine.require_engine()
        self.models_root.mkdir(parents=True, exist_ok=True)
        tmp = self.models_root / f".build-{uuid.uuid4().hex}.json"
        try:
            if isinstance(req, S.LoadVnnlibRequest):
                built = model_sources.build_vnnlib_net(VnnlibInstance(req.benchmark, req.onnx, req.vnnlib), tmp)
            else:
                built = model_sources.build_classifier_net(req.source_id, req.indices or req.index, req.eps, tmp)
        except BridgeError as err:
            tmp.unlink(missing_ok=True)
            raise bridge_error(err, 404 if err.code == "source_not_found" else 422) from err
        sha = file_sha256(tmp)
        model_id = f"{req.kind}-{sha[:12]}"
        with self._lock:
            created = model_id not in self._derived
            if created:
                tmp.replace(self.models_root / f"{model_id}.json")
                entry = {"id": model_id, "description": built.description, "act_path": f"workbench-models/{model_id}.json",
                         "sha256": sha, "methods": list(verify_methods(built.input_rows)), "native": {},
                         "source": req.kind, "params": built.params}
                (self.models_root / f"{model_id}.meta.json").write_text(json.dumps(entry, indent=2))
                self._derived[model_id] = entry
            else:
                tmp.unlink(missing_ok=True)
        return next(m for m in self.models() if m.model_id == model_id), created

    # -- descriptions ----------------------------------------------------------
    def describe(self, model_id: str) -> S.ModelDescriptionOut:
        self.engine.require_engine()
        return self._describe_cached(model_id)

    @lru_cache(maxsize=32)
    def _describe_cached(self, model_id: str) -> S.ModelDescriptionOut:
        path = self.path(model_id)
        try:
            d = describe_model(path)
        except BridgeError as err:
            raise bridge_error(err) from err
        raw = asdict(d)
        for spec in raw["input_specs"]:
            spec["lb"], spec["ub"] = wire_numbers(spec["lb"]), wire_numbers(spec["ub"])
            if spec["center"] is not None:
                spec["center"] = wire_numbers(spec["center"])
        if raw["output_spec"] and raw["output_spec"]["thresholds"] is not None:
            raw["output_spec"]["thresholds"] = wire_numbers(raw["output_spec"]["thresholds"])
        raw.pop("source_path")
        return S.ModelDescriptionOut(model_id=model_id, act_commit=self.engine.info.commit, **raw)
