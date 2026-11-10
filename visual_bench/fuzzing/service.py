"""ACTFuzzer run records (VER-06/07): fuzzing views of runs, saved counterexamples, and their VNN-LIB export.

The fuzz run itself goes through the verification run lifecycle; this module reads its record
(fuzzing.json, fuzz.progress events) and the live state FuzzLive keeps while it runs.
"""
from __future__ import annotations

import math
import threading
from dataclasses import asdict
from typing import Any

from engine_bridge.contracts import BridgeError
from engine_bridge.execution import FUZZ_PROVENANCE, FuzzRunControl, fuzzing_options
from visual_bench.errors import AppError
from visual_bench.fuzzing import schemas as S
from visual_bench.fuzzing.live import FuzzLive
from visual_bench.model_spec.service import ModelService
from visual_bench.records import RecordStore
from visual_bench.records.store import now_iso
from visual_bench.verification.service import SAVED, RunService, vnncomp_sat
from visual_bench.wire import display_numbers, wire_number, wire_numbers


class FuzzingService:
    def __init__(self, runs: RunService, records: RecordStore, models: ModelService, live: FuzzLive) -> None:
        self.runs = runs
        self.records = records
        self.models = models
        self.live = live
        self._lock = threading.Lock()

    @staticmethod
    def defaults() -> S.FuzzOptions:
        return S.FuzzOptions()

    def options(self) -> S.FuzzOptionsSchemaOut:
        self.runs.engine.require_engine()
        return S.FuzzOptionsSchemaOut(
            options=[S.FuzzOptionOut.model_validate(asdict(o)) for o in fuzzing_options()],
            live_control=self.runs.engine.capability_available("fuzz.control"))

    def control(self, run_id: str, req: S.FuzzControlRequest) -> S.FuzzControlOut:
        """Queue one command per request ID. A retry returns the first receipt, including after completion."""
        with self._lock:
            run = self.runs.get(run_id)
            receipts = self.records.annotation(run_id, "fuzz_control_requests.json") or []
            prior = next((r for r in receipts if r["request_id"] == req.request_id), None)
            if prior is not None:
                return S.FuzzControlOut.model_validate({**prior, "status": "duplicate"})
            if run.method != "fuzz" or run.status != "running":
                raise AppError(409, "run_not_running", "Live fuzz control requires a running fuzz worker.")
            if req.action != "stop" and not self.runs.engine.capability_available("fuzz.control"):
                raise AppError(409, "capability_unavailable", "The active ACT checkout does not support fuzz.control.")
            changes = req.changes
            if req.action == "update":
                if not changes:
                    raise AppError(422, "invalid_options", "An update requires at least one live option.")
                try:
                    changes = FuzzRunControl().update(changes)
                except BridgeError as exc:
                    raise AppError(422 if exc.code == "invalid_options" else 409, exc.code, exc.message) from exc
            self.runs.send_fuzz_control(run_id, req.action, changes)
            receipt = S.FuzzControlOut(run_id=run_id, action=req.action, request_id=req.request_id,
                                      status="queued", changes=changes)
            self.records.write_annotation(run_id, "fuzz_control_requests.json", [*receipts, receipt.model_dump()])
            return receipt

    def _control_state(self, run_id: str) -> S.FuzzControlStateOut | None:
        initial = self.records.manifest(run_id).get("execution", {}).get("fuzz_live")
        if initial is None:
            return None
        state = S.FuzzControlStateOut(paused=False, live=dict(initial), changes=[])
        for event in self.records.events(run_id):
            if event["kind"] == "fuzz.control":
                change = S.FuzzConfigChangeOut.model_validate(event["payload"])
                state.changes.append(change)
                state.live.update(change.applied)
            elif event["kind"] in ("fuzz.paused", "fuzz.resumed"):
                state.paused = event["payload"]["paused"]
            elif event["kind"] in ("run.completed", "run.failed"):
                state.paused = False
        return state

    def fuzzing(self, run_id: str) -> S.FuzzingOut:
        run = self.runs.get(run_id)
        base: dict[str, Any] = {"run_id": run_id, "status": run.status, "options": self.runs.request(run_id).fuzz,
                                "config": {}, "provenance": dict(FUZZ_PROVENANCE)}
        if run.method != "fuzz":
            return S.FuzzingOut(availability="unsupported", summary=None, timeline=[], strategies=[],
                                counterexamples=[], **base)
        base["control"] = self._control_state(run_id)
        raw = self.records.artifact(run_id, "fuzzing.json") if run.status == "completed" else None
        base["saved"] = [S.SavedCounterexampleOut(saved_at=e["saved_at"], counterexample=counterexample_out(e["counterexample"]))
                         for e in self.records.annotation(run_id, SAVED) or []]
        if raw is None:
            live = [S.FuzzPointOut.model_validate(e["payload"]) for e in self.records.events(run_id)
                    if e["kind"] == "fuzz.progress"]
            latest, hits = self.live.snapshot(run_id)
            # While running, counterexamples are the ones ACT reported in violating frames so far.
            return S.FuzzingOut(availability="pending" if run.status in ("queued", "running") else "not_recorded",
                                summary=None, timeline=live, strategies=[],
                                counterexamples=[counterexample_out(c) for c in hits],
                                frames=[frame_out(latest)] if latest else [], **base)
        seeds = [S.FuzzSeedOut(row=s["row"], input=display_numbers(s["input"]), output=wire_numbers(s["output"]))
                 for s in raw.get("seeds", [])]
        summary = S.FuzzSummaryOut.model_validate({k: raw[k] for k in S.FuzzSummaryOut.model_fields if k in raw})
        base["config"] = raw["config"]
        return S.FuzzingOut(availability="available", summary=summary,
                            timeline=[S.FuzzPointOut.model_validate(p) for p in raw["timeline"]],
                            strategies=[S.FuzzStrategyOut.model_validate(s) for s in raw["strategies"]],
                            counterexamples=[counterexample_out(c) for c in raw["counterexamples"]], seeds=seeds,
                            frames=[frame_out(fr) for fr in raw.get("frames", [])], **base)

    # -- saved counterexamples (user annotations on a fuzz run) ---------------
    def _find_counterexample(self, run_id: str, index: int) -> dict[str, Any] | None:
        raw = self.records.artifact(run_id, "fuzzing.json")
        if raw is not None:
            found = [c for c in raw["counterexamples"] if c["index"] == index]
            found += [f["counterexample"] for f in raw.get("frames", [])
                      if f.get("counterexample") and f["counterexample"]["index"] == index]
            return found[0] if found else None
        return self.live.hit(run_id, index)

    def save_counterexample(self, run_id: str, index: int) -> tuple[S.SavedCounterexampleOut, bool]:
        """Save ACT's counterexample #index on the run record; saving it again returns the saved entry."""
        if self.runs.get(run_id).method != "fuzz":
            raise AppError(422, "unsupported_method", "Only fuzz runs record counterexamples to save.")
        with self._lock:
            saved = self.records.annotation(run_id, SAVED) or []
            entry: dict[str, Any] | None = next((e for e in saved if e["counterexample"]["index"] == index), None)
            created = entry is None
            if entry is None:
                ce = self._find_counterexample(run_id, index)
                if ce is None:
                    raise AppError(404, "counterexample_not_found",
                                   f"ACT reported no counterexample #{index} in this run's record or live state")
                entry = {"saved_at": now_iso(), "counterexample": ce}
                self.records.write_annotation(run_id, SAVED, [*saved, entry])
        return S.SavedCounterexampleOut(saved_at=entry["saved_at"], counterexample=counterexample_out(entry["counterexample"])), created

    def saved_assignment(self, run_id: str, index: int) -> str:
        """A saved counterexample as a VNN-COMP result (verification.service.vnncomp_sat)."""
        run = self.runs.get(run_id)
        saved = self.records.annotation(run_id, SAVED) or []
        entry = next((e for e in saved if e["counterexample"]["index"] == index), None)
        if entry is None:
            raise AppError(404, "counterexample_not_saved", f"Counterexample #{index} is not saved on {run_id}")
        x, y = entry["counterexample"]["input"], entry["counterexample"]["output"]
        specs = self.models.describe(run.model_id).input_specs
        shape = specs[0].shape if specs and math.prod(specs[0].shape) == len(x) else [1, len(x)]
        return vnncomp_sat(x, y, shape)


def counterexample_out(c: dict[str, Any]) -> S.FuzzCounterexampleOut:
    return S.FuzzCounterexampleOut(**{**c, "severity": wire_number(c["severity"]), "input": display_numbers(c["input"]),
                                      "output": wire_numbers(c["output"]), "seed_input": display_numbers(c["seed_input"]),
                                      "seed_output": None if c.get("seed_output") is None else
                                      wire_numbers(c["seed_output"])})


def frame_out(fr: dict[str, Any]) -> S.FuzzFrameOut:
    ce = fr.get("counterexample")
    return S.FuzzFrameOut.model_validate({**fr, "input": display_numbers(fr["input"]),
                                          "seed_input": display_numbers(fr["seed_input"]),
                                          "counterexample": counterexample_out(ce) if ce else None})
