"""BaB observation coverage payloads (/api/runs/{id}/coverage)."""
from __future__ import annotations

__all__ = ['CoverageOut']


from visual_bench.wire import Scalar, Availability, Wire


class CoverageOut(Wire):
    run_id: str
    node_events: Availability
    wave_events: Availability
    final_summary: Availability
    reason: str
    summary: dict[str, Scalar] | None
