"""ACT BaB observation coverage (EVT-01) and the final summary filter.

ACT checkouts with act.pipeline.gui.bab_gui (capability events.bab_nodes) report every committed BaB wave; older
ones, including the pinned baseline, only put a final summary in VerifyResult.metadata. The summary is labeled
summary-only and never expanded into nodes.
"""
from __future__ import annotations

from typing import Mapping

BAB_SUMMARY_KEYS = (
    "nodes", "pool_remaining", "nodes_minted", "exhausted_budget_time", "exhausted_budget_nodes",
    "any_dropped_frontier_cap", "reason", "budget_exhausted_in", "multi_split_wave_count",
)


def observation_coverage(waves: bool) -> dict[str, str]:
    """Coverage of a BaB run whose ACT checkout did (waves) or did not report committed waves."""
    if waves:
        return {
            "node_events": "available",
            "wave_events": "available",
            "final_summary": "available",
            "reason": "ACT reports every committed BaB wave (solved nodes, queued children, frontier) and the end of "
                      "the search (act.pipeline.gui.bab_gui).",
        }
    return {
        "node_events": "unsupported",
        "wave_events": "unsupported",
        "final_summary": "available",
        "reason": "This ACT checkout reports no BaB waves (act.pipeline.gui.bab_gui, events.bab_nodes); only post-run "
                  "metadata is observable.",
    }


def bab_summary(metadata: Mapping[str, object]) -> dict[str, object]:
    return {k: metadata[k] for k in BAB_SUMMARY_KEYS if k in metadata}
