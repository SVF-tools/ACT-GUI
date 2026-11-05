# Shared Integration Contract

**Status:** design draft, not an implemented schema. **Owner:** B; A reviews scientific semantics.

## Scope

Define shared bridge data semantics and failure boundaries. HTTP routes and Model Explorer formats are outside this contract. Start with small type definitions such as contracts.py when implementation requires them; no additional package or plugin framework is needed.

## Minimum Data Vocabulary

| Data | Required semantics |
| --- | --- |
| EngineInfo / Capabilities | ACT commit/API, supported methods/specifications/operations, limitations |
| Session/Model/RunHandle | Identity, lifetime, execution environment; native handles are not browser objects |
| Model/SpecDescription | Snapshot provenance, stable layer/tensor IDs, DAG, variables/constraints, shape/dtype |
| Context | run/node/revision/layer/stage/projection and applicability; batch lane is not node identity |
| Bound / Geometry | Objective, direction, computed/inherited origin, method, precision, coordinates/projection, guarantee, provenance |
| Availability | available/pending/not_recorded/unsupported; missing data is not zero |
| Command / Receipt | command_id, target, revision precondition, parameters, actual applied/rejected state; acceptance is not application |
| Event | Run, sequence, revision, batch, kind, coverage; scientific state must be committed |
| Error | Code, explanation, retryability; an error does not substitute for a scientific verdict |

## Design Patterns

Neutral types and immutable descriptions isolate mutable ACT objects. Structured errors represent expected failure explicitly. Workbench services map these types to their wire schema; bridge definitions do not import visual_bench. Browser contracts are generated from the workbench Pydantic source.

Cross-process payloads require explicit serialization; native solver/GPU pointers cannot be assumed transferable. At JSON boundaries, define valid encodings for Infinity and large integer IDs rather than emitting invalid JSON or losing precision.

## Implementation and Acceptance

Define engine_session/model_spec fields and real samples first. Add execution, inspection, and events with their features. Each change updates adapters, workbench mappings, and tests together.

Verify semantics, absence states, numerical encoding, incompatible versions, and generated-type drift. Concrete signatures are established during implementation; this document does not assert that a proposed API already exists in ACT.
