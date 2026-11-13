"""Input provenance over HTTP (MSV-08): GET /api/models/{id}/provenance and POST .../provenance/nearest.

Real ACT builds of a safenlp_2024 instance with dataset metadata installed under ACT_ROOT/data/vnnlib.
Text and neighbours are workbench data and require no provenance API in the active ACT engine.
"""
from __future__ import annotations

from typing import Any
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from engine_bridge.model_spec import sources as model_sources
from visual_bench.testing import sources_or_skip

INSTANCE = {"kind": "vnnlib", "benchmark": "safenlp_2024", "onnx": "onnx/medical/perturbations_0.onnx",
            "vnnlib": "vnnlib/medical/hyperrectangle_132.vnnlib"}


def _safenlp(client: TestClient) -> dict[str, Any]:
    bench = next((b for b in sources_or_skip(client)["vnnlib"] if b["benchmark"] == "safenlp_2024"), None)
    if bench is None or not any(i["vnnlib"] == INSTANCE["vnnlib"] for i in bench["instances"]):
        pytest.skip("safenlp_2024 medical hyperrectangle_132 is not installed")
    return bench


def test_catalog_models_have_no_input_provenance(client: TestClient):
    model_id = next(m["model_id"] for m in client.get("/api/models").json() if m["source"] == "catalog")
    out = client.get(f"/api/models/{model_id}/provenance").json()
    assert (out["status"], out["rows"]) == ("none", [])
    near = client.post(f"/api/models/{model_id}/provenance/nearest", json={"row": 0, "point": [0.0]})
    assert near.status_code == 404 and near.json()["error"]["code"] == "no_provenance"


def test_safenlp_property_shows_its_source_sentence_and_neighbours(client: TestClient):
    bench = _safenlp(client)
    assert "source.provenance" not in {c["name"] for c in client.get("/api/engine").json()["capabilities"]}
    model_id = client.post("/api/models", json={"source": INSTANCE}).json()["model_id"]
    out = client.get(f"/api/models/{model_id}/provenance").json()
    assert out["status"] == "available" and len(out["rows"]) == 1
    row = out["rows"][0]
    assert (row["row"], row["benchmark"], row["key"], row["family"]) == (0, "safenlp_2024", INSTANCE["vnnlib"], "character")
    assert row["text"] and row["task"]["class_names"][row["label"]] and len(row["anchor"]) == 30
    listed = next(i for i in bench["instances"] if i["vnnlib"] == INSTANCE["vnnlib"])
    assert listed["text"] == row["text"]

    near = client.post(f"/api/models/{model_id}/provenance/nearest",
                       json={"row": 0, "point": row["anchor"], "k": 2}).json()
    assert near["neighbours"][0]["example_id"] == row["example_id"] and near["neighbours"][0]["distance"] < 1e-9
    assert near["neighbours"][1]["distance"] > 0
    wrong = client.post(f"/api/models/{model_id}/provenance/nearest", json={"row": 0, "point": [0.0, 1.0]})
    assert wrong.status_code == 422 and wrong.json()["error"]["code"] == "invalid_point"
    beyond = client.post(f"/api/models/{model_id}/provenance/nearest", json={"row": 3, "point": row["anchor"]})
    assert beyond.status_code == 422 and beyond.json()["error"]["code"] == "invalid_row"


def test_missing_dataset_metadata_reports_none(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _safenlp(client)
    model_id = client.post("/api/models", json={"source": INSTANCE}).json()["model_id"]
    monkeypatch.setattr(model_sources, "vnnlib_root", lambda: tmp_path)
    out = client.get(f"/api/models/{model_id}/provenance").json()
    assert (out["status"], out["rows"]) == ("none", [None])
    near = client.post(f"/api/models/{model_id}/provenance/nearest", json={"row": 0, "point": [0.0] * 30})
    assert near.status_code == 404 and near.json()["error"]["code"] == "no_provenance"
