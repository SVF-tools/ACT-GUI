"""Assistant explanation tests through the HTTP surface (deterministic fake provider, real ACT run).

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from visual_bench.testing import follow_to_end


def test_explanation_cites_resolvable_evidence_and_keeps_context(client: TestClient):
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    ctx = {"model_id": "bab_deep_mlp", "run_id": run_id, "layer_id": 3, "neuron": 1}
    ans = client.post("/api/assistant/explain", json={"context": ctx, "question": "why?"}).json()
    assert ans["context"] == ctx and ans["provider_kind"] == "fake"
    ids = {e["ref_id"] for e in ans["evidence"]}
    assert all(ref in ids for s in ans["sections"] for ref in s["evidence"])
    assert any("UNKNOWN" in e["value"] for e in ans["evidence"] if e["kind"] == "run_result")
    mismatch = client.post("/api/assistant/explain", json={"context": {**ctx, "model_id": "range_check"}, "question": "?"})
    assert mismatch.status_code == 422 and mismatch.json()["error"]["code"] == "context_mismatch"
