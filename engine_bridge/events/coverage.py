"""ACT observation coverage for the pinned baseline (EVT-01, first version).

The baseline exposes no BaB observer, so node-level committed events are
unsupported. The only BaB observation is the final summary ACT puts in
VerifyResult.metadata; it is labeled summary-only and never expanded into nodes.
"""
from __future__ import annotations

from typing import Mapping

BAB_SUMMARY_KEYS = (
    "nodes", "pool_remaining", "nodes_minted", "exhausted_budget_time", "exhausted_budget_nodes",
    "any_dropped_frontier_cap", "reason", "budget_exhausted_in", "multi_split_wave_count",
)


def observation_coverage() -> dict[str, str]:
    return {
        "node_events": "unsupported",
        "wave_events": "unsupported",
        "final_summary": "available",
        "reason": "ACT baseline has no BaB observer/commit hook (plan ACT-03); only post-run metadata is observable.",
    }


def bab_summary(metadata: Mapping[str, object]) -> dict[str, object]:
    return {k: metadata[k] for k in BAB_SUMMARY_KEYS if k in metadata}
