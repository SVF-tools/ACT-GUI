# Engine Session

**Status:** first version: `session.py` (ES-01 probe, diagnostics, capabilities; ES-04 Gurobi license probe); ES-02 handles and ES-03 not started. **Owner:** B; A reviews environment and capability semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).


## Current Files and Usage

| File | Responsibility |
| --- | --- |
| `session.py` | `act_root()`, `act_imports()` (makes the pinned ACT importable or raises `act_missing`), `probe(expected_commit)` → `EngineInfo` with capabilities and diagnostics, `probe_gurobi(license_file)` → `SolverStatus`. |
| `__init__.py` | Public API: `act_imports`, `act_root`, `probe`, `probe_gurobi`. |
| `test_engine_session.py` | Probe against the pinned commit, missing ACT, version mismatch, Gurobi license rejection. |

Used by: every other bridge module (`act_imports`), `visual_bench/engine` (status, license check). Tests: `.venv/bin/python -m pytest engine_bridge/engine_session`.

## 1. Subproblems and Objective

Establish an ACT integration context with explicit versions/capabilities and manage engine resource handles.

| Subproblem | Responsibility |
| --- | --- |
| Version | Inspect the actual ACT commit/API and dependencies instead of inferring capabilities from GUI versions. |
| Capabilities | Describe supported model/specification/inspection/operation scopes and limitations. |
| Resources | Acquire/release handles and prevent cross-process misuse or access after release. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not manage user sessions, Web connections, worker startup/restart policy, or task queues.

## 3. Inputs, Outputs, and State

- **Inputs:** Pinned dependency configuration, required capabilities, and actual execution environment.
- **Outputs:** EngineInfo, Capabilities, SessionHandle, and structured unavailability diagnostics.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Session facade and explicit resource lifecycle.** Use one integration entry point for capabilities and handles; avoid an implicit global ACT singleton.

**Capability discovery.** Select behavior from actual capability information instead of spreading version branches throughout the workbench.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Depends only on ACT/environment and integration contracts. Workbench workers create/use sessions; no callbacks into workbench logic are required.

Start with one session adapter, not a multi-engine provider registry.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| ES-01 | Implement version/capability probe | BASE-01 | Against the pinned baseline, every advertised capability has a known support source or verified sample; missing ACT and version mismatch produce deterministic diagnostics. |
| ES-02 | Implement explicit resource handles | ES-01 | Open/use/close has a defined lifecycle; crossing a process boundary does not transfer native solver/GPU objects. |
| ES-04 | Probe optional solver licenses (Gurobi) | ES-01 | `probe_gurobi(license_file)` starts a Gurobi environment in a fresh process and returns Gurobi's own verdict as licensed, restricted, invalid, or not_installed, without credential values; a host-bound license for another host reports invalid with Gurobi's HostID message (`test_engine_session.py`). |
| ES-03 | Validate cleanup and compatibility regression | ES-02 | Repeated close and post-close access produce deterministic diagnostics with no leaked resources; ES-01 incompatibility diagnostics hold across every declared engine combination. |

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Missing ACT or an incompatible version produces structured diagnostics.
- Unsupported capabilities never default to true.
- Repeated release and use of invalid handles have defined behavior without resource leaks.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Probe ACT | Start the workbench service/worker. | Report the actual ACT version/environment and supported capabilities without importing GUI code. |
| Bind engine resources | A worker opens a session for supported work. | Return a process-local handle with explicit ownership and release semantics. |
| Reject incompatible use | An operation requires an unavailable method or uses a closed handle. | Return a structured reason; never optimistically advertise the capability. |

### Processing Flow

1. Read configured ACT baseline and inspect installed engine metadata/capabilities.
2. Validate the requested capability set and resource prerequisites.
3. Create a session inside its owning execution process; expose only neutral diagnostics outside it.
4. Release resources deterministically and invalidate dependent handles.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `probeEngine(config) → EngineInfo + Capabilities` | Non-computational compatibility probe; record unknown/unsupported explicitly. |
| `openSession(config) → SessionHandle` | Handle has an owning process/session identity; it is not a browser DTO. |
| `closeSession(handle) → CloseResult` | Idempotent close; subsequent operations receive invalid_handle. |

### Planned Files (design targets)

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `adapter.py` | ACT metadata, binding, capability mapping, and cleanup. |
| `test_session.py` | Missing/incompatible engine and handle lifecycle. |

### State, Failure, and Recovery Rules

Do not manage worker scheduling or user run lists here. A supported GUI platform does not imply this engine environment is supported; report engine compatibility independently.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
