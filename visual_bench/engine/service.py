"""ACT engine status and solver licenses (VER-05): the workbench side of engine_bridge.engine_session.

Every other service calls require_engine() before it asks the bridge to touch ACT.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import cached_property
from pathlib import Path

from engine_bridge.contracts import EngineInfo
from engine_bridge.engine_session import probe
from visual_bench.engine import schemas as S
from visual_bench.engine.solver_license import GurobiLicense
from visual_bench.errors import AppError


class EngineService:
    def __init__(self, expected_commit: str, secrets_root: Path) -> None:
        self.expected_commit = expected_commit
        self.gurobi = GurobiLicense(secrets_root)

    @cached_property
    def info(self) -> EngineInfo:
        return probe(self.expected_commit)

    def engine_out(self) -> S.EngineInfoOut:
        d = asdict(self.info)
        d["usable"] = self.info.usable
        return S.EngineInfoOut.model_validate(d)

    def require_engine(self) -> None:
        if not self.info.usable:
            first = next(d for d in self.info.diagnostics if d.severity == "error")
            raise AppError(503, first.code, first.message)
