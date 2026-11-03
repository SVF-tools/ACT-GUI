# Inspection Adapter

**Status:** design specification; not implemented. **Owner:** B; A owns layer-state and projection semantics.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Read node, layer, and set evidence under an exact context for propagation views and AI queries.

| Subproblem | Responsibility |
| --- | --- |
| Addressing | Map run/node/revision/layer/stage to DAG input/output tensors. |
| Data | Expose before/after bounds, constraints/geometry, coordinates, and guarantees. |
| History | Distinguish current data, recordings, unrecorded/unsupported data, and newly computed results. |
| Cost | Use on-demand reads, paging, and artifact references; declare concurrent-read and additional-inspection capabilities. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not recalculate scientific results itself, invent intermediate animation stages, or recover unrecorded historical tensors.

## 3. Inputs, Outputs, and State

- **Inputs:** Session/RunHandle, node/layer/revision, and projection/stage requests.
- **Outputs:** Node/LayerInspection, GeometryArtifact references, provenance/method/precision, and availability.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Immutable query context.** Fix identity/version in the request and echo it in responses so callers can reject stale data.

**On-demand artifacts.** Separate metadata from large payloads and avoid loading unrequested layers.

**Availability union.** Represent available/pending/not_recorded/unsupported distinctly instead of returning empty arrays for every case.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Uses engine_session/model_spec/contracts and ACT read/inspection interfaces. Reading mutable live state must respect ACT safe boundaries.

Start with read-only layer queries. Missing ACT capabilities require corresponding engine work.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| INSP-01 | Expose fixed-run layer states | EXE-02, MSB-03 | A small real network yields correctly mapped before/after data for input through output; absent stages are explicit. |
| INSP-02 | Expose geometry and projection metadata | INSP-01 | Coordinates, representation, guarantee, method, dtype/tolerance, and source are present; interval-only data is not upgraded into fabricated geometry. |
| INSP-03 | Define historical availability and new inspection semantics | INSP-01, REC-02 | Integration with retained records distinguishes old evidence, missing history, and recomputation; new inspection data never overwrites original historical provenance. |

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Responses match the requested run/node/revision or explicitly reject/report unavailability.
- Inherited origins, projection coordinates, guarantees, and tolerances are preserved.
- Interval-only input stays interval-only; recomputation is never labeled as an original historical artifact.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Data Required by Propagation Views

The goal is queryable layer state. These are integration requirements to agree with ACT, not claims that ACT currently exposes every field.

- **Identity and context:** run_id, node_id where applicable, revision, model/spec references, layer_id, stage_id, and input/output tensor mapping.
- **Stage semantics:** operator, analysis method, and before/after bounds. Preserve finer ACT-provided stages and their order; do not invent intermediates.
- **Geometry:** optional set representations/constraints, coordinates or projection definition, guarantee, and artifact reference. Interval-only data must not become a supposedly more precise polygon.
- **Provenance and availability:** computed/inherited origin, precision/tolerance, available/pending/not_recorded/unsupported, and whether this is a new inspection.

model_spec supplies the network DAG and tensor connectivity. Use them to locate stages; do not silently flatten a DAG into one sequential chain.

Load selected layers/stages lazily. Do not require every run to retain every tensor for every node. Declare fine-grained recording support, retention coverage, and additional computation cost.

ACT performs scientific transformations, bounds, and projections. The bridge requests and converts data; visual_bench navigates and renders stages. Regression checks cover tensor/stage mapping, before/after semantics, projection/guarantee, and absent history so a seemingly continuous display cannot combine unrelated contexts.

## 10. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Read layer state | Request a specific run/layer/revision and optional search node. | Return ACT before/after values and exact tensor/stage mapping, or an explicit unavailable result. |
| Request geometry | Choose coordinates/projection and supported representation. | Return ACT-computed geometry with coordinate and guarantee metadata; large payloads use references. |
| Inspect history | Request a historical revision. | Report retained data or not_recorded; a new computation has a new inspection identity and provenance. |

### Processing Flow

1. Validate handle, target context, capability, requested coordinates, and method.
2. Use a stable ACT read/commit boundary; reject or queue a read that would race mutable state.
3. Map bounds and optional geometry, preserving computed/inherited origin and precision.
4. Return the echoed context and a discriminated availability result; represent extra computation as pending/new inspection.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `queryLayer(runHandle, context) → LayerInspectionResult` | Mandatory context includes requested stage/tensor semantics; no silently substituted current revision. |
| `queryNode(runHandle, nodeRef) → NodeInspection` | Identity and bound origins are preserved independently of batch layout. |
| `requestProjection(context, projectionSpec) → GeometryResult or PendingInspection` | Scientific computation remains in ACT; returned metadata identifies the exact projection. |
| `queryHistorical(context) → InspectionAvailability` | This does not promise access to unrecorded ACT state. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `adapter.py` | ACT state lookup, availability, and result conversion. |
| `projection.py` | Thin request adapter only when ACT exposes projection capability. |
| `test_inspection.py` | Context/mapping/provenance and historical availability checks. |

### State, Failure, and Recovery Rules

REC-02 is a cross-module acceptance dependency, not permission for bridge code to import records. The workbench combines record retrieval with engine availability. Engine reads and extra GPU computation are serialized/queued when ACT cannot support safe concurrent access.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
