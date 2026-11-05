"""ACT engine status and solver license payloads (GET /api/engine, /api/solvers/gurobi)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from visual_bench.wire import Availability, Method, Wire

__all__ = ['ApiCheckOut', 'CapabilityOut', 'DiagnosticOut', 'EngineBranchesOut', 'EngineInfoOut', 'EngineRemoteOut', 'EngineSourceOut',
           'EngineSourcesOut', 'EngineSwitchRequest', 'SolverLicenseUpload', 'SolverStatusOut']


class CapabilityOut(Wire):
    name: str
    availability: Availability
    source: str

class ApiCheckOut(Wire):
    """One ACT symbol a capability's bridge adapter calls, checked on the active checkout."""
    capability: str
    symbol: str
    ok: bool
    detail: str

class DiagnosticOut(Wire):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str

class EngineSourceOut(Wire):
    """Where the imported ACT code comes from: the pinned baseline checkout or a staged branch head."""
    kind: Literal["baseline", "branch"]
    remote: str | None = None
    url: str | None = None
    branch: str | None = None
    commit: str | None = None
    switched_at: str | None = None

class EngineRemoteOut(Wire):
    name: str
    url: str
    custom: bool  # entered by a user (and remembered after it imported as ACT), not operator-configured

class EngineSourcesOut(Wire):
    active: EngineSourceOut
    remotes: list[EngineRemoteOut]
    custom_allowed: bool  # whether users may enter their own repository URL (ACT_GUI_ALLOW_CUSTOM_REMOTES)

class EngineBranchesOut(Wire):
    remote: str
    url: str
    branches: list[str]

class EngineSwitchRequest(Wire):
    """Neither remote nor url: the pinned baseline. Otherwise the branch head of a listed remote (by name)
    or of a user-entered https git URL."""
    remote: str | None = None
    url: str | None = Field(default=None, max_length=300)
    branch: str | None = Field(default=None, min_length=1, max_length=255)

class EngineInfoOut(Wire):
    act_root: str
    commit: str | None
    expected_commit: str | None
    tracked_changes: bool | None
    python: str
    torch: str | None
    cuda_available: bool | None
    usable: bool
    source: EngineSourceOut
    capabilities: list[CapabilityOut]
    diagnostics: list[DiagnosticOut]
    api_checks: list[ApiCheckOut]

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
