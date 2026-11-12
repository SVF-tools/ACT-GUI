"""BaB views of a run (BAB-01): observation coverage and the search tree projected from its recorded waves.

A run records waves only when its ACT checkout passed events.bab_nodes at start (manifest execution.bab_tree).
The tree of a running run is read from the unsealed log incrementally; a completed run's log must match its seal.
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass

from engine_bridge.events import observation_coverage
from visual_bench.bab import schemas as S
from visual_bench.bab.tree import BabTree
from visual_bench.errors import AppError
from visual_bench.records import RecordStore
from visual_bench.verification.service import RunService

CACHED_TREES = 16


@dataclass
class _Loaded:
    tree: BabTree
    offset: int
    sealed: bool


class BabService:
    def __init__(self, runs: RunService, records: RecordStore) -> None:
        self.runs = runs
        self.records = records
        self._lock = threading.Lock()
        self._trees: OrderedDict[str, _Loaded] = OrderedDict()

    def _records_waves(self, run_id: str) -> bool:
        return bool(self.records.manifest(run_id).get("execution", {}).get("bab_tree"))

    def coverage(self, run_id: str) -> S.CoverageOut:
        run = self.runs.get(run_id)
        cov = observation_coverage(run.method == "bab" and self._records_waves(run_id))
        summary = run.result.bab_summary if run.result else None
        return S.CoverageOut.model_validate({
            **cov, "run_id": run_id, "summary": summary,
            "final_summary": "available" if summary is not None else
            ("pending" if run.status in ("queued", "running") else "not_recorded")})

    def _load(self, run_id: str) -> BabTree | None:
        sealed = self.records.hashes(run_id) is not None
        with self._lock:
            loaded = self._trees.pop(run_id, None) or _Loaded(BabTree(), 0, False)
            if not loaded.sealed:
                try:
                    read = self.records.bab_log(run_id, loaded.offset, sealed)
                    if read is None:
                        return None
                    lines, loaded.offset = read
                    for line in lines:
                        loaded.tree.apply(line)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise AppError(409, "record_corrupt", f"BaB tree log could not be read: {exc}") from exc
                loaded.sealed = sealed
            self._trees[run_id] = loaded
            while len(self._trees) > CACHED_TREES:
                self._trees.popitem(last=False)
            return loaded.tree

    def tree(self, run_id: str, root: int = 0, limit: int = 2000) -> S.BabTreeOut:
        run = self.runs.get(run_id)
        recorded = run.method == "bab" and self._records_waves(run_id)
        tree = self._load(run_id) if recorded else None
        base = {"run_id": run_id, "status": run.status, "root": root, "limit": limit}
        if tree is None:
            if run.method != "bab":
                availability, reason = "unsupported", "Only BaB runs have a search tree."
            elif not recorded:
                availability, reason = "unsupported", observation_coverage(False)["reason"]
            elif run.status in ("queued", "running"):
                availability, reason = "pending", "Waiting for ACT's first committed BaB wave."
            else:
                availability, reason = "not_recorded", "The run ended before ACT reported a BaB wave."
            return S.BabTreeOut.model_validate({
                **base, "availability": availability, "reason": reason, "complete": False, "path": [], "nodes": [],
                "truncated": False, "counts": {}, "shares": None, "waves": [], "terminal": None})
        try:
            snapshot = tree.snapshot(root, limit)
        except KeyError as exc:
            raise AppError(404, "node_not_found", f"ACT reported no BaB node {root} in {run_id}") from exc
        end = tree.end or {}
        return S.BabTreeOut.model_validate({
            **base, **snapshot, "availability": "available", "reason": observation_coverage(True)["reason"],
            "complete": tree.terminal is not None, "waves": tree.waves, "terminal": tree.terminal,
            "ignored_records": end.get("ignored_records", 0), "recording_error": end.get("error")})

    def node(self, run_id: str, node_id: int) -> S.BabNodeDetailOut:
        run = self.runs.get(run_id)
        tree = self._load(run_id) if run.method == "bab" and self._records_waves(run_id) else None
        if tree is None or node_id not in tree.nodes:
            raise AppError(404, "node_not_found", f"ACT reported no BaB node {node_id} in {run_id}")
        return S.BabNodeDetailOut.model_validate({"run_id": run_id, **tree.detail(node_id)})
