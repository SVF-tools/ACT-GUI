"""Input provenance through the bridge (MSB-07): ACT's provenance records copied into neutral contracts.

The sidecar is synthetic (written in tmp_path): it checks the adapter's mapping on top of ACT's own reader, not the
safenlp_2024 reconstruction. Skipped unless the active ACT checkout has act.pipeline.gui.provenance_gui.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine_bridge.contracts import BridgeError, TextVariant, VnnlibInstance
from engine_bridge.engine_session import capability_available
from engine_bridge.model_spec import provenance, sources

RECORDED = VnnlibInstance("bench", "net.onnx", "vnnlib/a.vnnlib")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def bench(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    if not capability_available("source.provenance"):
        pytest.skip("the active ACT checkout has no act.pipeline.gui.provenance_gui (source.provenance)")
    monkeypatch.setattr(sources, "vnnlib_root", lambda: tmp_path)
    root = tmp_path / "bench"
    (root / "vnnlib").mkdir(parents=True)
    (root / "provenance").mkdir()
    recorded, other = root / "vnnlib" / "a.vnnlib", root / "vnnlib" / "b.vnnlib"
    recorded.write_text("; a\n")
    other.write_text("; b\n")
    manifest = {"schema": "act.input_provenance/1", "benchmark": "bench", "modality": "text",
                "representation": "2-d test space",
                "tasks": {"t": {"title": "T", "description": "test task", "class_names": ["yes", "no"],
                                "dataset": "d", "dataset_url": None}},
                "families": {"f": {"title": "family f", "description": "test family"}},
                "sources": [{"name": "synthetic", "commit": "0"}], "stats": {}}
    examples = [{"id": "t:0", "task": "t", "text": "zero", "label": 0, "split": "train_pos", "anchor": [0.0, 0.0]},
                {"id": "t:1", "task": "t", "text": "one", "label": 1, "split": "test_neg", "anchor": [1.0, 0.0]}]
    inputs = [{"files": {"vnnlib/a.vnnlib": _sha(recorded)}, "task": "t", "family": "f", "family_index": 3,
               "example": "t:0", "variants": [{"text": "zer0", "kind": "char_replacement", "kept": True, "cosine": 0.9}],
               "variants_status": "replayed", "match": {"status": "verified", "detail": "synthetic"}}]
    (root / "provenance" / "manifest.json").write_text(json.dumps(manifest))
    (root / "provenance" / "examples.jsonl").write_text("".join(json.dumps(e) + "\n" for e in examples))
    (root / "provenance" / "inputs.jsonl").write_text("".join(json.dumps(e) + "\n" for e in inputs))
    return root


def test_recorded_property_is_copied_out_of_act(bench: Path):
    p = provenance.input_provenance(RECORDED)
    assert p is not None
    assert (p.key, p.text, p.label, p.split, p.family_index, p.match_status) == (
        "vnnlib/a.vnnlib", "zero", 0, "train_pos", 3, "verified")
    assert p.anchor == (0.0, 0.0) and p.task.class_names == ("yes", "no") and p.family_title == "family f"
    assert p.variants == (TextVariant("zer0", "char_replacement", True, 0.9),)
    assert provenance.has_provenance("bench") and not provenance.has_provenance("elsewhere")
    assert provenance.input_provenance(VnnlibInstance("bench", "net.onnx", "vnnlib/b.vnnlib")) is None


def test_nearest_inputs_rank_known_examples_and_reject_other_dimensions(bench: Path):
    near = provenance.nearest_inputs(RECORDED, [0.9, 0.1], k=2)
    assert [n.example_id for n in near] == ["t:1", "t:0"] and near[0].label == 1
    assert abs(near[0].distance - 0.02 ** 0.5) < 1e-12
    with pytest.raises(BridgeError) as err:
        provenance.nearest_inputs(RECORDED, [1.0, 2.0, 3.0])
    assert err.value.code == "invalid_point"


def test_an_edited_instance_is_not_described(bench: Path):
    (bench / "vnnlib" / "a.vnnlib").write_text("; edited after the sidecar was built\n")
    assert provenance.input_provenance(RECORDED) is None
