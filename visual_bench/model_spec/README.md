# Model and Specification View

**Status:** first version: `ModelList.tsx`, `ModelGraph.tsx` (in-house SVG DAG), `SpecPanel.tsx` (MSV-01); MSV-02/03 not started. **Owner:** C; B integrates data; A reviews variable and constraint semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Help users understand the model and specification under verification and select objects for further analysis.

| Subproblem | Responsibility |
| --- | --- |
| Network description | DAG structure, tensor connections, layer attributes, shapes/dtypes, and stable IDs. |
| Specification | Input domains, output constraints, variable mappings, and normalization; keep editable drafts separate from run snapshots. |
| Rendering and linking | Bidirectional graph/detail selection. Convert renderer-specific formats only within this module. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not independently reinterpret model semantics, simplify unsupported specifications into boxes, or calculate bounds inside graph components.

## 3. Inputs, Outputs, and State

- **Inputs:** Stable model/spec descriptions, source hashes, capabilities, and selection context.
- **Outputs:** Network/specification views, layer selection, explicit model/spec references, and run-input drafts.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**View model and renderer adapter.** Convert engine descriptions into presentation data before adapting them to Model Explorer. The bridge remains independent of the renderer.

**Immutable run inputs.** Drafts may change; model/spec snapshots referenced by an existing run remain fixed.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Use verification model-query use cases and workspace selection interfaces. These may start as small functions. Requires real bridge.model_spec descriptions, not BaB controls.

Start with view.tsx, view_model.ts, and the required renderer adapter. Model Explorer is not yet installed or validated.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| MSV-01 | Deliver real description list/detail UI | VER-01, WS-02 | A real sample shows correct layer shapes, tensor edges, and specification variables with loading/error states. |
| MSV-02 | Evaluate and wrap the network renderer | MSV-01 | Show stable IDs, external selection, node callbacks, resize, worker/assets, and browser findings; document a fallback if the candidate fails. |
| MSV-03 | Validate specification drafts | MSV-01, MSB-03 | Invalid variable mappings are explained; a valid change creates a new reference and cannot mutate an existing run. |

Owner: **C**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Layer ID/shape agree across the graph, detail view, and ACT description.
- Normalization and output-constraint variable mapping are correct; unsupported input retains an explanation.
- Graph selection and programmatic navigation synchronize without recursive selection events.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Open model/spec | Choose an uploaded artifact or allowed server artifact. | Display graph/constraint metadata, source identity, and capability warnings. |
| Inspect a layer | Select a network node or use an external navigation action. | Graph and detail panel resolve the same layer/tensor IDs. |
| Prepare a run input | Edit a supported specification draft and validate it. | Validation produces a new immutable specification reference; an existing run remains unchanged. |

### Processing Flow

1. Resolve an artifact reference through the application query entry point.
2. Render a list/detail view from ModelDescription/SpecDescription before introducing a graph renderer.
3. Build renderer data with a reversible layer-ID mapping; keep vendor-specific fields local.
4. Send selection to workspace; submit validated input references to the run-creation use case.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `loadDescription(modelRef, specRef) → DescriptionViewModel` | Uses the shared query gateway; does not parse ACT objects in the browser. |
| `toNetworkGraph(description) → RendererGraph` | Pure renderer conversion with stable layer/tensor mapping. |
| `validateSpecDraft(draft, modelRef) → ValidationResult` | Requests ACT-backed validation through the service; returns field-level errors or a new spec reference. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `ModelSpecView.tsx` | Input selection, metadata, constraint detail, and validation feedback. |
| `view_model.ts` | Description-to-view transformations and identity maps. |
| `network_renderer.ts` | Model Explorer integration only after its spike passes. |
| `model_spec.test.tsx` | User selection, unsupported specifications, and draft immutability. |

### State, Failure, and Recovery Rules

A renderer failure retains a usable description table. Unsupported specification types remain visible with their actual representation and a reason, rather than being converted to a supported box.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
