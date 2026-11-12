"""BaB search tree: projection of recorded waves, log reading, and the HTTP surface on real ACT runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from visual_bench.bab.tree import BabTree
from visual_bench.records import RecordStore
from visual_bench.testing import follow_to_end


def _child(node_id: int, parent: int, depth: int, frontier: str = "pending") -> dict[str, Any]:
    return {"node_id": node_id, "parent_id": parent, "depth": depth, "frontier_state": frontier,
            "branch": {"kind": "input_axis", "phases": [], "intervals": [{"axis": node_id, "lb": 0.0, "ub": 0.5}]}}


def _solved(node_id: int, parent: int, depth: int, outcome: str, bound: float | None) -> dict[str, Any]:
    return {"node_id": node_id, "parent_id": parent, "depth": depth, "solve_status": "SAT", "outcome": outcome,
            "bound": bound, "bound_kind": "certified_node_lower_bound", "layers": []}


def _wave(seq: int, wave: int, nodes: list[dict[str, Any]], children: list[dict[str, Any]], frontier: int,
          evicted: tuple[int, ...] = ()) -> dict[str, Any]:
    return {"kind": "wave", "seq": seq, "wave": wave, "t_ms": 10.0 * wave, "nodes": nodes, "children": children,
            "frontier_size": frontier, "evicted_node_ids": list(evicted)}


def _terminal(seq: int, wave: int, status: str, node_id: int | None = None) -> dict[str, Any]:
    return {"kind": "terminal", "seq": seq, "wave": wave, "t_ms": 99.0, "status": status, "reason": "r",
            "frontier_size": 0, "node_id": node_id, "parent_id": None, "depth": None}


SEARCH = [  # root splits; child 1 is proved, child 2 splits into a queued 3 and a capped-away 4; 5 is evicted later
    _wave(1, 1, [_solved(0, -1, 0, "branched", -2.0)], [_child(1, 0, 1), _child(2, 0, 1)], 2),
    _wave(2, 2, [_solved(1, 0, 1, "proved_main", 0.5), _solved(2, 0, 1, "branched", -1.0)],
          [_child(3, 2, 2), _child(4, 2, 2, "evicted"), _child(5, 2, 2)], 2),
    _wave(3, 3, [], [], 1, evicted=(5,)),
    _terminal(4, 3, "UNKNOWN"),
]


def _tree(lines: list[dict[str, Any]]) -> BabTree:
    tree = BabTree()
    for line in lines:
        tree.apply(line)
    return tree


def test_projection_tracks_states_waves_and_shares():
    tree = _tree(SEARCH)
    snap = tree.snapshot(0, 100)
    rows = {r["node_id"]: r for r in snap["nodes"]}
    assert {i: r["state"] for i, r in rows.items()} == {0: "branched", 1: "proved", 2: "branched", 3: "pending",
                                                         4: "evicted", 5: "evicted"}
    assert (rows[5]["created_wave"], rows[5]["evicted_wave"], rows[1]["solved_wave"]) == (2, 3, 2)
    assert rows[0]["descendants"] == 5 and rows[2]["children"] == 3 and not snap["truncated"]
    assert snap["counts"] == {"pending": 1, "branched": 2, "proved": 1, "falsified": 0, "retired": 0, "evicted": 2,
                              "unresolved": 0, "nodes": 6, "solved": 3}
    assert snap["shares"]["proved"] == 0.5 and snap["shares"]["pending"] == pytest.approx(1 / 6)
    assert snap["shares"]["evicted"] == pytest.approx(1 / 3)
    second = tree.waves[1]
    assert (second["proved"], second["branched"], second["evicted"], second["min_bound"]) == (1, 1, 1, -1.0)
    assert tree.waves[2]["evicted"] == 1 and tree.terminal is not None and tree.terminal["status"] == "UNKNOWN"


def test_snapshot_keeps_a_node_budget_and_focuses_subtrees():
    tree = _tree(SEARCH)
    snap = tree.snapshot(0, 3)
    assert [r["node_id"] for r in snap["nodes"]] == [0, 1, 2] and snap["truncated"]
    assert next(r for r in snap["nodes"] if r["node_id"] == 2)["hidden_children"] == 3
    focus = tree.snapshot(2, 100)
    assert [r["node_id"] for r in focus["path"]] == [0] and [r["node_id"] for r in focus["nodes"]] == [2, 3, 4, 5]
    assert focus["shares"]["pending"] == pytest.approx(1 / 3) and focus["shares"]["evicted"] == pytest.approx(2 / 3)
    detail = tree.detail(3)
    assert [r["node_id"] for r in detail["path"]] == [0, 2] and detail["node"]["branch"]["intervals"][0]["axis"] == 3
    with pytest.raises(KeyError):
        tree.snapshot(42, 10)


def test_terminal_names_the_deciding_node():
    falsified = _tree([*SEARCH[:2], _terminal(3, 3, "FALSIFIED", node_id=3)])
    assert falsified.state(falsified.nodes[3]) == "falsified"
    presolved = _tree([_terminal(1, 0, "CERTIFIED", node_id=0)])
    assert presolved.state(presolved.nodes[0]) == "proved" and presolved.shares(0)["proved"] == 1.0


def test_log_reads_complete_lines_from_an_offset_and_checks_the_seal(tmp_path: Path):
    store = RecordStore(tmp_path)
    store.create("run-0123456789ab", {"created_at": "now"})
    log = store.run_dir("run-0123456789ab") / "bab.jsonl"
    log.write_text(json.dumps(SEARCH[0]) + "\n" + '{"kind": "wa')  # torn tail: the worker is mid-write
    read = store.bab_log("run-0123456789ab")
    assert read is not None
    lines, offset = read
    assert lines == [SEARCH[0]] and offset == len(json.dumps(SEARCH[0])) + 1
    log.write_text(json.dumps(SEARCH[0]) + "\n" + json.dumps(SEARCH[1]) + "\n")
    assert store.bab_log("run-0123456789ab", offset) == ([SEARCH[1]], log.stat().st_size)
    store.seal("run-0123456789ab")
    assert store.bab_log("run-0123456789ab", offset, sealed=True) == ([SEARCH[1]], log.stat().st_size)
    log.write_text(log.read_text() + json.dumps(SEARCH[2]) + "\n")
    with pytest.raises(ValueError):
        store.bab_log("run-0123456789ab", 0, sealed=True)


def _tree_capability(client: TestClient) -> bool:
    caps = {c["name"]: c["availability"] for c in client.get("/api/engine").json()["capabilities"]}
    return caps["events.bab_nodes"] == "available"


@pytest.mark.parametrize("model_id", ["bab_deep_mlp", "unsafe_linear"])
def test_bab_run_records_its_search_tree(client: TestClient, model_id: str):
    if not _tree_capability(client):
        pytest.skip("ACT checkout has no act.pipeline.gui.bab_gui; select SVF-tools/ACT main >= 22693fb via ACT_GUI_ENGINES")
    run_id = client.post("/api/runs", json={"model_id": model_id, "method": "bab", "time_budget_s": 15}).json()["run_id"]
    events = follow_to_end(client, run_id)
    assert "verify.bab" in [e["kind"] for e in events] and events[-1]["kind"] == "run.completed"
    run = client.get(f"/api/runs/{run_id}").json()
    tree = client.get(f"/api/runs/{run_id}/bab").json()
    assert tree["availability"] == "available" and tree["complete"] and tree["recording_error"] is None
    assert tree["terminal"]["status"] == run["result"]["act_status"]
    root = tree["nodes"][0]
    if run["result"]["act_status"] == "FALSIFIED":  # ACT's counterexample came from the root, before any wave
        assert root["state"] == "falsified" and tree["waves"] == []
    else:
        assert tree["counts"]["solved"] == run["result"]["bab_summary"]["nodes"] and root["state"] == "proved"
    assert client.get(f"/api/runs/{run_id}/bab/nodes/0").json()["node"]["node_id"] == 0
    assert client.get(f"/api/runs/{run_id}/bab/nodes/99999").json()["error"]["code"] == "node_not_found"
    assert client.get(f"/api/runs/{run_id}/coverage").json()["node_events"] == "available"


def test_bab_tree_is_unsupported_without_act_wave_records(client: TestClient):
    if _tree_capability(client):
        pytest.skip("the active ACT checkout records BaB waves")
    run_id = client.post("/api/runs", json={"model_id": "bab_deep_mlp", "method": "bab", "time_budget_s": 15}).json()["run_id"]
    follow_to_end(client, run_id)
    tree = client.get(f"/api/runs/{run_id}/bab").json()
    assert tree["availability"] == "unsupported" and tree["nodes"] == [] and "act.pipeline.gui.bab_gui" in tree["reason"]
    assert client.get(f"/api/runs/{run_id}/coverage").json()["node_events"] == "unsupported"
