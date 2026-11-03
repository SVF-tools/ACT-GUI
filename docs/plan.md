# Development Plan

**Status:** all implementation tasks are Planned. This repository currently contains documentation only. Module READMEs own detailed feature behavior, interfaces, implementation files, task acceptance, and completion records. This document owns bootstrap tasks, integration order, and release acceptance.

Task dependencies are prerequisites for acceptance, not code-import directions. Developers may build against explicitly labeled fixtures before engine work lands; a fixture alone cannot complete a real ACT integration task. No duration or staffing-throughput estimate is assumed.

## Bootstrap

| ID | Owner | Task | Depends on | Completion evidence |
| --- | --- | --- | --- | --- |
| BASE-01 | A | Pin ACT baseline and inspect real capabilities | None | Record commit, environment/solver, a distributable small model/spec, and missing hooks needed for observation/inspection/control. |
| BASE-02 | B | Bootstrap reproducible tooling and contract generation | BASE-01 | Validate Python/TypeScript packaging, thin entry points, pinned dependencies, minimal test/CI commands, Pydantic→REST/event generation, and the first real fixture. |

## Module Task Map

| Module | Owner | Task IDs | Detailed plan |
| --- | --- | --- | --- |
| visual_bench/workspace | C | WS-01, WS-02, WS-03 | [README](../visual_bench/workspace/README.md) |
| visual_bench/model_spec | C | MSV-01, MSV-02, MSV-03 | [README](../visual_bench/model_spec/README.md) |
| visual_bench/verification | B | VER-01, VER-02, VER-03, VER-04 | [README](../visual_bench/verification/README.md) |
| visual_bench/bab | C | BAB-01, BAB-02, BAB-03 | [README](../visual_bench/bab/README.md) |
| visual_bench/analysis | D | ANA-01, ANA-02, ANA-03 | [README](../visual_bench/analysis/README.md) |
| visual_bench/assistant | B | AI-01, AI-02, AI-03 | [README](../visual_bench/assistant/README.md) |
| visual_bench/records | B | REC-01, REC-02, REC-03, REC-04 | [README](../visual_bench/records/README.md) |
| engine_bridge/engine_session | B | ES-01, ES-02, ES-03 | [README](../engine_bridge/engine_session/README.md) |
| engine_bridge/model_spec | B | MSB-01, MSB-02, MSB-03 | [README](../engine_bridge/model_spec/README.md) |
| engine_bridge/execution | B | EXE-01, EXE-02, EXE-03 | [README](../engine_bridge/execution/README.md) |
| engine_bridge/inspection | B | INSP-01, INSP-02, INSP-03 | [README](../engine_bridge/inspection/README.md) |
| engine_bridge/events | B | EVT-01, EVT-02, EVT-03 | [README](../engine_bridge/events/README.md) |

## Integration Slices

| Slice | Required outcome | Main dependency chain |
| --- | --- | --- |
| I1: real model/spec inspection | Start from documented commands; display one real graph and specification with correct identity and errors | BASE-01/02 → ES-01/02 → MSB-01/02/03 → VER-01; WS-01/02 → MSV-01, then MSV-02/03 |
| I2: real run and minimal persistence | Worker execution, run identity, final ACT result, explicit failure, saved provenance | EXE-01 + REC-01 + VER-01 → VER-02; EXE-02 establishes observation/inspection handles |
| I3: propagation slice | Manually browse real input-to-output layer states, then add available geometry | EXE-02 → INSP-01 → ANA-01; INSP-02 → ANA-02. Full BaB control is not required |
| I4: committed BaB and replay | Stable node identity, committed batches, snapshots, reconnect, local graph | EVT-01/02 → REC-02 + VER-03 → BAB-01/02; REC-03 adds replay |
| I5: evidence-based AI | Ask about a selected real node, obtain supported evidence, and navigate to the source | AI-01 + BAB-01 → AI-02. Provider integration is selected and configured here |
| I6: controls, advanced analysis, and export | Shared manual/AI execution, recorded propagation, traceable exports | EXE-03 → VER-04 → BAB-03/AI-03; INSP-03 + REC-03 → ANA-03; ANA-02 + REC-03 → REC-04 |

I3 and I4 may proceed in parallel after real execution handles exist. First delivery is I1, followed by I2 and the focused propagation slice; do not schedule all modules concurrently for a three-person team.

## Cross-repository Work

A owns ACT public-interface and scientific-semantics work. BASE-01 identifies actual gaps. EXE-02/03, EVT-01/02, and INSP-01/02 may require ACT changes; their module plans define the intended capability rather than asserting it exists. Link the ACT issue/PR and tested commit in each integration task. Keep the GUI baseline pinned; do not silently track ACT main.

## Team and Review

- A: ACT interfaces, numerical semantics, stable identities, commit/control boundaries, and real samples.
- B: integration, application services, contracts, records, AI orchestration, and cross-repository coordination.
- C: workbench interaction, browser views, selection state, and AI presentation.
- D, if available: analysis/visualization and evaluation integration. With three contributors, C implements D-owned views and B coordinates their integration.

Each task owner supplies its tests. A reviews mathematical semantics; C reviews user-visible behavior. A cross-layer feature has one integrated acceptance result, not separate claims that each side is complete.

## Release Acceptance

| ID | Owner | Depends on | Required evidence |
| --- | --- | --- | --- |
| REL-01 | B | MSV-02, MSV-03, WS-03, BAB-03, ANA-03, AI-03, REC-04, EVT-03, ES-03 | Run the real model→verification→BaB→propagation→AI evidence/authorized plan→record/replay/export flow on declared Windows/macOS/Linux browser configurations; record supported engine combinations, performance measurements, and limitations. |

A release may explicitly omit an unsupported control only through a documented scope change: keep the capability disabled, update affected task acceptance, and report the limitation. Do not mark an unimplemented task complete merely because its button is hidden.

## Validation and Completion Rules

Use pure/behavior tests for selection and state, native-versus-adapter parity for scientific data, schema-generation checks for wire contracts, and a few real browser flows for end-to-end behavior. Pair deterministic fake-provider tests with separately reported real-provider evaluation. GPU/solver-specific behavior needs its actual environment before claiming support.

Measure renderer size, event throughput, inspection latency, memory, and observer overhead on recorded hardware/fixture/browser versions; agree thresholds before release rather than inventing performance claims. Three browser engines on one OS do not certify Windows/macOS/Linux.

Each task completion record includes code PR, input/fixture provenance, actual commands/results, ACT/provider versions where relevant, and known limitations. Add tests and lightweight CI with the first behavior; planned source files and commands are not required to exist before their task starts.
