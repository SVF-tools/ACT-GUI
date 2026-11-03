# Records and Replay

**Status:** first version: `store.py`, `RecordsView.tsx` (REC-01; REC-02/03 partial: lifecycle events, recovery, replay; REC-04 export only). **Owner:** B; D/C integrate figure and data export.
Follow the [repository rules](../../AGENTS.md) and [parent scope](../README.md).

## 1. Subproblems and Objective

Persist traceable runs and AI actions, supporting queries, replay, and reproducible exports.

| Subproblem | Responsibility |
| --- | --- |
| Commit | Persist snapshots, events, artifacts, and recoverable commit positions without referencing unpublished files. |
| Coverage | Record which node/layer/revision states are retained; distinguish absent, not recorded, and corrupted data. |
| Replay | Reconstruct recorded state from snapshots and events; support retrieval after disconnection. |
| Export | Fix context, numerical data, plot settings, and version provenance; delegate rendering to the owning view. |

## 2. Scope and Non-goals

Own the behavior above and its failure/availability states. Deliver it incrementally using the sequence below; the full scope is not a first-slice requirement.

Does not restore solver memory, recompute missing history, manage browser selection, or decide algorithm state.

## 3. Inputs, Outputs, and State

- **Inputs:** Committed verification state/events, inspection artifacts, AI action records, and export requests.
- **Outputs:** Snapshot/event queries, artifact reads, coverage, run bundles, and fixed data/plot configurations.
- State, absence, and scientific semantics follow the [architecture](../../docs/design.md). Type names here describe intended contracts, not existing APIs.

## 4. Design Patterns and Rationale

**Repository and atomic commit.** Start with one local store behind small read/write interfaces, not a distributed storage platform.

**Snapshots and appended events.** Persist committed order with idempotent append and explicit gaps. A general event-sourcing framework is unnecessary.

**Immutable artifacts and manifests.** Associate data by IDs/hashes. Use relative artifact references instead of private absolute paths in bundles.

Use small interfaces, pure functions, or ordinary classes. A pattern name alone does not justify adding a framework.

## 5. Dependencies and Implementation Placement

Depend on shared record types and storage interfaces, not ACT, model providers, or rendering components. Inject a renderer into export workflows when needed.

Start with storage.py and the formats actually needed. Do not introduce a database before there is a recording use case.

Add code and focused tests in this module as implementation proceeds. Keep language/runtime boundaries explicit. No installation or test commands exist yet.

## 6. Implementation Plan

All tasks are **Planned**. IDs identify reviewable implementation slices; dependencies are completion prerequisites, not code-import instructions. Fixture-based work may proceed earlier against an agreed contract, but it does not satisfy real-integration acceptance.

| ID | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| REC-01 | Persist immutable run metadata and final result | BASE-03 | Save/read a manifest and artifact for the native ACT run recorded in BASE-03 with identical hashes; no private absolute paths are required in a bundle. |
| REC-02 | Persist commit batches and snapshot boundaries | REC-01, EVT-02 | A simulated interrupted write recovers the last committed prefix; incomplete references are never visible. |
| REC-03 | Implement replay, coverage, and resync reads | REC-02 | Snapshot S plus following events reproduces recorded state; missing/expired history is explicitly represented. |
| REC-04 | Export fixed research data and figure configuration | REC-03, ANA-02 | Export/import preserves numerical data, selected coordinates, guarantees, revision, and plot configuration; invalid bundle paths are rejected. |

Owner: **B**. A reviews scientific semantics; use the team-role mapping in the [development plan](../../docs/plan.md). There are no implied calendar estimates.

Missing ACT interfaces require linked ACT issues/changes owned by A. Record the required capability and engine PR before marking the corresponding GUI integration task complete.

## 7. Acceptance and Tests

- After a crash, recover the last committed state without referencing partially written artifacts.
- Duplicate events do not duplicate records; sequence gaps are explicit.
- Reject path traversal in bundles, do not treat missing history as zero, and trace exported data to its original source.

On completion, provide real samples, commands actually run, results, and unverified items, then update this document's status. See the [development plan](../../docs/plan.md).

## 8. Future Extraction Criteria

Split internal files/directories when independent evolution, reuse, or size warrants it. This README owns this module's subproblem and design details; the parent retains summary and navigation.

## 9. Functional Implementation Specification

**Design proposal:** the interfaces and file names below are implementation targets, not existing code or ACT APIs. Add them only with the task that uses them. The task table above owns delivery status.

### Feature Behavior

| Feature | Trigger | Observable result |
| --- | --- | --- |
| Save a run | Persist configuration, result, committed events, and selected artifacts. | Store provenance and coverage with a recoverable commit position. |
| Reopen or reconnect | Request a snapshot and events after its covered sequence. | Return a consistent boundary; expired history requires an explicit resync rather than silent loss. |
| Export research evidence | Export a stage/comparison/run bundle. | Include data, plot settings, revision, method/guarantee, and version provenance; validate imported bundles. |

### Processing Flow

1. Write a new artifact to a temporary file, validate it, then publish it atomically.
2. Commit event/index references only after all referenced artifacts are available.
3. Associate snapshots with a committed event boundary; recover only the committed prefix after a crash.
4. Read through a repository interface for live/history modes; report coverage and corruption separately.
5. Export relative artifact references and a manifest; reject path traversal and size-limit violations on import.

### Proposed Public Operations

| Operation | Contract and responsibility |
| --- | --- |
| `createRunRecord(manifest) → RecordRef` | Initial immutable inputs/provenance; no solver-state claim. |
| `appendCommit(runId, batch, artifactRefs) → CommitPosition` | Idempotent by committed batch identity; all references must be readable. |
| `readSnapshot(runId, atSeq?) / readEvents(runId, afterSeq)` | Consistent boundary and explicit retention/coverage response. |
| `readArtifact(id) / exportBundle(query, plotConfig)` | Validate integrity and preserve provenance; render through an injected view renderer. |

### Planned Files

Paths are relative to this module; none of these implementation files exists yet. Keep the public API small and add implementation/testing files with the feature, without further directory scaffolding.

| File | Responsibility |
| --- | --- |
| `repository.py` | Small storage interface and first local implementation. |
| `commit_log.py` | Committed positions, snapshot index, and recovery. |
| `bundle.py` | Manifest, integrity, import/export, and relative references. |
| `test_records.py` | Crash recovery, duplicate batches, missing files, and traversal rejection. |

### State, Failure, and Recovery Rules

Persistence failures must be visible as recording failure/degradation, not silently reported as a complete recording. Do not claim an engine rollback merely because storage failed. Orphan published artifacts can be cleaned only after checking committed references. Replay never executes imported commands.

### Task Completion Record

For each completed task, attach its implementation PR, fixture/input provenance, exact commands and results, any ACT/provider dependency, and remaining capability limitations. Update status here only after the stated evidence exists. Tests mentioned in this document remain planned until then.
