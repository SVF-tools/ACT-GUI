# Verification Application

**Status:** first version: run lifecycle service and worker (VER-01/02; VER-03/04 partial: lifecycle SSE and idempotent start only), run stop and the ACT verdict banner (VER-07). Engine status and the Gurobi license moved to [engine](../engine/README.md) (VER-05) and ACTFuzzer views and saved counterexamples to [fuzzing](../fuzzing/README.md) (VER-06, VER-07 saving) on 2026-11-04. **Owner:** B; C owns run interaction; A reviews verdict semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).


## Current Files and Usage

| File | Layer | Responsibility |
| --- | --- | --- |
| `schemas.py` | Wire | `RunRequest`, `RunOut`, `RunResultOut`, `RunList`, `RunEvent` (SSE payload). |
| `service.py` | Service | `RunService`: `start` (validation, idempotency, manifest, supervisor thread), `stop`, `get`, `list`, `request`. Method-neutral: live worker output goes to an injected `LiveObserver` (fuzzing's `FuzzLive`). |
| `worker.py` | Worker | `python -m visual_bench.verification.worker <request> <output> <progress_fd>`: runs `run_verification` or `fuzzing.runner`, records interval layer states, writes the result file. ACT calls go through engine_bridge only. |
| `routes.py` | HTTP | `POST/GET /api/runs`, `GET /api/runs/{id}`, `POST /api/runs/{id}/stop`, `GET /api/runs/{id}/events` (SSE replay + follow). |
| `api.ts`, `hooks.ts` | Browser data | Run list/run queries, start/stop mutations, SSE following that invalidates the run's queries on each committed event. |
| `RunsPanel.tsx`, `RunHistory.tsx`, `VerdictBanner.tsx`, `labels.ts` | Views | Run settings and start button beside the network, run history in the right column, ACT verdict banner for Verification/BaB modes, method labels. |
| `test_verification.py` | Tests | BaB lifecycle vs. native, falsified run, stop without verdict, domains, idempotency, invalid requests, tampered and torn records. |

Run this module's tests: `.venv/bin/python -m pytest visual_bench/verification`.

Dependencies: model_spec (`ModelService`: entry, methods, pinned path, native reference), engine (engine gate, commit, worker license env), records, and an injected `LiveObserver`. fuzzing, analysis, bab, and assistant read runs through `RunService`.

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

Use cases live in `service.py`, HTTP mapping in `routes.py`, and `server.py` only includes the router; Python use cases do not depend on React or FastAPI. Add code and focused tests in this module as implementation proceeds.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| VER-01 | Implement description gateway and wire generation | MSB-03, BASE-02 | Applies the BASE-02 generation pipeline to real descriptions: real bridge data validates through Pydantic and generated browser types have no drift. |
| VER-02 | Implement isolated run lifecycle | VER-01, EXE-01, REC-01 | Start returns a run reference without waiting for completion; a deterministic sample matches native ACT; worker failure is visible. Method `interval` takes `domain` (`interval` default, `dual`, `hybridz`), recorded on the run; native references apply to the interval domain only. |
| VER-03 | Implement committed snapshots, SSE stream, and reconnect | VER-02, EVT-02, REC-02 | The service SSE route emits payloads that validate against the generated event schema; snapshot at S plus events after S reconstructs the same state; duplicates and gaps do not corrupt it. |
| VER-05 | Accept a user-supplied Gurobi license and hand it to run workers | ES-04 | Moved to [engine](../engine/README.md#3-tasks). Run manifests still record the license source and requested device (`service.py`). |
| VER-06 | Run and demonstrate ACTFuzzer from the GUI | EXE-04, VER-02, REC-01 | Moved to [fuzzing](../fuzzing/README.md#3-tasks); this module runs fuzz like any other method (worker, progress pipe, `fuzz.progress` events, SSE). |
| VER-07 | Stop runs and show the ACT verdict (saving/export of fuzz counterexamples: [fuzzing](../fuzzing/README.md#3-tasks)) | VER-06 | `POST /api/runs/{id}/stop` is idempotent and commits `run.stop_requested`: a fuzz worker gets SIGTERM and ACTFuzzer ends after its current iteration with ACT's report (`summary.stopped`); verify/BaB workers are killed and the run fails with `stopped` (no verdict); a worker that ignores the stop for `STOP_GRACE_S` is killed. `VerdictBanner.tsx` shows ACT's verdict with the native reference for Verification and BaB runs. Evidence: `test_verification.py::test_stop_ends_a_verification_worker_without_a_verdict`, `../fuzzing/test_fuzzing.py::test_stop_ends_fuzz_run_with_act_report_of_iterations_run`. |
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

### Planned Files (design targets)

Implemented equivalents: `use_cases.py` → `service.py`; `schemas.py` and `worker.py` exist; `client.ts` → `api.ts` + `hooks.ts`; `test_use_cases.py` → `test_verification.py`. Still planned:

| File | Responsibility |
| --- | --- |
| `run_state.py` | Lifecycle and committed-state projection once committed scientific events exist (VER-03). |
| `commands.py` | Shared command gateway with expected_revision and receipts (VER-04). |

### State, Failure, and Recovery Rules

Define run lifecycle as queued/running/paused/completed/failed/cancelled and store ACT verdict separately. Reserve command identity before dispatch. If a crash leaves application uncertain, reconcile with ACT or mark outcome_unknown and block automatic replay; do not blindly resend a potentially applied action.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
