# Analysis and Propagation

**Status:** first version: `AnalysisView.tsx` (ANA-01 on recorded interval states; ANA-02 limited to interval-box projection); ANA-03 not started. **Owner:** D; with three contributors C implements, B integrates data, and A reviews numerical semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).


## Current Files and Usage

| File | Layer | Responsibility |
| --- | --- | --- |
| `schemas.py` | Wire | `LayerStatesOut`, `LayerStateOut`. |
| `service.py` | Service | `AnalysisService.layer_states(run_id)`: reads the sealed `layers.json` of a completed run (recorded by the run worker through `engine_bridge.inspection`), with availability and provenance. |
| `routes.py` | HTTP | `GET /api/runs/{id}/layers`. |
| `api.ts`, `hooks.ts` | Browser data | Layer-state query keyed under the run (`keys.layers`), refreshed with the run's events. |
| `AnalysisView.tsx` | View | Propagation stepper, before/after bars, value selection, interval-box projection (Verification mode). |

Tests: the layer-state route is covered by `../verification/test_verification.py` (BaB lifecycle, domain runs) and the bridge parity in `engine_bridge/inspection/test_inspection.py`.

## 1. Subproblems and Objective

Show input-to-output approximation propagation and support comparisons with explicit provenance.

| Subproblem | Responsibility |
| --- | --- |
| Propagation | Stage navigation, input set/operator/output approximation, and bound summaries; support DAG paths and merge inputs. |
| Geometry | Coordinate/projection selection and interval/constraint/set representations; distinguish samples from sound outer approximations. |
| Comparison | Compare parent/child or pre/post-refinement data at the same layer, coordinates, and scale; expose method and budget differences between experiments. |
| Browsing | Layer selection, stage playback, and links to network views, BaB, and AI evidence. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not compute scientific projections or verification verdicts in the browser, treat animation intermediates as evidence, or equate stage playback with solver stepping.

## 3. Inputs, Outputs, and State

- **Inputs:** Layer inspections, geometry/artifacts, model DAG, specification, and selection context.
- **Outputs:** Propagation View, bound/set plots, comparison displays, and exportable data/plot configuration.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Stage view models and pure derivation.** Map ACT before/after states and provenance into testable stages. Do not hide scientific transformations inside renderers.

**Context-keyed queries and renderer adapters.** Include run/node/revision/layer/projection in cache keys. Plotting libraries receive data and configuration only.

**Comparable snapshots.** Fix both comparison sources and explicitly handle incompatible dimensions or scales.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Use verification queries backed by engine_bridge.inspection. workspace owns context; records supplies historical artifacts. Complete BaB controls are not a prerequisite.

Start with one PropagationView and a stage model. Do not create an analysis/propagation subdirectory yet.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| ANA-01 | Deliver manual real-data propagation | INSP-01, VER-02, WS-02 | For a small real model, navigate input to output; every stage agrees with ACT before/after values and tensor IDs; missing stages are explicit. |
| ANA-02 | Add geometry, coordinate selection, and comparison | ANA-01, INSP-02 | Two selected coordinates render their declared representation; samples are distinct; incompatible axes disable misleading comparisons. |
| ANA-03 | Add recorded playback and evidence navigation | ANA-02, INSP-03, REC-03 | Playback does not invoke solver stepping; a missing historical stage pauses/skips explicitly; AI evidence selects the exact recorded stage. |

Owner: **D**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Geometry, numbers, and method labels in one view refer to the same context.
- Interval-only data renders as an interval box; missing history is not_recorded, not invented geometry.
- Late layer/node responses do not replace the active view; dimension changes are not misrepresented as tighter approximation.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Propagation View Design

Overapproximation propagation is a dedicated interactive view within analysis. Show how an input domain transforms and is approximated across the network, and how the output relates to the specification. Share context with network, BaB, and AI views without creating another top-level area.

Start with a PropagationView component; extract analysis/propagation only when code complexity requires it.

