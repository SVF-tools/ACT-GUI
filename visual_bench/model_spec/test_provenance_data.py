"""Workbench dataset metadata: source matching, nearest examples and file-integrity checks.

Synthetic sidecars exercise the real reader without an ACT checkout or provider.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from visual_bench.model_spec import provenance
from visual_bench.model_spec.provenance import TextVariant

RECORDED = "vnnlib/a.vnnlib"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def bench(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ACT_ROOT", str(tmp_path / "no-act-checkout"))
    monkeypatch.setenv("ACT_CODE_ROOT", str(tmp_path / "no-act-checkout"))
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


def test_recorded_property_exposes_its_dataset_metadata(bench: Path):
    p = provenance.input_provenance(bench / RECORDED)
    assert p is not None
    assert (p.key, p.text, p.label, p.split, p.family_index, p.match_status) == (
        "vnnlib/a.vnnlib", "zero", 0, "train_pos", 3, "verified")
    assert p.anchor == (0.0, 0.0) and p.task.class_names == ("yes", "no") and p.family_title == "family f"
    assert p.variants == (TextVariant("zer0", "char_replacement", True, 0.9),)
    assert provenance.input_provenance(bench / "vnnlib/b.vnnlib") is None


def test_nearest_inputs_rank_known_examples_and_reject_other_dimensions(bench: Path):
    near = provenance.nearest_inputs(bench / RECORDED, [0.9, 0.1], k=2)
    assert [n.example_id for n in near] == ["t:1", "t:0"] and near[0].label == 1
    assert abs(near[0].distance - 0.02 ** 0.5) < 1e-12
    with pytest.raises(ValueError, match="point has 3 values"):
        provenance.nearest_inputs(bench / RECORDED, [1.0, 2.0, 3.0])


def test_an_edited_instance_is_not_described(bench: Path):
    (bench / "vnnlib" / "a.vnnlib").write_text("; edited after the sidecar was built\n")
    assert provenance.input_provenance(bench / RECORDED) is None
