"""ACT engine status and solver license payloads (GET /api/engine, /api/solvers/gurobi)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from visual_bench.wire import Availability, Method, Wire

__all__ = ['CapabilityOut', 'DiagnosticOut', 'EngineInfoOut', 'SolverLicenseUpload', 'SolverStatusOut']


class CapabilityOut(Wire):
    name: str
    availability: Availability
    source: str

class DiagnosticOut(Wire):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str

class EngineInfoOut(Wire):
    act_root: str
    commit: str | None
    expected_commit: str | None
    tracked_changes: bool | None
    python: str
    torch: str | None
    cuda_available: bool | None
    usable: bool
    capabilities: list[CapabilityOut]
    diagnostics: list[DiagnosticOut]

class SolverLicenseUpload(Wire):
    """Text of a solver license file (e.g. gurobi.lic). Stored server-side; never returned."""
    content: str = Field(min_length=1, max_length=16384)

class SolverStatusOut(Wire):
    solver: Literal["gurobi"]
    version: str | None
    license_source: Literal["uploaded", "environment", "none"]
    license_fingerprint: str | None  # first 12 hex digits of the license file's sha256
    license_updated_at: str | None
    license_state: Literal["licensed", "restricted", "invalid", "not_installed"]
    message: str
    used_by_methods: list[Method]  # workbench methods whose ACT path calls this solver
