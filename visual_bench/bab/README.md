# BaB Explorer

**Status:** not started beyond `BabView.tsx`, which shows observation coverage and ACT's final BaB summary; BAB-01..03 need committed node events (ACT-03). **Owner:** C; D may support rendering; A reviews search semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).


## Current Files and Usage

| File | Layer | Responsibility |
| --- | --- | --- |
| `schemas.py` | Wire | `CoverageOut`. |
| `service.py` | Service | `BabService.coverage(run_id)`: observation coverage from `engine_bridge.events` plus ACT's final BaB summary when recorded. |
| `routes.py` | HTTP | `GET /api/runs/{id}/coverage`. |
| `api.ts`, `hooks.ts` | Browser data | Coverage query keyed under the run (`keys.coverage`). |
| `BabView.tsx` | View | Coverage and final summary (BaB mode). |

Tests: covered through `../verification/test_verification.py` (`bab.summary` event) and `../assistant/test_assistant.py` (coverage evidence).

## 1. Subproblems and Objective

Expose search structure, selected paths, node state, and branching rationale.

| Subproblem | Responsibility |
| --- | --- |
| Scale | Global summaries, selected paths, local subtrees, paging, and aggregation instead of rendering every node by default. |
| Relationships | Distinguish split edges from merge/reuse provenance; not every relationship is a single-parent tree edge. |
| Inspection and actions | Node details, bound provenance, and branching rationale; delegate actions to verification. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not mutate the ACT frontier, prune search through graph-node deletion, or infer success from an empty frontier.

## 3. Inputs, Outputs, and State

- **Inputs:** run/revision, node summaries, relationships, recording coverage, and selected node.
- **Outputs:** Local search views, details, workspace selections, and requests through the shared command entry point.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Read-only state projection.** Derive display models from committed snapshots/events; local graph state contains layout and expansion only.

**Renderer adapter.** React Flow/ELK are candidates. Encapsulate the mapping between engine node identity and renderer identity.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

verification supplies queries/event projections; workspace owns selection. Coordinate with analysis through public interfaces rather than internal state.

Start with a graph view model and one panel. Never write layout coordinates back into engine state.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| BAB-01 | Show committed node table and selected path | VER-03, WS-02 | A recorded real run has matching IDs/status/bound origins in table and detail. |
| BAB-02 | Add bounded local graph navigation | BAB-01, PERF-01 | Expand/page a subtree while preserving selected path and positions; large fixtures stay within a measured view budget. |
| BAB-03 | Add supported node actions | BAB-02, VER-04 | An action creates one shared command and shows accepted/applied/rejected independently of graph appearance. |

Owner: **C**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Node identity survives batch-lane reordering.
- Computed and inherited bounds have distinguishable provenance.
- Retries/rollback do not leave ghost nodes; exceeding the view budget triggers aggregation rather than a frozen page.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Browse search | Open a run and select a node or path. | Show aggregate progress, a local subtree, and node details under a fixed revision. |
| Expand detail | Expand another subtree or inspect provenance. | Page data within a view budget; distinguish split edges from merge/reuse links. |
| Request a branch action | Choose an available control from node detail. | Route to the shared command gateway and show actual receipt; renderer edits never mutate the search directly. |

### Processing Flow

1. Fetch a revision-bound node page/path and subscribe to committed updates.
2. Normalize by logical node_id and derive a local graph view model.
3. Apply layout without changing domain identities; store expansion/position separately.
4. Publish node selection to workspace; request operations through verification.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `buildLocalGraph(nodes, relations, selection, budget) → GraphViewModel` | Pure projection; preserve relation kinds. |
| `getNodePage(runId, revision, cursor, filters) → NodePage` | Application query backed by recorded committed state or ACT inspection. |
| `requestNodeAction(nodeRef, action) → CommandReceipt` | Delegates to verification with current capability and revision preconditions. |

### Planned Files (design targets)

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `BabView.tsx` | Overview, graph, node detail, and action controls. |
| `graph_model.ts` | Identity-preserving local graph projection. |
| `layout_adapter.ts` | Candidate React Flow/ELK integration. |
| `bab.test.tsx` | Selection, pagination, provenance, and capability feedback. |

### State, Failure, and Recovery Rules

When full provenance is unavailable, show supported summaries and the coverage limitation. Do not synthesize missing parents or infer a verdict from visible-node counts.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
