"""Fuzz run, fuzzing record, and saved counterexample tests through the HTTP surface (real ACTFuzzer runs).

Run completion is awaited on the run's own SSE stream (bounded by the worker timeout), never with sleeps.
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from visual_bench.server import create_app
from visual_bench.testing import follow_to_end, sources_or_skip


def test_fuzz_run_streams_progress_and_records_act_counterexamples(client: TestClient, tmp_path: Path):
    assert "fuzz" in client.get("/api/models").json()[0]["methods"]
    body = {"model_id": "unsafe_linear", "method": "fuzz", "time_budget_s": 10,
            "fuzz": {"max_iterations": 50, "rng_seed": 7}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    kinds = [e["kind"] for e in follow_to_end(client, run_id)]
    assert kinds[:2] == ["run.queued", "run.started"] and kinds[-1] == "run.completed"
    assert set(kinds[2:-1]) == {"fuzz.progress"}

    run = client.get(f"/api/runs/{run_id}").json()
    assert run["result"]["verdict"] == "falsified" and run["native_reference"] is None
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["availability"] == "available" and fz["options"]["rng_seed"] == 7
    assert fz["summary"]["iterations"] == 50 and fz["summary"]["counterexample_count"] >= 1
    assert run["result"]["counterexample"] == fz["counterexamples"][0]["input"]
    assert fz["seeds"] and len(fz["counterexamples"][0]["seed_output"]) == len(fz["seeds"][0]["output"])
    assert fz["timeline"][-1]["iteration"] == 50
    assert fz["frames"] and fz["frames"][-1]["iteration"] == 50
    assert len(fz["frames"][0]["input"]) == len(fz["frames"][0]["seed_input"]) == len(fz["seeds"][0]["input"])
    assert sum(s["selected"] for s in fz["strategies"]) == 50
    assert "fuzzing.json" in json.loads((tmp_path / "records" / run_id / "artifacts.json").read_text())

def test_saved_counterexample_is_idempotent_and_exports_vnnlib2_assignment(client: TestClient):
    body = {"model_id": "unsafe_linear", "method": "fuzz", "time_budget_s": 10,
            "fuzz": {"max_iterations": 50, "rng_seed": 7}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    follow_to_end(client, run_id)
    ce = client.get(f"/api/runs/{run_id}/fuzzing").json()["counterexamples"][0]
    url = f"/api/runs/{run_id}/saved-counterexamples"
    first, again = client.post(url, json={"index": ce["index"]}), client.post(url, json={"index": ce["index"]})
    assert (first.status_code, again.status_code) == (201, 200) and first.json() == again.json()
    assert client.post(url, json={"index": 999}).json()["error"]["code"] == "counterexample_not_found"
    saved = client.get(f"/api/runs/{run_id}/fuzzing").json()["saved"]
    assert [s["counterexample"] for s in saved] == [ce]

    resp = client.get(f"{url}/{ce['index']}/vnnlib")
    assert resp.status_code == 200 and f"{run_id}-ce{ce['index']}.counterexample" in resp.headers["content-disposition"]
    # VNN-COMP result: "sat", then per variable "<name> <type> [<dims>]" and its values in row-major order.
    lines = resp.text.splitlines()
    shape = client.get("/api/models/unsafe_linear").json()["input_specs"][0]["shape"]
    nx, ny = len(ce["input"]), len(ce["output"])
    assert lines[0] == "sat" and lines[1] == f"X float64 [{','.join(map(str, shape))}]"
    assert [float(v) for v in lines[2:2 + nx]] == ce["input"]
    assert lines[2 + nx] == f"Y float64 [1,{ny}]" and [float(v) for v in lines[3 + nx:]] == ce["output"]
    assert client.get(f"{url}/12345/vnnlib").status_code == 404
    bundle = zipfile.ZipFile(io.BytesIO(client.get(f"/api/runs/{run_id}/export").content))
    assert f"{run_id}/saved_counterexamples.json" in bundle.namelist()

def test_stop_ends_fuzz_run_with_act_report_of_iterations_run(tmp_path: Path):
    app = create_app(tmp_path / "records")
    client = TestClient(app)
    body = {"model_id": "bab_deep_mlp", "method": "fuzz", "time_budget_s": 120,
            "fuzz": {"max_iterations": 1_000_000, "rng_seed": 0}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    # Wait on the record store's commit signal for ACT's first progress report (an SSE stream the test
    # closes early would keep the TestClient waiting until the run ends).
    records = app.state.workbench.records
    seq = 0
    while True:
        evs = records.wait_for_events(run_id, seq, 60.0)
        assert evs, "no fuzz progress within 60 s"
        if any(e["kind"] == "fuzz.progress" for e in evs):
            break
        seq = evs[-1]["seq"]
    assert client.post(f"/api/runs/{run_id}/stop").json()["status"] == "running"
    kinds = [e["kind"] for e in follow_to_end(client, run_id)]
    assert "run.stop_requested" in kinds and kinds[-1] == "run.completed"
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["summary"]["stopped"] is True and fz["summary"]["iterations"] < 1_000_000
    assert client.post(f"/api/runs/{run_id}/stop").json()["status"] == "completed"  # no-op once terminal

def test_fuzz_defaults_match_the_pinned_act_pipeline_yaml(client: TestClient):
    from engine_bridge.execution import fuzzing_defaults

    served = client.get("/api/fuzz/defaults").json()
    act = fuzzing_defaults()
    assert act and {k: served[k] for k in act} == act

def test_fuzz_hyperparameters_reach_act_and_invalid_ones_are_rejected(client: TestClient):
    zero = {k: 0 for k in ("gradient", "pgd", "activation", "boundary", "random")}
    bad = client.post("/api/runs", json={"model_id": "unsafe_linear", "method": "fuzz",
                                         "fuzz": {"mutation_weights": zero}})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_request"
    body = {"model_id": "unsafe_linear", "method": "fuzz", "time_budget_s": 10,
            "fuzz": {"max_iterations": 20, "rng_seed": 1, "perturb_mode": "adaptive_perdim", "perturb_scale": 0.05,
                     "seed_selection_strategy": "random", "coverage_strategy": "BestInputCov", "pgd_restarts": 2,
                     "mutation_weights": {**zero, "random": 1}}}
    run_id = client.post("/api/runs", json=body).json()["run_id"]
    follow_to_end(client, run_id)
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    cfg = fz["config"]
    assert (cfg["perturb_mode"], cfg["perturb_scale"], cfg["seed_selection_strategy"], cfg["coverage_strategy"],
            cfg["pgd_restarts"]) == ("adaptive_perdim", 0.05, "random", "BestInputCov", 2)
    assert {s["name"] for s in fz["strategies"] if s["selected"]} == {"random"}

def test_fuzz_options_require_fuzz_method_and_other_runs_have_no_fuzzing(client: TestClient):
    bad = client.post("/api/runs", json={"model_id": "range_check", "method": "interval", "fuzz": {}})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_request"
    run_id = client.post("/api/runs", json={"model_id": "range_check", "method": "interval"}).json()["run_id"]
    follow_to_end(client, run_id)
    assert client.get(f"/api/runs/{run_id}/fuzzing").json()["availability"] == "unsupported"

def test_torch_batch_is_one_net_fuzzed_row_by_row(client: TestClient):
    sources_or_skip(client)
    body = {"source": {"kind": "torch", "source_id": "mnist_conv_small", "index": 3, "eps": 0.3, "indices": [3, 0, 7]}}
    m = client.post("/api/models", json=body).json()
    assert (m["methods"], m["params"]["batch"], m["params"]["indices"]) == (["interval", "fuzz"], 3, "3,0,7")
    d = client.get(f"/api/models/{m['model_id']}").json()
    assert d["input_specs"][0]["shape"] == [3, 1, 28, 28]
    full = {"source": {"kind": "torch", "source_id": "cifar10_conv_med", "index": 0, "eps": 0.01, "indices": list(range(64))}}
    big = client.post("/api/models", json=full).json()
    assert client.get(f"/api/models/{big['model_id']}").json()["input_specs"][0]["shape"] == [64, 3, 32, 32]
    assert client.post("/api/runs", json={"model_id": m["model_id"], "method": "bab"}).status_code != 202

    run_id = client.post("/api/runs", json={"model_id": m["model_id"], "method": "fuzz", "time_budget_s": 30,
                                           "fuzz": {"max_iterations": 300, "rng_seed": 0}}).json()["run_id"]
    follow_to_end(client, run_id)
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["config"]["batch_size"] == 3 and [s["row"] for s in fz["seeds"]] == [0, 1, 2]
    rows = {c["spec_row"] for c in fz["counterexamples"]}
    assert rows and rows <= {0, 1, 2}  # recorded counterexamples are the first ones found (capped)
    labels = [int(x) for x in m["params"]["targets"].split(",")]
    assert all(c["true_class"] == labels[c["spec_row"]] for c in fz["counterexamples"])

def test_vnnlib_properties_on_one_network_are_one_net_fuzzed_row_by_row(client: TestClient):
    s = sources_or_skip(client)
    cora = next(b for b in s["vnnlib"] if b["benchmark"] == "cora_2024")
    props = [i["vnnlib"] for i in cora["instances"] if i["onnx"] == "onnx/mnist-point.onnx"][:3]
    body = {"source": {"kind": "vnnlib", "benchmark": "cora_2024", "onnx": "onnx/mnist-point.onnx",
                       "vnnlib": props[0], "vnnlibs": props}}
    m = client.post("/api/models", json=body).json()
    assert (m["methods"], m["params"]["batch"], m["params"]["vnnlibs"]) == (["interval", "fuzz"], 3, ",".join(props))
    assert client.get(f"/api/models/{m['model_id']}").json()["input_specs"][0]["shape"] == [3, 784]

    run_id = client.post("/api/runs", json={"model_id": m["model_id"], "method": "fuzz", "time_budget_s": 30,
                                           "fuzz": {"max_iterations": 50, "rng_seed": 0}}).json()["run_id"]
    follow_to_end(client, run_id)
    fz = client.get(f"/api/runs/{run_id}/fuzzing").json()
    assert fz["config"]["batch_size"] == 3 and [s["row"] for s in fz["seeds"]] == [0, 1, 2]
    rebuilt = client.post(f"/api/models/{m['model_id']}/rebuild").json()
    assert rebuilt["model_id"] == m["model_id"]
