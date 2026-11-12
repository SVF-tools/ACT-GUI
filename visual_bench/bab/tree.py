"""Search-tree projection of a BaB run's committed waves (BAB-01).

Fed the lines of bab.jsonl in order (records/bab.py), it keeps every node ACT has named with the waves that created,
solved or evicted it, the per-wave statistics and ACT's terminal record. Node states are derived from ACT's outcomes
only; the tree never decides a verdict.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

PROVED = ("proved_main", "proved_terminal")
RETIRED = ("retired_max_depth", "retired_terminal")
STATES = ("pending", "branched", "proved", "falsified", "retired", "evicted", "unresolved")


@dataclass
class Node:
    node_id: int
    parent_id: int
    depth: int
    created_wave: int
    branch: dict[str, Any] | None = None
    evicted_wave: int | None = None
    solved_wave: int | None = None
    solve_status: str | None = None
    outcome: str | None = None
    bound: float | None = None
    bound_kind: str | None = None
    layers: list[dict[str, Any]] = field(default_factory=list)
    children: list[int] = field(default_factory=list)
    descendants: int = 0


class BabTree:
    def __init__(self) -> None:
        self.nodes: dict[int, Node] = {0: Node(0, -1, 0, 0)}
        self.waves: list[dict[str, Any]] = []
        self.terminal: dict[str, Any] | None = None
        self.end: dict[str, Any] | None = None

    def apply(self, line: dict[str, Any]) -> None:
        if line["kind"] == "wave":
            self._wave(line)
        elif line["kind"] == "terminal":
            self.terminal = {k: line[k] for k in ("seq", "wave", "t_ms", "status", "reason", "frontier_size", "node_id")}
        elif line["kind"] == "end":
            self.end = line
        else:
            raise ValueError(f"unknown BaB log line kind {line['kind']!r}")

    def _add(self, node_id: int, parent_id: int, depth: int, wave: int, branch: dict[str, Any] | None) -> Node:
        node = self.nodes[node_id] = Node(node_id, parent_id, depth, wave, branch)
        ancestor = self.nodes.get(parent_id)
        if ancestor is not None:
            ancestor.children.append(node_id)
        while ancestor is not None:
            ancestor.descendants += 1
            ancestor = self.nodes.get(ancestor.parent_id)
        return node

    def _wave(self, line: dict[str, Any]) -> None:
        wave = line["wave"]
        evicted = 0
        for child in line["children"]:
            node = self.nodes.get(child["node_id"]) or self._add(
                child["node_id"], child["parent_id"], child["depth"], wave, child["branch"])
            if child["frontier_state"] == "evicted" and node.evicted_wave is None:
                node.evicted_wave = wave
                evicted += 1
        for solved in line["nodes"]:
            node = self.nodes.get(solved["node_id"]) or self._add(
                solved["node_id"], solved["parent_id"], solved["depth"], wave, None)
            node.solved_wave, node.solve_status, node.outcome = wave, solved["solve_status"], solved["outcome"]
            node.bound, node.bound_kind, node.layers = solved["bound"], solved["bound_kind"], solved["layers"]
        for node_id in line["evicted_node_ids"]:
            node = self.nodes.get(node_id)
            if node is not None and node.evicted_wave is None:
                node.evicted_wave = wave
                evicted += 1
        outcomes = [n["outcome"] for n in line["nodes"]]
        bounds = [n["bound"] for n in line["nodes"] if n["bound"] is not None]
        self.waves.append({
            "wave": wave, "seq": line["seq"], "t_ms": line["t_ms"], "solved": len(outcomes),
            "created": len(line["children"]), "proved": sum(o in PROVED for o in outcomes),
            "branched": outcomes.count("branched"), "retired": sum(o in RETIRED for o in outcomes),
            "unresolved": outcomes.count("unresolved"), "evicted": evicted, "frontier_size": line["frontier_size"],
            "min_bound": min(bounds) if bounds else None,
        })

    def state(self, node: Node) -> str:
        terminal = self.terminal
        if terminal is not None and terminal["node_id"] == node.node_id:
            if terminal["status"] == "FALSIFIED":
                return "falsified"
            if terminal["status"] == "CERTIFIED":  # the root presolve proved the property
                return "proved"
        if node.outcome in PROVED:
            return "proved"
        if node.outcome == "branched":
            return "branched"
        if node.outcome in RETIRED:
            return "retired"
        if node.outcome is not None:
            return "unresolved"
        return "evicted" if node.evicted_wave is not None else "pending"

    def row(self, node: Node, hidden_children: int = 0) -> dict[str, Any]:
        return {"node_id": node.node_id, "parent_id": node.parent_id, "depth": node.depth, "state": self.state(node),
                "outcome": node.outcome, "created_wave": node.created_wave, "solved_wave": node.solved_wave,
                "evicted_wave": node.evicted_wave, "bound": node.bound, "branch": node.branch,
                "children": len(node.children), "descendants": node.descendants, "hidden_children": hidden_children}

    def detail(self, node_id: int) -> dict[str, Any]:
        node = self.nodes[node_id]
        return {"node": self.row(node), "solve_status": node.solve_status, "bound_kind": node.bound_kind,
                "layers": node.layers, "path": [self.row(n) for n in self.ancestors(node_id)],
                "children": [self.row(self.nodes[c]) for c in sorted(node.children)]}

    def ancestors(self, node_id: int) -> list[Node]:
        out = []
        parent = self.nodes.get(self.nodes[node_id].parent_id)
        while parent is not None:
            out.append(parent)
            parent = self.nodes.get(parent.parent_id)
        return out[::-1]

    def snapshot(self, root: int, limit: int) -> dict[str, Any]:
        """At most `limit` nodes breadth-first from root (KeyError for an unknown root), and the whole tree's counts."""
        order: list[int] = []
        queue = deque([self.nodes[root].node_id])
        while queue and len(order) < limit:
            node_id = queue.popleft()
            order.append(node_id)
            queue.extend(sorted(self.nodes[node_id].children))
        shown = set(order)
        rows = [self.row(self.nodes[i], sum(c not in shown for c in self.nodes[i].children)) for i in order]
        counts: dict[str, int] = {state: 0 for state in STATES}
        for node in self.nodes.values():
            counts[self.state(node)] += 1
        counts["nodes"] = len(self.nodes)
        counts["solved"] = sum(n.solved_wave is not None for n in self.nodes.values())
        return {"root": root, "path": [self.row(n) for n in self.ancestors(root)], "nodes": rows,
                "truncated": len(order) < self.nodes[root].descendants + 1, "counts": counts,
                "shares": self.shares(root)}

    def shares(self, root: int) -> dict[str, float]:
        """The root's subtree as fractions per leaf state, each node's share split equally among its children."""
        out: dict[str, float] = {state: 0.0 for state in STATES if state != "branched"}
        stack = [(root, 1.0)]
        while stack:
            node_id, share = stack.pop()
            node = self.nodes[node_id]
            if node.children:
                stack.extend((c, share / len(node.children)) for c in node.children)
            else:
                state = self.state(node)
                out["unresolved" if state == "branched" else state] += share
        return out
