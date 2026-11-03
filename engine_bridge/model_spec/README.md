# Model and Specification Adapter

**Status:** first version: `describe.py` (MSB-01..03 for JSON nets with box INPUT_SPEC); parity tests in `../test_bridge.py`; A review pending. **Owner:** B; A reviews scientific mapping.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Obtain accurate, stable, read-only model/specification descriptions from ACT for workbench consumption.

| Subproblem | Responsibility |
| --- | --- |
| Loading | Parse models/specifications through supported ACT entry points, not a separate parser with different semantics. |
| Mapping | Layer/tensor IDs, DAG connections, variable mapping, shape/dtype, input domains, and output constraints. |
| Boundaries | Distinguish model snapshots from native handles and metadata from large weight artifacts. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not emit Model Explorer-specific formats, compute graph layout, or silently replace unsupported specifications.

## 3. Inputs, Outputs, and State

- **Inputs:** Valid SessionHandle, permitted model/specification sources, and loading parameters.
- **Outputs:** ModelDescription, SpecDescription, stable IDs/provenance, and LoadError/Unsupported results.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Adapter and anti-corruption layer.** Translate changing ACT representations into stable integration descriptions so GUI code does not track internal object changes.

**Immutable snapshots.** Bind descriptions to source hashes and do not expose mutable tensors or caches.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Uses engine_session, shared contracts, and native ACT loading/description capabilities. Does not depend on inspection or GUI modules.

Start with one mapping module using neutral types. The workbench separately encodes the wire schema.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| MSB-01 | Define neutral descriptions against a real sample | ES-01, BASE-03 | Field map covers DAG, layer/tensor identity, shapes, provenance, and required spec semantics; A reviews it. |
| MSB-02 | Implement model loading and mapping | MSB-01, ES-02 | Repeated reads of one snapshot preserve IDs and match native ACT connectivity/shape; no mutable tensor escapes. |
| MSB-03 | Implement spec loading and validation | MSB-02 | Real input-domain/output-constraint mapping matches ACT; invalid variables and unsupported representations have explicit errors. |

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- Connections, shapes, variables, and normalization agree with native ACT.
- Repeated reads of a snapshot preserve identity.
- Invalid or unsupported inputs have explicit errors; descriptions contain no raw ACT objects.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Load a model | Given an allowed artifact source and active session. | Use ACT loading and return a model handle plus an immutable structural description. |
| Load/validate a specification | Given a model reference and specification data/source. | Preserve domains, constraints, variable mapping, normalization, and unsupported reasons. |
| Describe without payload inflation | Request model/spec metadata. | Provide stable IDs and artifact references without dumping all weights or mutable ACT caches. |

### Processing Flow

1. Resolve the workbench-provided source into an ACT-supported loader input.
2. Invoke ACT loading/validation and capture the source hash and engine baseline.
3. Map DAG/layer/tensor identity and specification variables into neutral descriptions.
4. Retain native handles inside their owner process; expose metadata/artifact references only.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `loadModel(session, source) → ModelHandle + ModelDescription` | Stable IDs are scoped to a model snapshot. |
| `loadSpec(session, modelHandle, sourceOrDraft) → SpecDescription` | Use ACT validation; preserve unsupported types rather than coercing them. |
| `describeModel(modelHandle) → ModelDescription` | Read-only mapping; no renderer-specific fields or raw ACT objects. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `adapter.py` | ACT loader/validator mapping and immutable description conversion. |
| `mapping.py` | Add if graph/spec mapping becomes independently complex. |
| `test_mapping.py` | Native parity, stable identity, unsupported inputs, and immutable descriptions. |

### State, Failure, and Recovery Rules

Changing source content produces a new snapshot identity. A renderer namespace or filename is not a stable model identity. Native file loading is restricted to sources already admitted by the workbench, not arbitrary paths generated by AI.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
