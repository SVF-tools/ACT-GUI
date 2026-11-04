"""BaB observation coverage of a run (BAB-01): what ACT exposes about the search, and the final summary if recorded."""
from __future__ import annotations

from engine_bridge.events import observation_coverage
from visual_bench.bab import schemas as S
from visual_bench.verification.service import RunService


class BabService:
    def __init__(self, runs: RunService) -> None:
        self.runs = runs

    def coverage(self, run_id: str) -> S.CoverageOut:
        run = self.runs.get(run_id)
        cov = observation_coverage()
        summary = run.result.bab_summary if run.result else None
        return S.CoverageOut(run_id=run_id, node_events=cov["node_events"], wave_events=cov["wave_events"],
                             final_summary="available" if summary is not None else
                             ("pending" if run.status in ("queued", "running") else "not_recorded"),
                             reason=cov["reason"], summary=summary)
