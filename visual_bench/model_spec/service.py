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

from engine_bridge.contracts import DISPLAY_VALUES, BridgeError, VnnlibInstance
from engine_bridge.engine_session import act_root
from engine_bridge.execution import UNIVERSAL_METHODS, required_capability, verify_methods
from engine_bridge.model_spec import describe_model, file_sha256
from engine_bridge.model_spec import sources as model_sources
from visual_bench.engine.service import EngineService
from visual_bench.errors import AppError, bridge_error
from visual_bench.model_spec import provenance as model_provenance
from visual_bench.model_spec import schemas as S
from visual_bench.wire import Method, wire_numbers


class ModelService:
    def __init__(self, catalog: dict[str, Any], models_root: Path, engine: EngineService) -> None:
        self.catalog = catalog
        self.models_root = models_root
        self.engine = engine
        self._lock = threading.Lock()
        self._derived: dict[str, dict[str, Any]] = {}
        # (model_id, ACT commit) -> whether ACT loaded the built net when it was described on that commit.
        self._load_checks: dict[tuple[str, str | None], bool] = {}
        for meta in sorted(models_root.glob("*.meta.json")) if models_root.is_dir() else ():
            entry = json.loads(meta.read_text())
            if "batch" in entry["params"]:  # recorded under an older method rule; eligibility follows the bridge
                entry["methods"] = list(verify_methods(int(entry["params"]["batch"])))
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

    def methods(self, entry: dict[str, Any]) -> list[Method]:
        """Methods the net supports and whose ACT API passes on the active checkout."""
        declared: list[Method] = [*entry["methods"], *UNIVERSAL_METHODS]
        return [m for m in declared if self.engine.capability_available(required_capability(m))]

    def native(self, model_id: str, method: Method) -> dict[str, Any] | None:
        """Recorded native ACT result of a catalog model (interval domain only); None for built models."""
        return self.entry(model_id)["native"].get(method)

    def engine_check(self, entry: dict[str, Any], commit: str | None) -> S.EngineCheck | None:
        if entry.get("source", "catalog") == "catalog":
            return None
        built = (entry.get("built_with") or {}).get("commit")
        if built is not None and built == commit:
            return "same_commit"
        loaded = self._load_checks.get((entry["id"], commit))
        return "unchecked" if loaded is None else "loads" if loaded else "load_failed"

    def models(self) -> list[S.ModelSummary]:
        commit = self.engine.info.commit
        return [S.ModelSummary(model_id=m["id"], description=m["description"], act_path=m["act_path"],
                               sha256=m["sha256"], methods=self.methods(m), native=m["native"],
                               source=m.get("source", "catalog"), params=m.get("params", {}),
                               built_with=m.get("built_with"), engine_check=self.engine_check(m, commit))
                for m in [*self.catalog["models"], *self._derived.values()]]

    # -- model sources (MSB-04) ----------------------------------------------
    def sources(self) -> S.SourcesOut:
        self.engine.require_engine()
        groups: dict[str, list[S.VnnlibInstanceOut]] = {}
        multi_network = self.engine.capability_available("source.vnnlib.multi_network")
        instances = model_sources.vnnlib_instances()
        root = model_sources.vnnlib_root()
        described = {b for b in {i.benchmark for i in instances}
                     if (root / b / model_provenance.SIDECAR / "manifest.json").is_file()}
        for inst in instances:
            if "," in inst.onnx and not multi_network:
                continue  # the active ACT cannot combine the networks of a multi-network property
            p = model_provenance.input_provenance(root / inst.benchmark / inst.vnnlib) if inst.benchmark in described else None
            groups.setdefault(inst.benchmark, []).append(
                S.VnnlibInstanceOut(onnx=inst.onnx, vnnlib=inst.vnnlib, text=p.text if p is not None else None))
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
        self.engine.require_capability("source.vnnlib" if isinstance(req, S.LoadVnnlibRequest) else "source.onnx_classifier")
        if isinstance(req, S.LoadVnnlibRequest) and "," in req.onnx:
            self.engine.require_capability("source.vnnlib.multi_network")
        self.models_root.mkdir(parents=True, exist_ok=True)
        tmp = self.models_root / f".build-{uuid.uuid4().hex}.json"
        try:
            if isinstance(req, S.LoadVnnlibRequest):
                built = model_sources.build_vnnlib_net(
                    [VnnlibInstance(req.benchmark, req.onnx, v) for v in req.vnnlibs or [req.vnnlib]], tmp)
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
                src = self.engine.source
                entry = {"id": model_id, "description": built.description, "act_path": f"workbench-models/{model_id}.json",
                         "sha256": sha, "methods": list(verify_methods(built.input_rows)), "native": {},
                         "source": req.kind, "params": built.params,
                         "built_with": {"commit": self.engine.info.commit, "kind": src.kind, "remote": src.remote,
                                        "branch": src.branch}}
                (self.models_root / f"{model_id}.meta.json").write_text(json.dumps(entry, indent=2))
                self._derived[model_id] = entry
            else:
                tmp.unlink(missing_ok=True)
        return next(m for m in self.models() if m.model_id == model_id), created

    def rebuild(self, model_id: str) -> tuple[S.ModelSummary, bool]:
        """Build a built model again from its recorded source parameters on the active ACT engine."""
        entry = self.entry(model_id)
        p = entry.get("params", {})
        try:
            if entry.get("source") == "torch":
                indices = [int(x) for x in str(p["indices"]).split(",")] if "indices" in p else None
                req: S.LoadVnnlibRequest | S.LoadTorchRequest = S.LoadTorchRequest(
                    kind="torch", source_id=str(p["source_id"]), index=int(p["index"]), eps=float(p["eps"]),
                    indices=indices)
            elif entry.get("source") == "vnnlib":
                req = S.LoadVnnlibRequest(kind="vnnlib", benchmark=str(p["benchmark"]), onnx=str(p["onnx"]),
                                          vnnlib=str(p["vnnlib"]),
                                          vnnlibs=str(p["vnnlibs"]).split(",") if "vnnlibs" in p else None)
            else:
                raise AppError(422, "not_rebuildable", f"{model_id} is a pinned catalog model, not built by the workbench")
        except (KeyError, ValueError) as err:
            raise AppError(422, "not_rebuildable", f"{model_id} lacks the source parameters to rebuild it: {err}") from err
        return self.load(req)

    # -- descriptions ----------------------------------------------------------
    def describe(self, model_id: str) -> S.ModelDescriptionOut:
        self.engine.require_capability("model.load_json")
        self.engine.require_capability("spec.read")
        return self._describe_cached(model_id, self.engine.info.commit)

    @lru_cache(maxsize=32)
    def _describe_cached(self, model_id: str, act_commit: str | None) -> S.ModelDescriptionOut:
        path = self.path(model_id)
        try:
            d = describe_model(path)
        except BridgeError as err:
            if err.code == "model_load_failed":
                self._load_checks[(model_id, act_commit)] = False
            raise bridge_error(err) from err
        self._load_checks[(model_id, act_commit)] = True
        raw = asdict(d)
        for spec in raw["input_specs"]:
            rows = spec["shape"][0] if len(spec["shape"]) == 4 and spec["shape"][0] > 1 else 1
            per_row = len(spec["lb"]) // rows  # the browser shows a batched spec one row at a time
            shown = per_row <= DISPLAY_VALUES
            spec["lb"] = wire_numbers(spec["lb"]) if shown else None
            spec["ub"] = wire_numbers(spec["ub"]) if shown else None
            spec["center"] = wire_numbers(spec["center"]) if shown and spec["center"] is not None else None
        if raw["output_spec"] and raw["output_spec"]["thresholds"] is not None:
            raw["output_spec"]["thresholds"] = wire_numbers(raw["output_spec"]["thresholds"])
        raw.pop("source_path")
        return S.ModelDescriptionOut(model_id=model_id, act_commit=act_commit, **raw)

    # -- input provenance (MSV-08) ---------------------------------------------
    def _vnnlib_rows(self, entry: dict[str, Any]) -> list[VnnlibInstance] | None:
        """The VNN-LIB property behind each ACT input row of a model built from VNN-LIB sources, else None."""
        if entry.get("source") != "vnnlib":
            return None
        p = entry["params"]
        vnnlibs = str(p["vnnlibs"]).split(",") if "vnnlibs" in p else [str(p["vnnlib"])]
        return [VnnlibInstance(str(p["benchmark"]), str(p["onnx"]), v) for v in vnnlibs]

    def provenance(self, model_id: str) -> S.ProvenanceOut:
        rows = self._vnnlib_rows(self.entry(model_id))
        if rows is None:
            return S.ProvenanceOut(model_id=model_id, status="none", rows=[],
                                   reason="only models built from VNN-LIB properties have input provenance")
        out: list[S.InputProvenanceOut | None] = []
        for row, inst in enumerate(rows):
            p = model_provenance.input_provenance(model_sources.vnnlib_root() / inst.benchmark / inst.vnnlib)
            out.append(None if p is None else S.InputProvenanceOut(row=row, **asdict(p)))
        found = any(p is not None for p in out)
        return S.ProvenanceOut(model_id=model_id, status="available" if found else "none", rows=out,
                               reason=None if found else "No source metadata is recorded for these VNN-LIB properties")

    def nearest(self, model_id: str, req: S.NearestRequest) -> S.NearestOut:
        rows = self._vnnlib_rows(self.entry(model_id))
        if rows is None:
            raise AppError(404, "no_provenance", f"{model_id} is not built from VNN-LIB properties")
        if req.row >= len(rows):
            raise AppError(422, "invalid_row", f"{model_id} has {len(rows)} input row(s)")
        inst = rows[req.row]
        path = model_sources.vnnlib_root() / inst.benchmark / inst.vnnlib
        if model_provenance.input_provenance(path) is None:
            raise AppError(404, "no_provenance", f"No source metadata is recorded for {inst.benchmark}/{inst.vnnlib}")
        try:
            found = model_provenance.nearest_inputs(path, req.point, req.k)
        except ValueError as err:
            raise AppError(422, "invalid_point", str(err)) from err
        return S.NearestOut(model_id=model_id, row=req.row, neighbours=[S.InputNeighbourOut(**asdict(n)) for n in found])
