# Verification Application

**Status:** first version: `service.py`, `worker.py`, `RunsPanel.tsx`, `EngineBadge.tsx` (VER-01/02; VER-03/04 partial: lifecycle SSE and idempotent start only); `solver_license.py`, `EngineView.tsx`, `GurobiLicensePanel.tsx` (apply a license from WLS credentials, pasted text, or a file, with Gurobi's verdict), and `GurobiBadge.tsx` (top-bar license state; opens the Engine tab) (VER-05); method `fuzz` and `FuzzView.tsx` (the Fuzzing tab) (VER-06). **Owner:** B; C owns run interaction; A reviews verdict semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Provide shared application query/command entry points for users and AI, and manage application run lifecycle.

| Subproblem | Responsibility |
| --- | --- |
| Reads and configuration | Model/spec read use cases, fixed configuration, and run creation. |
| Execution orchestration | Isolated worker lifecycle and task state; never execute a complete long verification inside an HTTP handler. |
| Commands | Capabilities, authorization scope, budgets, expected_revision, and idempotency; separate accepted/applied/rejected. |
| State projection | Update application state from committed engine events. Separate connectivity, lifecycle, and scientific verdict. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not choose branching algorithms, compute verdicts, import ACT directly, or maintain a second persistent event store.

## 3. Inputs, Outputs, and State

- **Inputs:** Run requests, precise queries, user/AI commands, real bridge results, and committed events.
- **Outputs:** run_id, state snapshots/projections, query results, execution receipts, and structured errors.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Application use cases and dependency injection.** FastAPI routes and AI tools call the same functions. Inject bridge and records interfaces.

**Explicit state machine and idempotent commands.** Make transitions testable. Retries return the existing result instead of applying an action twice.

**Separate queries and commands.** Read-only inspection and run mutations have different preconditions. A full CQRS platform is unnecessary.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Use bridge capabilities, reads, execution, inspection/events, and an injected records storage interface. Do not depend on graph features or assistant implementations.

Begin with use_cases.py and wire schemas. Keep HTTP composition in visual_bench/server.py; Python use cases do not depend on React.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| VER-01 | Implement description gateway and wire generation | MSB-03, BASE-02 | Applies the BASE-02 generation pipeline to real descriptions: real bridge data validates through Pydantic and generated browser types have no drift. |
| VER-02 | Implement isolated run lifecycle | VER-01, EXE-01, REC-01 | Start returns a run reference without waiting for completion; a deterministic sample matches native ACT; worker failure is visible. Method `interval` takes `domain` (`interval` default, `dual`, `hybridz`), recorded on the run; native references apply to the interval domain only. |
| VER-03 | Implement committed snapshots, SSE stream, and reconnect | VER-02, EVT-02, REC-02 | The service SSE route emits payloads that validate against the generated event schema; snapshot at S plus events after S reconstructs the same state; duplicates and gaps do not corrupt it. |
| VER-05 | Accept a user-supplied Gurobi license and hand it to run workers | ES-04 | `PUT/DELETE /api/solvers/gurobi/license` and `GET /api/solvers/gurobi`; only text shaped like a Gurobi license is stored (0600, under `ACT_GUI_SECRETS`, default `<records>/../secrets`), its content is never returned, an uploaded license overrides `GRB_LICENSE_FILE`, and each run manifest records the license source and requested device (`test_service.py`). |
| VER-06 | Run and demonstrate ACTFuzzer from the GUI | EXE-04, VER-02, REC-01 | `fuzz` is a run method for every catalog model, with `FuzzOptions` (max iterations, RNG seed, stop at first counterexample); options on another method are rejected. The worker streams progress as JSON lines over an inherited pipe; the supervisor commits each as a `fuzz.progress` event, so the Fuzzing tab follows the run live over SSE and a reconnect replays it. Mutated-input frames (lane 0 of ACT's mutated batch, sampled with the progress reports) arrive on the same pipe but are held in memory as the latest frame only, never committed as events; the Fuzzing tab shows that frame beside the coverage chart while running, and `fuzzing.json` keeps up to 16 frames as a playable filmstrip whose position is marked on the chart. The sealed `fuzzing.json` artifact holds ACT's summary, timeline, per-strategy counts, and the first 20 counterexamples (each with ACT's model output on its seed), plus the first 20 seed rows with their outputs; `GET /api/runs/{id}/fuzzing` serves it (`pending` with the live timeline while running). The view shows coverage and counterexamples over iterations, the seed inputs and their outputs, a gallery of mutated counterexamples (seed / mutated / perturbation; image thumbnails for 1- or 3-channel square inputs), expected vs argmax class for labelled properties, a seed-vs-mutated input and output comparison, and strategy shares. Records written before seed capture omit those parts. `test_service.py` covers the lifecycle and record. |
| VER-04 | Implement the shared command gateway | VER-03, EXE-03 | Same-ID retry cannot apply twice; changed parameters, stale revision, unsupported actions, and expired authority are rejected. |

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Retrying a command_id does not reapply it; the same ID with different parameters is rejected.
- Worker failure, timeout, and disconnection cannot become CERTIFIED.
- Stale revisions, unsupported capabilities, and exceeded budgets produce defined receipts.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Read engine data | A view or AI tool requests model/node/layer data. | Use one application query path with the same context and validation regardless of caller. |
| Start and observe a run | Submit fixed model/spec/config references. | Return run_id promptly; an isolated worker reports progress and final result without blocking service requests. |
| Apply a control | Submit a supported action with command_id and expected_revision. | Return accepted or rejected, then report actual applied/rejected outcome after ACT checks. |

### Processing Flow

1. Validate the wire request and map it to an application request.
2. Check identity, capability, authorization scope, budget, and idempotency where relevant.
3. Dispatch reads to the bridge or schedule an isolated worker for computation.
4. Persist committed results/events through records and update the run projection.
5. Return an immutable query result or expose snapshot/events/command receipts to clients.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `describeInputs(modelRef, specRef) → Descriptions` | Shared first-slice read use case. |
| `startRun(request, clientRequestId) → RunRef` | Duplicate creation requests return the same run; conflicting reused IDs are rejected. |
| `queryInspection(context, query) → InspectionResult` | Returns immediately available data or a distinct pending inspection reference. |
| `submitCommand(command) → CommandReceipt` | Checks expected_revision and idempotency; acceptance is not application. |
| `getSnapshot(runId) / subscribe(runId, afterSeq)` | Snapshot includes the exact covered sequence; unavailable replay windows require resynchronization. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `use_cases.py` | Shared application operations for routes and AI tools. |
| `schemas.py` | Pydantic wire source and exports for REST/event generation. |
| `worker.py` | Process entry and IPC messages; direct ACT calls remain in bridge. |
| `run_state.py` | Lifecycle and committed-state projection. |
| `client.ts` | Generated-client binding and snapshot/event consumption. |
| `test_use_cases.py` | Parity, retries, worker failures, and control preconditions. |

### State, Failure, and Recovery Rules

Define run lifecycle as queued/running/paused/completed/failed/cancelled and store ACT verdict separately. Reserve command identity before dispatch. If a crash leaves application uncertain, reconcile with ACT or mark outcome_unknown and block automatic replay; do not blindly resend a potentially applied action.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
