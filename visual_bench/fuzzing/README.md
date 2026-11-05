# Fuzzing

**Current responsibility and status.** This module presents ACTFuzzer as the `fuzz` method of the shared run lifecycle. It owns fuzz options, live progress projection, recorded fuzz artifacts, saved counterexamples, and VNN-LIB export. The first version is implemented. B owns the service path, C owns the Fuzzing mode, and A reviews violation semantics.

This module does not start or stop runs itself, decide whether a property is violated, or import ACT. ACT decides the counterexample and verdict. The shared run lifecycle is [verification](../verification/README.md), and ACT adaptation is [engine_bridge/execution](../../engine_bridge/execution/README.md). See the [parent flow diagram](../README.md#flow-diagram) and [project development entry point](../../README.md#choose-a-development-task).

## Change Guide

| Goal | Required edits | Conditional edits / reused path |
| --- | --- | --- |
| Expose another ACT FuzzingConfig parameter | [schemas.py](schemas.py), [FuzzSettings.tsx](FuzzSettings.tsx), bridge [fuzz.py](../../engine_bridge/execution/fuzz.py) TUNABLE, parameter/default tests; regenerate wire.ts | [runner.py](runner.py) and split_options already forward ordinary hyperparameters. Change them only for a separate run argument or changed ACT calling convention. verification forwards nested FuzzOptions unchanged. |
| Change a control label or image layout | Owning FuzzSettings/Fuzz* view or [presentation.ts](presentation.ts) | No schema, worker, storage or bridge edit when the data is unchanged. |
| Add a new live metric from ACT | Bridge observation and neutral contract, [schemas.py](schemas.py), [service.py](service.py), view and relevant tests | Inspect [runner.py](runner.py) and [live.py](live.py): dataclass serialization and progress forwarding are generic. Change them only for new message/state semantics. SSE already invalidates run queries. |
| Add a field to recorded fuzz output | Bridge result if absent, [service.py](service.py)/[schemas.py](schemas.py) mapping, consuming view and tests | runner.py uses dataclasses.asdict; verification writes fuzzing.json generically. Existing storage/export usually need no change. |
| Change saved counterexample meaning or assignment export | [service.py](service.py), related tests | [routes.py](routes.py), API/hooks/views only when URL, payload or interaction changes. PNG rendering is browser-owned. |
| Change shared start/stop or lifecycle | [verification](../verification/README.md#change-guide) | runner.py only for fuzz-specific execution/stop semantics. |

After schema changes run `npm run gen:types`. A path appearing below does not make every file on it a required edit.

## Flow Diagram

Arrows are labeled as calls, results, or events. Neighboring modules are named explicitly and linked in the block tables. HTTP transport may be grouped; views use hooks or props, never direct fetch calls.

### Configure and start

```mermaid
flowchart TB
  Settings["FuzzSettings.tsx"] -- "Draft options via app.tsx" --> Panel["verification/RunsPanel.tsx"]
  Panel --> Hooks["verification hooks.ts"]
  Hooks -- "POST RunRequest with method fuzz" --> Run["verification RunService"]
  Run -- "model path, options, worker env" --> Worker["verification/worker.py"]
  Worker -- "run(model, request)" --> Runner["fuzzing/runner.py"]
  Runner -- "split_options, run_fuzzing" --> Bridge["engine_bridge/execution"]
  Bridge -- "ACT result" --> Runner
  Runner -- "worker output" --> Worker
  Worker -- "result file and progress pipe" --> Run
```

| Block | Code entry | Contract or artifact | Neighbor handoff |
| --- | --- | --- | --- |
| Configure | [FuzzSettings.tsx](FuzzSettings.tsx), [../verification/hooks.ts](../verification/hooks.ts) | `FuzzOptions` nested in `RunRequest` | [Verification](../verification/README.md) owns start and idempotency |
| Execute | [runner.py](runner.py) | `run_fuzzing` result and JSON line messages | [Engine bridge](../../engine_bridge/execution/README.md) owns ACT semantics |
| Supervise | [../verification/service.py](../verification/service.py) | Worker output becomes sealed result and fuzz artifact | [Records](../records/README.md) owns persistence |

### Live progress, frames, and query return

```mermaid
flowchart TB
  Bridge["Bridge ACT observer"] -->|"FuzzProgress / FuzzFrame callbacks"| Worker["runner / worker send"]
  Worker -->|"JSON lines over inherited pipe"| Supervisor["verification supervisor"]
  Supervisor -->|"observe message"| Live["FuzzLive"]
  Live -->|"Progress payload to commit"| Supervisor
  Supervisor -->|"Append then serve SSE event"| Browser["useLiveRuns invalidates run queries"]
  Browser -->|"Refetch fuzzing API"| Service["FuzzingService"]
  Live -->|"In-memory frame and hits"| Service
  Service -->|"FuzzingOut via hooks"| View["FuzzView"]
```

| Block | Code entry | Contract or artifact | Neighbor handoff |
| --- | --- | --- | --- |
| Progress | [live.py](live.py), [../verification/service.py](../verification/service.py) | `fuzz.progress` is committed and replayable | [Verification](../verification/README.md) owns event sequence |
| Frame | [live.py](live.py) | Latest frame is memory only while running | Fuzzing owns display state |
| Browser return | [service.py](service.py), [hooks.ts](hooks.ts) | `FuzzingOut` is pending with timeline and latest frame | [Visual Bench browser composition](../README.md#flow-diagram) refreshes the view |

### Save and export

```mermaid
flowchart TB
  User["SaveButton.tsx"] -- "counterexample index" --> Route["fuzzing/routes.py"]
  Route --> Service["FuzzingService"]
  Service -- "find ACT counterexample" --> Record["fuzzing.json or FuzzLive"]
  Service -- "annotation" --> Store[("saved_counterexamples.json")]
  User -- "download URL" --> Export["saved_assignment"]
  Export -- "sat plus X and Y float64 assignment" --> File["VNN-LIB result text"]
  Service -- "input shape" --> Model["model_spec.ModelService"]
```

| Block | Code entry | Contract or artifact | Neighbor handoff |
| --- | --- | --- | --- |
| Save | [service.py: save_counterexample](service.py) | First save returns 201, repeat returns 200, unknown ACT index is 404 | [Records](../records/README.md#flow-diagram) stores user annotation |
| Export | [service.py: saved_assignment](service.py) via `verification.service.vnncomp_sat` | `sat`, shaped `X`, and `[1,n]` `Y`, all `float64` (same format as verification-run exports) | [model_spec](../model_spec/README.md#flow-diagram) supplies shape |
| Image export | [FuzzSaved.tsx](FuzzSaved.tsx) and view helpers | Browser can download native resolution PNG for image inputs | Browser presentation owns PNG formatting |

## Validation

Run the module's real ACT tests:

```bash
.venv/bin/python -m pytest visual_bench/fuzzing
```

Acceptance is observable when the run emits queued, started, progress, and completed events; `/api/runs/{id}/fuzzing` changes from pending to available; `fuzzing.json` is sealed; frames are available without becoming events; repeated save requests return 201 then 200; and the exported text contains `sat`, shaped `X`, and `[1,n]` `Y`.

Use `visual_bench/verification/test_verification.py` for shared stop and run lifecycle behavior. Use `engine_bridge/execution/test_execution.py` for bridge frame and stop semantics. Do not claim these checks were run unless their command and result are recorded in the task completion record.

## Acceptance

- ACT controls the counterexample and verdict. Fuzzing reports `falsified` or `unknown`, never `certified`.
- Progress events are committed record data. Frames are display state while live and a capped artifact after completion.
- Saved counterexamples are annotations on the run record, not a second scientific result.

## Reference and Backlog

<details>
<summary>Current files, routes and contracts</summary>

## Current Files and Contracts

| Layer | Entry | Contract or artifact | Owner for handoff |
| --- | --- | --- | --- |
| Wire | [schemas.py](schemas.py) | `FuzzOptions`, `FuzzingOut`, progress, frame, seed, counterexample, and saved-counterexample payloads | `verification` embeds options in `RunRequest`; `generated/wire.ts` is generated |
| Worker | [runner.py](runner.py) | Calls `split_options` and `run_fuzzing`; writes JSON lines for `progress` and `frame`; returns `outcome` and `fuzzing` | `engine_bridge/execution` owns ACT option and result adaptation |
| Live service | [live.py](live.py) | Keeps the latest frame and ACT hits in memory; returns `fuzz.progress` for supervisor commit | `verification.RunService` owns the pipe and event log |
| Application service | [service.py](service.py) | Reads `fuzzing.json` and committed progress, saves annotations, emits VNN-LIB 2.0 text | `records` owns artifacts and annotations; `model_spec` owns input descriptions |
| HTTP | [routes.py](routes.py) | `/api/fuzz/defaults`, `/api/runs/{id}/fuzzing`, saved-counterexample routes | `verification` owns `/api/runs` and SSE |
| Browser data | [api.ts](api.ts), [hooks.ts](hooks.ts) | TanStack Query keys, mutations, and invalidation | `shared` owns HTTP and query primitives |
| Views | [FuzzView.tsx](FuzzView.tsx), [FuzzTimeline.tsx](FuzzTimeline.tsx), [FuzzMutations.tsx](FuzzMutations.tsx), [FuzzCounterexamples.tsx](FuzzCounterexamples.tsx), [FuzzSaved.tsx](FuzzSaved.tsx), [FuzzInputs.tsx](FuzzInputs.tsx), [FuzzStrategies.tsx](FuzzStrategies.tsx), [DeltaBars.tsx](DeltaBars.tsx), [SaveButton.tsx](SaveButton.tsx), [FuzzSettings.tsx](FuzzSettings.tsx), [presentation.ts](presentation.ts) | Presentation of live and sealed data | `workspace` and `verification` provide selection and run controls |
| Tests | [test_fuzzing.py](test_fuzzing.py) | Real ACT lifecycle, options, live events, stop, saved export, batch inputs | Keep fake fixtures separate from real ACT checks |


</details>

<details>
<summary>Task acceptance and planned capabilities</summary>

## Tasks

<a id="3-tasks"></a>

Task IDs retain the original `VER` prefix. Dependencies are acceptance prerequisites, not import instructions.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| VER-06 | Run and demonstrate ACTFuzzer from the GUI | EXE-04, VER-02, REC-01 | `fuzz` is a run method for every catalog model, with `FuzzOptions` (max iterations, RNG seed, stop at first counterexample, and ACTFuzzer's tunable hyperparameters: coverage strategy, activation threshold, mutation weights, perturb mode/scale, seed selection, PGD restarts; defaults equal the pinned ACT `pipeline.yaml`, served by `GET /api/fuzz/defaults` and drift-checked against ACT in `test_fuzzing.py`); options on another method are rejected. The worker streams progress as JSON lines over an inherited pipe; the supervisor commits each as a `fuzz.progress` event, so the Fuzzing tab follows the run live over SSE and a reconnect replays it. Mutated-input frames (lane 0 of ACT's mutated batch, sampled with the progress reports) arrive on the same pipe but are held in memory as the latest frame only, never committed as events; the Fuzzing tab shows that frame beside the coverage chart while running, and `fuzzing.json` keeps up to 16 frames as a playable filmstrip whose position is marked on the chart. The sealed `fuzzing.json` artifact holds ACT's summary, timeline, per-strategy counts, and the first 20 counterexamples (each with ACT's model output on its seed), plus the first 20 seed rows with their outputs; `GET /api/runs/{id}/fuzzing` serves it (`pending` with the live timeline while running). The view shows coverage and counterexamples over iterations, the seed inputs and their outputs, a gallery of mutated counterexamples (seed / mutated / perturbation; image thumbnails for 1- or 3-channel square inputs), expected vs argmax class for labelled properties, a seed-vs-mutated input and output comparison, and strategy shares. Records written before seed capture omit those parts. `test_fuzzing.py` covers the lifecycle and record. |
| VER-07 | Stop runs; save and export fuzz counterexamples; show the ACT verdict | VER-06 | `POST /api/runs/{id}/stop` is idempotent and commits `run.stop_requested`: a fuzz worker gets SIGTERM, ACTFuzzer ends after its current iteration through its own timeout check, and the run completes with ACT's report of the iterations run (`summary.stopped`); verify/BaB workers are killed and the run fails with `stopped` (no verdict). A worker that ignores the stop for `STOP_GRACE_S` is killed. Violating frames carry ACT's own counterexample (`FuzzFrameOut.counterexample`; lane 0 need not be it), so the Fuzzing tab lists counterexamples while running. `POST /api/runs/{id}/saved-counterexamples {index}` saves ACT's counterexample #index on the record (idempotent: 201 then 200; 404 if ACT reported none); `GET .../saved-counterexamples/{index}/vnnlib` returns it as a VNN-COMP result file: `sat` followed by the VNN-LIB 2.0 command-line assignment (standard Sec. 5.3.1) of `X` (input-spec shape) and `Y` (`[1, n]`), element type `float64` because ACT computes and checks in float64; the browser exports image inputs as a native-resolution PNG. `VerdictBanner.tsx` shows the selected run's ACT verdict (CERTIFIED / COUNTEREXAMPLE FOUND / UNKNOWN / TIMEOUT, or no verdict) above the Verification and BaB modes. Evidence: `test_fuzzing.py` (save/export, fuzz stop), `../verification/test_verification.py` (verify stop), and `engine_bridge/execution/test_execution.py` (frame counterexample, `should_stop`). |


Future command controls, richer ACT observer support, and additional frame history require an ACT capability and a task update before implementation. The current implementation relies on ACTFuzzer's private progress hook and keeps only the latest live frame.

</details>
