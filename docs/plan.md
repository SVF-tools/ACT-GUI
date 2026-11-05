# Development Plan

**Status:** a runnable version exists; [First-version status](#first-version-status) records dated implementation evidence and remaining acceptance gaps. An implementation milestone is not full roadmap acceptance. Module READMEs own current development paths, detailed task acceptance and completion records. This document owns the task index, ACT prerequisites, future integration order and release acceptance.

## Choose the Right Entry

| Your task | Read first |
| --- | --- |
| Change an implemented feature | [Root task chooser](../README.md#choose-a-development-task), then the owning module's Change Guide and Validation sections |
| Understand a cross-module handoff | [Workbench map](../visual_bench/README.md#flow-diagram) or [bridge map](../engine_bridge/README.md#flow-diagram) |
| Plan an unsupported capability | The module backlog, then [Cross-repository Work](#cross-repository-work) and the integration slices below |
| Review past acceptance evidence | [First-version status](#first-version-status) and the owning module's task record; rerun relevant checks for a new change |

Roadmap dependencies below are not a file-edit sequence. A feature may reuse a completed lifecycle/storage path without modifying it. Current flows belong in module guides; proposed APIs and future file names stay in their backlogs.

Task dependencies are prerequisites for acceptance, not code-import directions. Developers may build against explicitly labeled fixtures before engine work lands; a fixture alone cannot complete a real ACT integration task. No duration or staffing-throughput estimate is assumed.

## Bootstrap

| ID | Owner | Task | Depends on | Completion evidence |
| --- | --- | --- | --- | --- |
| BASE-01 | A | Pin ACT baseline and inspect real capabilities | None | Record commit, environment/solver, a distributable small model/spec, and the gap list for observation/inspection/control, mapped to ACT-01..05. |
| BASE-02 | B | Bootstrap reproducible tooling, local web entry, and contract generation | None | Validate Python/TypeScript packaging, thin app.tsx/server.py entry points, pinned dependencies, and minimal test/CI commands. Documented development commands start the FastAPI service and the browser dev server on loopback; opening the printed localhost URL loads the workbench shell, which reaches a service health route. The Pydantic→TypeScript/event-schema pipeline runs on a synthetic schema with a drift check. |
| BASE-03 | A | Commit the first real fixture | BASE-01, BASE-02 | The BASE-01 model/spec and one native ACT verification result are stored with provenance (ACT commit, environment, command, hashes) and load through the BASE-02 test tooling. |

BASE-02 does not wait for ACT; only BASE-03 needs the pinned engine. Development access is a browser on the same machine at the documented localhost URL; remote access is a distribution concern (DIST-01).

## Module Task Map

| Module | Owner | Task IDs | Detailed plan |
| --- | --- | --- | --- |
| visual_bench/workspace | C | WS-01, WS-02, WS-03, WS-04 | [README](../visual_bench/workspace/README.md) |
| visual_bench/model_spec | C | MSV-01, MSV-02, MSV-03, MSV-04, MSV-05 | [README](../visual_bench/model_spec/README.md) |
| visual_bench/verification | B | VER-01, VER-02, VER-03, VER-04, VER-07 (stop, verdict banner), VER-11 (counterexample save/export), VER-12 (run diagnostics, reproduction snapshot) | [README](../visual_bench/verification/README.md) |
| visual_bench/fuzzing | B (service), C (views) | VER-06, VER-07 (saved counterexamples) | [README](../visual_bench/fuzzing/README.md) |
| visual_bench/engine | B | VER-05, VER-08 (ACT branch switching), VER-09 (capability gating), VER-10 (user-entered repositories) | [README](../visual_bench/engine/README.md) |
| visual_bench/bab | C | BAB-01, BAB-02, BAB-03 | [README](../visual_bench/bab/README.md) |
| visual_bench/analysis | D | ANA-01, ANA-02, ANA-03 | [README](../visual_bench/analysis/README.md) |
| visual_bench/assistant | B | AI-01, AI-02, AI-03, AI-04 | [README](../visual_bench/assistant/README.md) |
| visual_bench/records | B | REC-01, REC-02, REC-03, REC-04 | [README](../visual_bench/records/README.md) |
| engine_bridge/engine_session | B | ES-01, ES-02, ES-03, ES-04, ES-05, ES-06 | [README](../engine_bridge/engine_session/README.md) |
| engine_bridge/model_spec | B | MSB-01, MSB-02, MSB-03, MSB-04 | [README](../engine_bridge/model_spec/README.md) |
| engine_bridge/execution | B | EXE-01, EXE-02, EXE-03, EXE-04, EXE-05 | [README](../engine_bridge/execution/README.md) |
| engine_bridge/inspection | A | INSP-01, INSP-02, INSP-03 | [README](../engine_bridge/inspection/README.md) |
| engine_bridge/events | A | EVT-01, EVT-02, EVT-03 | [README](../engine_bridge/events/README.md) |

## Integration Slices

These are roadmap acceptance chains, including unimplemented ACT capabilities. They do not describe the order of calls in the current workbench. Fuzzing reuses I2's run lifecycle and records; its current start/live/export paths are in the [fuzzing guide](../visual_bench/fuzzing/README.md#flow-diagram).

| Slice | Required outcome | Main dependency chain |
| --- | --- | --- |
| I1: real model/spec inspection | Open the workbench at the documented localhost URL; display one real graph and specification with correct identity and errors, including missing-ACT and version-mismatch diagnostics | BASE-02 → WS-01/02; BASE-01 → BASE-03 + ES-01/02 → MSB-01/02/03 → VER-01 → MSV-01, then MSV-02/03 |
| I2: real run and minimal persistence | Worker execution, run identity, final ACT result, explicit failure, saved provenance | EXE-01 + REC-01 + VER-01 → VER-02 |
| I3: propagation slice | Manually browse real input-to-output layer states of a completed run, then add available geometry | EXE-01 + ACT-01 → INSP-01 → ANA-01; ACT-04 → INSP-02 → ANA-02. Live run handles and BaB are not required |
| I4: committed BaB and replay | Stable node identity, committed batches, snapshots, SSE reconnect, local graph | ACT-02 → EXE-02 → EVT-01 → ACT-03 → EVT-02 → REC-02 + VER-03 → BAB-01 → BAB-02 (with PERF-01); REC-03 adds replay |
| I5: evidence-based AI | Ask about a selected real layer/stage, obtain supported evidence, and navigate to the source; then the same for a committed BaB node | AI-01 + ANA-01 → AI-02; AI-02 + BAB-01 → AI-03. Provider integration is selected and configured in AI-02 |
| I6: controls, advanced analysis, export, and distribution | Shared manual/AI execution, recorded propagation, traceable exports, one-origin build | ACT-05 + EXE-03 → VER-04 → BAB-03/AI-04; INSP-03 + REC-03 → ANA-03; ANA-02 + REC-03 → REC-04; VER-03 → DIST-01 |

The initial delivery sequence was I1, then I2 and I3; first-version implementations now exist with the gaps listed below. I3 needs only a completed run plus ACT-01, so real-provider explanation work (AI-02) can follow I3 without waiting for committed BaB events. I4 depends on the riskiest ACT changes (ACT-02/03) and may proceed in parallel with I3/AI-02 once I2's prerequisites are satisfied.

## Cross-repository Work

A owns ACT public-interface and scientific-semantics work. BASE-01 produces the gap list; each gap is one ACT task below, and the GUI integration task that needs it depends on it explicitly. Module plans define the intended capability rather than asserting it exists.

| ID | Owner | ACT capability | Needed by | Depends on | Completion evidence |
| --- | --- | --- | --- | --- | --- |
| ACT-01 | A | Read layer states (before/after per stage, tensor mapping) for a completed run | INSP-01 | BASE-03 | A native ACT test reads input-to-output stages of the BASE-03 run; absent stages are reported, not zero-filled. |
| ACT-02 | A | Observable run handles: live inspection access, completion, interruption | EXE-02 | BASE-01 | Handle lifecycle and safe read boundary are documented and exercised by a native ACT test. |
| ACT-03 | A | Committed node/wave observation hooks with commit and rollback points | EVT-02 | EVT-01 | A native ACT test shows rolled-back work never appears as committed; batch identity, sequence, and revision are emitted. |
| ACT-04 | A | Geometry/projection export with coordinates, representation, and guarantee | INSP-02 | ACT-01 | A native ACT test exports a declared projection with its guarantee; interval-only methods report interval-only. |
| ACT-05 | A | Pause/step/split/cancel at safe boundaries with explicit rejection results | EXE-03 | ACT-02, ACT-03 | Each supported control has a native ACT test, including stale-target and failed-precondition rejection; unsupported controls are declared unsupported. |

Each ACT task completes either with a linked ACT issue/PR whose tested commit becomes the new pinned GUI baseline, or with BASE-01 evidence that the current baseline already provides the capability (closed with no ACT change). Keep the GUI baseline pinned; do not silently track ACT main. Switching to another branch in the Engine tab (VER-08) is an explicit, recorded user choice and does not move the pinned baseline.

## Team and Review

- A: ACT interfaces (ACT-01..05), numerical semantics, stable identities, commit/control boundaries, real samples (BASE-01/03), and the engine-facing inspection and events adapters.
- B: tooling, integration, application services, contracts, records, AI orchestration, distribution, and cross-repository coordination.
- C: workbench interaction, browser views, selection state, and AI presentation.
- D, if available: analysis/visualization, performance baselines, and evaluation integration. With three contributors, C implements D-owned views and PERF-01, and B coordinates their integration.

Each task owner supplies its tests. A reviews mathematical semantics; C reviews user-visible behavior. A cross-layer feature has one integrated acceptance result, not separate claims that each side is complete.

## Cross-cutting Tasks

| ID | Owner | Task | Depends on | Completion evidence |
| --- | --- | --- | --- | --- |
| PERF-01 | D | Record performance baselines and draft thresholds | BASE-03 | Record reference hardware, OS, browser versions, fixture sizes, and measurement method for renderer size, event throughput, inspection latency, memory, and observer overhead; A, B, and C agree draft thresholds used by BAB-02 and EVT-03. |
| DIST-01 | B | Package the one-origin distribution | BASE-02, VER-03 | One build serves assets, workers, API, and SSE from a single origin, bound to loopback by default; remote single-user mode refuses to start without HTTPS and configured access authentication; build and start commands are documented. |
| DIST-02 | B | Ship the workbench as a Docker Compose service with GPU support and user-supplied Gurobi licenses | BASE-02, BASE-03, ES-04, VER-05 | `scripts/docker_build.sh` builds one image from the pinned ACT commit; `docker compose up` serves the workbench on loopback; the bridge and service test suites pass inside the container on CPU and, with `compose.gpu.yaml`, on an NVIDIA GPU with the run result recording a CUDA device; no license file is present in the image. |

## First-version status

The following is historical evidence, not a fresh test report or a replacement for current module guides. Later source-loading, fuzzing and structural additions are recorded in their own rows.

Recorded 2026-11-03 against ACT `deff2fb0c031` (branch CLIMB, tracked tree clean), CPU, conda `act-py312` (Python 3.12, torch 2.11). Evidence: `.venv/bin/python -m pytest` (29 passed, real ACT), `npm test` (5 passed), `npm run typecheck`, `npm run check:types`, plus a headless-Chrome walk-through of the localhost UI (model → BaB run → layer → assistant → export). Fuzzing addition (same day): 39 passed, plus a headless-Chrome walk-through of live and completed fuzz runs on `bab_deep_mlp` and `unsafe_linear` (desktop dark/light, 390 px width).

| Task | State | What exists / what is missing |
| --- | --- | --- |
| BASE-01 | First version | Baseline pinned in `fixtures/catalog.json`. Gap list: no BaB observer (ACT-03), no observable run handles or controls (ACT-02/05), no projection export (ACT-04). Layer reads (ACT-01) already work through public `analyze`. |
| BASE-02 | First version | uv venv on the ACT env, npm/Vite/React/TS, `scripts/dev.sh` on loopback, Pydantic→TS generation with drift check. No CI yet. |
| BASE-03 | First version | `scripts/record_fixtures.py` records 8 ACT nets by path + sha256 + native verdicts (ACT files are not copied; ACT is AGPL-3.0): 4 ACT example nets, plus MNIST (6x100 MLP at eps 0.03 and a falsifiable eps 0.15 variant, conv-small) and CIFAR-10 (conv-med) nets that `scripts/gen_image_nets.py` converts from BaVerLy ONNX models in the ACT checkout through ACT's front end (L-inf box around test image 0, TOP1_ROBUST). Still a fixed catalog: no upload or arbitrary-path loading (MSB `loadModel`). |
| ES-01 | First version | Probe with capabilities, missing-ACT and version-mismatch diagnostics. ES-02 (explicit handles) not started; each call loads the model. |
| MSB-01..03 | First version | JSON ACT nets with box INPUT_SPEC and ASSERT; parity tests vs native DAG/spec. Other spec kinds raise `unsupported_spec`. No A review yet. |
| MSB-04, MSV-04 | First version | Model sources: VNN-LIB instances (ACT `create_specs_from_paths`) and ONNX image classifiers with a chosen MNIST/CIFAR-10 test image and eps; built nets stored content-addressed with their parameters; Load model panel. ACT torchvision-zoo models are not offered (untrained, 3x224x224 inputs exceed the bridge's spec limits). The BaVerLy CIFAR-10 model reaches 36% clean accuracy on raw pixels (no tried normalization exceeds 44%); ACT's interval BIAS transfer function does not accept 4-D constants, so no normalization layer is prepended. |
| MSV-05 | First version | 2026-11-05: built models record the ACT commit and source they were built on; after a branch switch a model whose net the active engine cannot load is marked "needs rebuild" and rebuilds from its recorded settings (`POST /api/models/{id}/rebuild`). See [model_spec](../visual_bench/model_spec/README.md#3-tasks). |
| VER-11 | First version | 2026-11-05: falsified verify_once/BaB runs save ACT's counterexample on the run record and export it as a VNN-COMP witness (Y from ACT's ACTToTorch model) or PNG, like fuzz counterexamples. See [verification](../visual_bench/verification/README.md#3-tasks). |
| VER-12 | First version | 2026-11-05: every run that reaches a worker records diagnostics (warnings, WARNING+ logs, ACT's printed [WARN]/[ERROR] lines, exception chain located at the innermost ACT frame, worker logs, engine snapshot); Run History shows them and downloads a reproduction snapshot with request, ACT net, engine info and `reproduce.py`. See [verification](../visual_bench/verification/README.md#3-tasks). |
| EXE-01 | First version | `verify_once` (interval / dual / hybridz domain, selectable per run) and `verify_bab_batched` (same entry as ACT's pipeline CLI); verdicts match recorded native results. EXE-02/03 blocked on ACT-02/05. |
| INSP-01 | First version | Interval after-states per layer, recorded by the run worker; "before" = predecessor's after. No paging (>65536 values rejected). INSP-02/03 not started. |
| EVT-01 | First version | Coverage audit: summary-only BaB metadata. EVT-02/03 blocked on ACT-03. |
| VER-01/02 | First version | Wire schemas + generated types; non-blocking start, worker process, failure states, native parity flag. |
| VER-03 | Partial | Ordered lifecycle events over SSE with replay (`after`/Last-Event-ID). No scientific snapshots (needs EVT-02). |
| VER-04 | Partial | Idempotent start (`client_request_id`, 409 on changed parameters). No engine commands exist. |
| REC-01 | First version | Manifest, hashed artifacts, sealed records, hash-checked reads, zip export without absolute paths. |
| REC-02/03 | Partial | Atomic writes, torn-tail recovery, interrupted-run marking, event replay. No commit batches (needs EVT-02). REC-04 export only, no import. |
| WS-01/02 | First version | Selection reducer + latest-request guard (vitest). WS-03 not started. |
| WS-04 | Implemented | Online-visitor bar: `POST /api/presence` heartbeat, in-memory 90 s window (pytest `visual_bench/workspace`). |
| MSV-01 | First version | Model list, SVG DAG, spec and layer detail on real data; image-shaped specs render as images with sampled perturbations. MSV-02 renderer evaluation and MSV-03 drafts not started. |
| ANA-01 | First version | Stepper over recorded layer states, before/after bars, value selection. ANA-02: interval-box 2-D projection only. ANA-03 not started. |
| BAB-01..03 | Not started | Blocked on committed node events (ACT-03); the BaB tab shows coverage and the summary only. |
| AI-01 | First version | Frozen context, typed evidence, deterministic fake provider, cited ids must resolve. AI-02 needs a real provider (not configured). |
| EXE-04, VER-06 | First version | ACTFuzzer as run method `fuzz` on every catalog model (`engine_bridge/execution/fuzz.py`, worker progress pipe, `fuzz.progress` SSE events, sealed `fuzzing.json`, `GET /api/runs/{id}/fuzzing`, Fuzzing tab with live timeline, strategies, and counterexamples). Progress relies on ACTFuzzer's private `_print_progress`; no public ACT observer exists. Fuzzing reports `falsified` or `unknown`, never `certified`. |
| ES-04, VER-05 | First version | Gurobi probe in a subprocess (`engine_bridge/engine_session/session.py`), license upload/remove/status API and the Engine tab; uploaded license stored 0600 and passed to run workers. Current methods do not use Gurobi. |
| ES-05, ES-06, VER-08..10 | First version | 2026-11-05: the Engine tab switches the imported ACT code between the pinned baseline and a branch head of any ACT fork: operator-configured remotes (`ACT_GUI_ACT_REMOTES`, default SVF-tools and guanqin-123) or an https URL a user enters (remembered once it imports as ACT; `ACT_GUI_ALLOW_CUSTOM_REMOTES=0` disables entry). Entering a URL runs that repository's code on the server, so a public deployment needs access control (DIST-01). A switch restarts the service process, because ACT cannot be re-imported in a running process. Catalog nets, `data/` and `literature/` stay on the baseline `ACT_ROOT`. Every capability is gated on API checks of the ACT symbols its adapter calls (`engine_session/parity.py`), and failing features are disabled in the browser. These are interface checks: a non-baseline commit keeps the `version_mismatch` warning, and its numerical results are not baseline-certified. |
| DIST-02 | First version | `Dockerfile`, `compose.yaml` (+ `compose.gpu.yaml`, `compose.gurobi.yaml`), `scripts/docker_build.sh`. No registry publishing or CI yet; the pinned ACT commit is not yet pushed upstream. |
| STRUCT-01 | First version | 2026-11-04 module-slice restructure (docs/design.md section 3): per-module `schemas.py`/`service.py`/`routes.py` composed in `workbench.py`; new `fuzzing` and `engine` modules split out of verification; browser `shared/` layer, per-module `api.ts`/`hooks.ts` on TanStack Query, mode registry; tests moved next to their modules; ACT method/option/provenance knowledge moved to `engine_bridge/execution`. HTTP paths and payloads unchanged (`npm run check:types` drift check; the only generated change is a docstring path). |
| DIST-01, PERF-01, REL-01 | Not started | The container serves one origin on loopback, but remote HTTPS/authentication mode is not implemented. |

## Release Acceptance

| ID | Owner | Depends on | Required evidence |
| --- | --- | --- | --- |
| REL-01 | B | MSV-02, MSV-03, WS-03, BAB-03, ANA-03, AI-04, REC-04, EVT-03, ES-03, DIST-01 | Run the real model→verification→BaB→propagation→AI evidence/authorized plan→record/replay/export flow on declared Windows/macOS/Linux browser configurations; record supported engine combinations, performance measurements, and limitations. |

A release may explicitly omit an unsupported control only through a documented scope change: keep the capability disabled, update affected task acceptance, and report the limitation. Do not mark an unimplemented task complete merely because its button is hidden.

## Validation and Completion Rules

Use pure/behavior tests for selection and state, native-versus-adapter parity for scientific data, schema-generation checks for wire contracts, and a few real browser flows for end-to-end behavior. Pair deterministic fake-provider tests with separately reported real-provider evaluation. GPU/solver-specific behavior needs its actual environment before claiming support.

Measure renderer size, event throughput, inspection latency, memory, and observer overhead on recorded hardware/fixture/browser versions; PERF-01 sets draft thresholds before the tasks that need them, and REL-01 confirms them; do not invent performance claims. Three browser engines on one OS do not certify Windows/macOS/Linux.

Each task completion record includes code PR, input/fixture provenance, actual commands/results, ACT/provider versions where relevant, and known limitations. Add tests and lightweight CI with the first behavior; planned source files and commands are not required to exist before their task starts.
