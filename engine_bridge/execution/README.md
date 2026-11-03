# Execution Adapter

**Status:** first version: `verify.py` (EXE-01 `verify_once` in the interval / dual / hybridz domain, + BaB), `fuzz.py` (EXE-04 ACTFuzzer); EXE-02/03 blocked on ACT-02/05. **Owner:** B; A owns ACT operation semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Faithfully invoke ACT verification and supported controls and report actual outcomes.

| Subproblem | Responsibility |
| --- | --- |
| Verification | Map fixed run configuration to supported ACT entry points. |
| Controls | Submit pause/step/split/cancel only when supported, with explicit safe-boundary semantics and granularity. |
| Results | Separate execution errors, timeouts, scientific verdicts, and command receipts; preserve counterexample provenance. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not implement search strategies, replace ACT validity checks, manage workbench run lists, or host HTTP services.

## 3. Inputs, Outputs, and State

- **Inputs:** Valid engine/model handles, run configuration, targets/revision preconditions, and stable command_id.
- **Outputs:** RunHandle, ACT results, actual applied/rejected receipts, and structured exceptions.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Command adapter.** Map application-validated commands into engine calls and recheck actual preconditions at the point of execution.

**Explicit handles and outcomes.** Return actual handles/state rather than assuming that a function return means verification has completed.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Uses engine_session/model_spec/contracts and ACT. The workbench owns the idempotency log; the adapter must not blindly retry an operation whose application is uncertain.

Support one verified execution mode first. Planned control methods must not be represented as existing ACT APIs.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| EXE-01 | Adapt a real verification entry point | MSB-03, ES-02 | A deterministic no-time-cutoff sample produces the same scientific result as native ACT under recorded tolerances. |
| EXE-02 | Define observable execution and run handles | EXE-01, ACT-02 | Handle lifecycle, inspection access, completion, and interruption semantics are agreed with A and exercised on ACT. |
| EXE-03 | Implement capability-gated safe controls | EXE-02, EVT-02, ACT-05 | Only ACT-implemented pause/step/split/cancel operations are enabled; stale targets and failed preconditions have actual rejection receipts. |
| EXE-04 | Adapt ACT's inference-based fuzzer | EXE-01 | `run_fuzzing` rebuilds the net with ACT's `ACTToTorch`, seeds ACTFuzzer with the net's INPUT rows, and reports ACT's `FuzzingReport`; counterexamples are only those ACT's PropertyChecker accepted. Verdict is `falsified` iff ACT reported a counterexample, otherwise `unknown` (fuzzing never certifies). Progress (iteration, coverage, counterexample count, corpus) is read between iterations. `test_bridge.py`: a counterexample on `unsafe_linear` lies inside the input box; 200 iterations on `bab_deep_mlp` (BaB-certified) report none. |

**EXE-01 domains.** `run_verification(..., method="interval", domain=...)` runs `verify_once` in one of ACT's abstract domains: `interval` (IntervalTF), `dual` (`set_solver_mode("dual")`, DualSolver), or `hybridz` (solver and TF mode `hybridz`, HybridzTF + HZSolver with the run budget as its MILP time limit). Selection mirrors `act/config/pipeline_cli.py` and always sets both ACT globals, so a previous run in the same process cannot leak. Layer inspection explicitly resets to the interval domain. BaB keeps its existing bounding path; domain selection for BaB is not exposed.

**EXE-04 notes.** Mutated-input frames (`FuzzFrame`, `on_frame`) come from a second instance seam: `fuzz.py` wraps the fuzzer's `mutation_engine.mutate`, keeps references to the latest seeds and mutated batch, and returns ACT's tensor unchanged; frames are display data, never a verdict. ACTFuzzer has no public progress hook in the baseline, so `fuzz.py` replaces the fuzzer instance's `_print_progress` (called after every iteration with `report_interval=1`); this private seam is recorded as the `fuzz.actfuzzer` capability source and must be rechecked when the pinned ACT commit changes. A public observer in ACTFuzzer would remove it. Seeds for `random`, NumPy, and torch are set from `rng_seed`; a time-bounded run still varies in iteration count. Mutation weights and other settings come from ACT's `act/config/pipeline.yaml`.

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Adapter and native ACT scientific results agree under documented tolerances.
- Unsupported controls, invalid nodes, and stale revisions are rejected with explanations.
- Cutoffs with unresolved domains or an empty frontier are not rewritten as CERTIFIED.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Verify a fixed input | The worker submits model/spec/config references. | Invoke ACT and return its verdict/counterexample/provenance without reinterpretation. |
| Expose a running computation | The application needs observation/inspection handles. | Bind a run handle to the actual execution and its safe observation boundaries. |
| Control supported work | Receive a versioned control command. | Apply only supported operations at ACT-safe points and report the real outcome. |

### Processing Flow

1. Resolve valid session/model/spec handles and validate configuration against capabilities.
2. Start ACT computation in the already-owned worker context.
3. Bind run identity to committed observation/inspection state; convert completion and failures.
4. For controls, recheck target/revision at the execution boundary, then return ACT applied/rejected evidence.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `verify(session, model, spec, config) → VerifyResult` | First supported mode may be blocking inside the worker; it must not block the HTTP server. |
| `startExecution(...) → RunHandle` | Proposed extension for observable execution; concrete semantics must be agreed with ACT. |
| `submitControl(runHandle, command) → ControlOutcome` | Requires engine capability and safe-boundary semantics; do not assume the API exists today. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `adapter.py` | Version-specific invocation and result conversion. |
| `controls.py` | Add only after supported control hooks exist. |
| `test_execution.py` | Native parity, verdict/error separation, and safe controls. |

### State, Failure, and Recovery Rules

For a command whose application is uncertain after transport failure, do not retry blindly. Return uncertainty for application-level reconciliation. A dropped domain, exhausted frontier, or local solver SAT status must not be transformed into a new global verdict by the adapter.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