| View element | Behavior |
| --- | --- |
| Layer/stage navigation | Navigate input → operators/layers along a selected network path → output. Link layer selection to the network view; support DAG branch selection and merge-input inspection |
| Set transformation | Show the stage input set, operator/method, and output approximation. Label two-dimensional coordinates, projections, and dimension changes. Expand finer transformation/relaxation stages only when ACT provides them |
| Bound summary | Show layer intervals, widths, available stability indicators, and method. Bind numbers and geometry to the same node/revision/layer |
| Stage browsing | Previous/next/play traverse available stages and synchronize layer selection. Playback is not ACT solver stepping |
| Comparison | Compare parent/child or pre/post-refinement data at the same layer, coordinates, and scale, with separate revision/method/guarantee labels |
| Output inspection | Relate available output approximations to specification boundaries. Read final verdicts from ACT rather than inferring global proof from a two-dimensional projection |

Model Explorer is a candidate network navigator in model_spec. Propagation uses dedicated set/constraint/numerical plots; the network renderer need not implement the entire analysis view.

For high-dimensional layers, prioritize bounds and explicit coordinate selection rather than unlabeled polygons. When dimensions change, show the new coordinates; changes in projected area across different coordinates do not establish approximation tightening.

Distinguish samples, exact representations, sound outer approximations, and heuristics. With intervals only, render an interval box. With no geometry, retain numerical inspection.

Playback visits ACT-provided or recorded states. Visual transitions are not additional computation evidence. Unrecorded historical states remain not_recorded; a new inspection has independent provenance.

Data flows through verification queries to engine_bridge.inspection. records persists it under the selected retention policy, workspace owns node/layer selection, and assistant may navigate to a stage and cite its evidence.

Initial acceptance uses a small real model with fixed input/run: manually traverse to the output, match ACT data/provenance, show missing stages, and prevent context mixing when selecting nodes. Add automatic playback and BaB comparisons afterward.

## 10. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Browse propagation | Select a run/input domain and a layer/path; press Previous or Next. | Show stage input/operator/output, bound summaries, coordinates, method, and availability from one context. |
| Inspect and compare sets | Choose coordinates or a second node/revision. | Request an ACT projection when supported; align comparable axes and label each source and guarantee. |
| Replay and export a stage | Play recorded stages or export the current comparison. | Playback visits stored/available states; export fixes context, numerical data, and plot settings. |

### Processing Flow

1. Resolve the model DAG into addressable stage references; require explicit path/merge-input choices.
2. Build a query key from model/spec/run/node/revision/layer/stage/projection/method.
3. Request stage data through verification and retain availability separately from payload.
4. Create a StageViewModel with before/after bounds and optional geometry; render numbers even when geometry is absent.
5. Move selection to the next stage or pin a comparison source; discard stale display responses by context key.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `listStages(modelRef, pathSelection) → StageRef[]` | Navigation derives from the actual DAG and available ACT stage semantics, not invented intermediate transforms. |
| `loadStage(context, projection) → StageResult` | Result has available/pending/not_recorded/unsupported/error branches with the echoed context. |
| `buildStageView(result) → StageViewModel` | Pure formatting and display metadata; no scientific bound or projection solver. |
| `compareStages(left, right, alignment) → ComparisonView` | Checks layer/tensor/coordinate compatibility before displaying a tightening comparison. |
| `advancePlayback(cursor, stageIndex) → PlaybackState` | Changes only the browsing cursor; never submits an engine step command. |

### Planned Files (design targets)

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `PropagationView.tsx` | Stage selector, input/operator/output area, bounds, and playback controls. |
| `stage_model.ts` | Stage identities, availability, context keys, and pure display transforms. |
| `plot_adapter.ts` | Interval/set/sample rendering with explicit guarantee labels. |
| `comparison.ts` | Alignment rules and fixed-source comparison view model. |
| `analysis.test.tsx` | Stage flow, stale responses, representation labels, and missing history. |

### State, Failure, and Recovery Rules

Presentation may animate between displayed states, but interpolated shapes are not evidence. Coordinate changes require relabeling; interval width/area across unrelated coordinates cannot establish tighter approximation. Output-specification overlays must use the same coordinate meaning, and ACT alone supplies the final verdict.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
