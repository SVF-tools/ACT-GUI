"""Model catalog, model sources, and model/spec description payloads (/api/models, /api/sources)."""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, model_validator

from visual_bench.wire import WireNumber, Scalar, Method, Wire

__all__ = ['NativeResult', 'BuiltWithOut', 'EngineCheck', 'ModelSummary', 'VnnlibInstanceOut', 'VnnlibBenchmarkOut', 'ClassifierSourceOut', 'SourcesOut', 'SampleOut', 'LoadVnnlibRequest', 'LoadTorchRequest', 'LoadModelRequest', 'LoadModelBody', 'ParamOut', 'LayerOut', 'InputSpecOut', 'OutputSpecOut', 'ModelDescriptionOut']


class NativeResult(Wire):
    status: str
    elapsed_s: float
    nodes: int | None

class BuiltWithOut(Wire):
    """The ACT engine a model was built on: its commit and where that code came from."""
    commit: str | None
    kind: Literal["baseline", "branch"]
    remote: str | None = None
    branch: str | None = None

# Whether a built model's ACT net loads on the active engine: built on the same commit, loaded (or failed to load)
# when it was first described on this commit, or not tried yet. Catalog models are pinned files: None.
EngineCheck = Literal["same_commit", "loads", "load_failed", "unchecked"]

class ModelSummary(Wire):
    model_id: str
    description: str
    act_path: str
    sha256: str
    methods: list[Method]
    native: dict[str, NativeResult]
    source: Literal["catalog", "vnnlib", "torch"] = "catalog"
    params: dict[str, Scalar] = {}  # how a vnnlib/torch model was built (benchmark, files, dataset, index, eps, ...)
    built_with: BuiltWithOut | None = None  # None for catalog models and models built before it was recorded
    engine_check: EngineCheck | None = None

class VnnlibInstanceOut(Wire):
    onnx: str  # one path, or one per network of a multi-network property, comma-separated in network order
    vnnlib: str

class VnnlibBenchmarkOut(Wire):
    benchmark: str
    instances: list[VnnlibInstanceOut]

class ClassifierSourceOut(Wire):
    source_id: str
    dataset: str
    onnx: str
    description: str

class SourcesOut(Wire):
    vnnlib: list[VnnlibBenchmarkOut]
    classifiers: list[ClassifierSourceOut]
    vnnlib_root: str

class SampleOut(Wire):
    dataset: str
    index: int
    size: int
    label: int
    shape: list[int]
    pixels: list[float]  # CHW in [0, 1]

BenchmarkPath = Annotated[str, Field(min_length=1, max_length=512, pattern=r"^[A-Za-z0-9_./-]+$")]
# One ONNX path, or one per network of a multi-network property, comma-separated in network order.
OnnxPaths = Annotated[str, Field(min_length=1, max_length=2048, pattern=r"^[A-Za-z0-9_./-]+(,[A-Za-z0-9_./-]+)*$")]

class LoadVnnlibRequest(Wire):
    kind: Literal["vnnlib"]
    benchmark: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    onnx: OnnxPaths
    vnnlib: BenchmarkPath
    # Properties of a batch on this one network, one ACT input row each, fuzzed together; None = [vnnlib].
    vnnlibs: list[BenchmarkPath] | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def _relative_paths(self) -> "LoadVnnlibRequest":
        if any(p.startswith("/") or ".." in p.split("/") for p in (*self.onnx.split(","), self.vnnlib, *(self.vnnlibs or ()))):
            raise ValueError("onnx and vnnlib must be paths inside the benchmark directory")
        if self.vnnlibs is not None and (self.vnnlibs[0] != self.vnnlib or len(set(self.vnnlibs)) != len(self.vnnlibs)):
            raise ValueError("vnnlibs must be distinct and start with vnnlib")
        return self

class LoadTorchRequest(Wire):
    kind: Literal["torch"]
    source_id: str = Field(min_length=1, max_length=64)
    index: int = Field(ge=0, le=1_000_000)
    eps: float = Field(ge=0, le=1)
    # Test images of a batch, one ACT input row each, fuzzed together; None = [index]. BaB takes single-image nets only.
    indices: list[Annotated[int, Field(ge=0, le=1_000_000)]] | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def _batch_starts_at_index(self) -> "LoadTorchRequest":
        if self.indices is not None and (self.indices[0] != self.index or len(set(self.indices)) != len(self.indices)):
            raise ValueError("indices must be distinct and start with index")
        return self

LoadModelRequest = Annotated[Union[LoadVnnlibRequest, LoadTorchRequest], Field(discriminator="kind")]

class LoadModelBody(Wire):
    source: LoadModelRequest

class ParamOut(Wire):
    name: str
    shape: list[int] | None
    value: str | None

class LayerOut(Wire):
    layer_id: int
    kind: str
    in_vars: int
    out_vars: int
    output_shape: list[int] | None
    preds: list[int]
    succs: list[int]
    params: list[ParamOut]

class InputSpecOut(Wire):
    layer_id: int
    kind: str
    # lb/ub/center are None above DISPLAY_VALUES values per row (too large to display); shape is always given.
    lb: list[WireNumber] | None
    ub: list[WireNumber] | None
    shape: list[int]  # lb/ub tensor shape as ACT stores it (images: N, C, H, W)
    center: list[WireNumber] | None  # unperturbed input, when the spec records one
    dataset: str | None  # dataset name from the INPUT layer, e.g. "mnist", "cifar10"

class OutputSpecOut(Wire):
    layer_id: int
    kind: str
    rows: int
    matrix: list[list[float]] | None
    thresholds: list[WireNumber] | None
    text: str
    true_class: int | None  # y_true of a robustness assertion (TOP1_ROBUST etc.)

class ModelDescriptionOut(Wire):
    model_id: str
    sha256: str
    act_commit: str | None
    layers: list[LayerOut]
    input_specs: list[InputSpecOut]
    output_spec: OutputSpecOut | None
    input_dim: int
    output_dim: int
