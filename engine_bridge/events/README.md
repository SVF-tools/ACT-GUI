# Committed Events Adapter

**Status:** first version: `coverage.py` (EVT-01 audit: final summary only); EVT-02/03 blocked on ACT-03. **Owner:** A; B integrates workbench mappings and reviews contract consistency.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).


## Current Files and Usage

| File | Responsibility |
| --- | --- |
| `coverage.py` | `observation_coverage()` (what the pinned ACT lets the GUI observe of BaB) and `bab_summary(metadata)` (final-summary keys only). |
| `__init__.py` | Public API: `observation_coverage`, `bab_summary`, `BAB_SUMMARY_KEYS`. |

Used by: the run worker (BaB summary) and `visual_bench/bab` (coverage). No dedicated tests yet: the BaB summary path is exercised by `visual_bench/verification/test_verification.py`.

## 1. Subproblems and Objective

Provide ACT committed events with identity, ordering, and coverage for observation and recording.

| Subproblem | Responsibility |
| --- | --- |
| Commit boundaries | Publish only after actual commit; temporary state before OOM retry/rollback must not become visible. |
| Identity and order | Preserve run/node/revision, per-run sequence, and batch changes; lane indices are not node IDs. |
| Coverage and backpressure | Distinguish wave summaries from full node events; report overflow or loss explicitly. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not host SSE, persist an event log, make search decisions, or fabricate unobserved node history.

## 3. Inputs, Outputs, and State

- **Inputs:** Committed ACT observer output, RunHandle, and observation configuration.
- **Outputs:** Normalized events/batches, per-run sequence, coverage, gaps, and terminal states.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Observer adapter.** Translate ACT observations into neutral events without changing search semantics.

**Bounded producer-consumer flow.** Bound queues and handle cancellation/release; report gaps instead of silently discarding state.

**Commit batches.** Identify all changes in a wave; consumers advance the visible revision only after complete application.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Uses contracts and ACT commit interfaces with execution-created run context. If ACT has no sequence, assign it at the commit boundary with one explicitly designated sequence owner.

Start with one observation adapter without introducing message middleware. Validate capability and coverage claims experimentally.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| EVT-01 | Audit and expose actual ACT observation coverage | EXE-02 | Record concrete hooks/commit points and limitations; summary-only data is labeled summary-only. |
| EVT-02 | Implement committed node/event batches | EVT-01, ACT-03 | With ACT-03 in the pinned baseline, rollback/retry leaves no ghost nodes; batch identity, seq, revision, and snapshot boundary agree. |
| EVT-03 | Validate backpressure and observation overhead | EVT-02, PERF-01 | A burst either preserves complete committed data or reports an explicit gap/degradation; deterministic scientific outcomes match observer-off execution. |

Owner: **A**. B reviews integration and contract consistency; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Failed attempts and retries do not create ghost nodes or duplicate commits.
- Order by sequence rather than timestamp; batch and snapshot coverage boundaries agree.
- Observation does not change deterministic-sample scientific outcomes, and overflow reports a gap/degraded recording.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Observe committed progress | Subscribe while a run executes. | Emit honest wave summaries first, identifying what detail is and is not available. |
| Observe node changes | ACT supplies stable identities and commit hooks. | Emit complete committed batches of creation/update/resolution events without ghost state. |
| Handle pressure and reconnect handoff | Consumer slows or observation stops. | Bound queues, report loss/coverage, and expose a sequence/checkpoint boundary for workbench persistence. |

### Processing Flow

1. Attach to verified ACT commit hooks using the execution run identity.
2. Collect a wave’s changes without publishing transient retry state.
3. Assign or preserve one per-run sequence and publish a complete batch with coverage.
4. On overflow/cancellation, report a defined terminal/gap state and detach resources; the workbench owns replay/SSE.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `observe(runHandle, config) → CommittedEventIterator` | Iterator yields normalized committed events/batches; coverage declares summary-only versus node-level information. |
| `getCommittedPosition(runHandle) → CommitPosition` | Position must agree with the corresponding snapshot boundary, not merely the latest observed timestamp. |
| `stopObservation(subscription) → ObservationStatus` | Releases observer resources without silently cancelling the ACT run. |

### Planned Files (design targets)

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `adapter.py` | Commit hooks, identity/sequence normalization, and coverage. |
| `buffer.py` | Bounded queue and batch assembly only as required. |
| `test_events.py` | Rollback, batch completeness, identity, overflow, and observer parity. |

### State, Failure, and Recovery Rules

Do not emit a new global sequence from both ACT and bridge. Choose one owner at the integration boundary. If ACT cannot provide an atomic snapshot/commit relationship, document and fix that engine capability before promising exact reconnect/replay.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
