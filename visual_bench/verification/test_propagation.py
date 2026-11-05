"""Native ACT worker/pipe/SSE/record/API integration, gated on the active observer capability."""
from __future__ import annotations

import pytest

from visual_bench.testing import follow_to_end


@pytest.mark.parametrize("domain", ["interval", "hybridz", "dual"])
def test_real_act_worker_records_live_propagation_and_own_domain(client, domain):
    wb = client.app.state.workbench
    if not wb.engine.capability_available("observe.propagation"):
        pytest.skip("active ACT lacks observe.propagation")
    response = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "interval", "domain": domain})
    assert response.status_code == 202, response.text
    run_id = response.json()["run_id"]
    events = follow_to_end(client, run_id)
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "completed", run["error"]
    propagated = [e for e in events if e["kind"] == "verify.propagation"]
    assert propagated
    assert all("values" not in e["payload"] for e in propagated)
    index = client.get(f"/api/runs/{run_id}/propagation").json()
    assert index["availability"] == "available" and index["complete"] is True
    assert index["records"] and {r["key"]["domain"] for r in index["records"]} == {domain}
    assert index["ignored_records"] == 0
    layer_id = next(r["key"]["layer_id"] for r in index["records"] if r["kind"] == "LayerBounds")
    detail = client.get(f"/api/runs/{run_id}/propagation/layers/{layer_id}").json()
    assert any("lb" in r["values"] for r in detail["records"])
    layers = client.get(f"/api/runs/{run_id}/layers").json()
    assert layers["method"] == domain and layers["provenance"]["domain"] == domain
    assert "propagation.json" in wb.records.hashes(run_id)
