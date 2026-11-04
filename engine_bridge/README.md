# Engine Bridge Scope

**Status:** first version: all five modules have code (see [plan status](../docs/plan.md#first-version-status)). **Owner:** B for engine_session, model_spec, and execution; A for inspection and events and reviews ACT interfaces and scientific semantics. The ACT engine itself remains in its separate repository.

## Purpose

Expose ACT capabilities through a stable, testable, GUI-independent integration contract, isolating the workbench from internal engine objects and version differences.

## Responsibilities

- Detect ACT versions/capabilities and adapt supported interfaces.
- Convert model/spec descriptions, stable identities, and provenance.
- Invoke runs, queries, and supported controls; report real results and errors.
- Adapt committed engine observations, preserving revision/sequence, identity, and proof semantics without exposing pre-rollback state.
- Read bounds/geometry/artifacts on demand without leaking mutable objects or treating batch lanes as node IDs.
- Compare integration behavior against native ACT results.

## Modules

Five modules have scope READMEs. Shared integration semantics live in contracts.md rather than a separate package. Add implementation with actual tasks; these are not independent services.

| Module | Scope | Main inputs/outputs | First delivery |
| --- | --- | --- | --- |
| [engine_session](engine_session/README.md) | Engine binding, environment/version checks, capabilities, resource handles | ACT configuration → engine information, capabilities, handles, diagnostics | First slice |
| [model_spec](model_spec/README.md) | ACT loading/inspection and stable descriptions | Model/spec sources → graph, shapes, variable/constraint mapping, IDs | First slice |
| [execution](execution/README.md) | Verification and supported controls | Configuration/preconditioned commands → run handles, verdicts, receipts/errors | Real run; controls later |
| [inspection](inspection/README.md) | Context-specific node/layer/bound/geometry reads | Context/projection request → provenance-bearing data and availability | Node/layer analysis |
| [events](events/README.md) | Committed node/wave/run observations | ACT observations → normalized events, ordering, coverage | BaB observability |

Shared [contracts](contracts.md) define descriptions, handles, events, command preconditions, and errors; `contracts.py` holds them as frozen dataclasses (no ACT objects, no tensors, no workbench types). Workbench Pydantic schemas own HTTP/SSE encoding; the service maps bridge data without creating a reverse dependency or a second handwritten browser protocol.

### Boundaries and Missing Capabilities

engine_session manages engine bindings and handles. visual_bench.verification manages worker scheduling/restarts and user run lists; do not create two process managers.

execution invokes and reports supported operations without selecting a search strategy or computing a verdict. ACT owns final operation validity. inspection may request new ACT-generated artifacts, but recomputation must retain new provenance rather than impersonating historical data.

events adapts committed observations; the workbench handles browser SSE connections and records handles persistence. If ACT provides only wave summaries, report that coverage. Detailed node history or controls require ACT interfaces; the bridge must not simulate them as supported.

### Acceptance Overview

Test incompatible/unavailable engines, native model/spec parity, results and command preconditions, inspection context/provenance/availability, and committed-event identity/order/rollback. Tests do not require a browser or AI provider; engine/solver requirements depend on the tested capability.

Layer propagation data requirements live in [inspection](inspection/README.md).

### Files and Usage

Each module is a package with a public `__init__.py`, implementation files, and its parity tests (`test_*.py`) next to them; the module README lists them. Shared files at this level:

| File | Responsibility |
| --- | --- |
| `contracts.py` | Neutral bridge data types and `BridgeError`. |
| `contracts.md` | Contract semantics and open design items. |
| `testing.py` | Test helpers: the pinned catalog, `model_path`, `native_net`, `require_sources`. |

Run all bridge tests with `.venv/bin/python -m pytest engine_bridge` (needs the pinned ACT checkout; no browser or AI provider). When ACT changes, update the adapter in the owning module, its parity test, and the capability list in `engine_session/session.py`, then re-check the workbench service that consumes it.

## Non-goals

- Do not copy ACT algorithm implementations or implement a verifier, bounds, projections, or search strategies here.
- Do not own HTTP routes, layout, graph coordinates, user sessions, AI providers, plan orchestration, or general record storage.
- Do not claim complete node history from a summary trace or invent pause/step capabilities.

## Inputs and Outputs

Inputs are model/spec sources, run configurations, precise queries, and preconditioned controls. Outputs are neutral descriptions, capabilities, run handles, scientific results with provenance, committed events, and structured integration errors.

Preserve objective/scope, numerical direction, computed/inherited origin, method, precision, and provenance. Do not recompute engine verdicts. Validate actual capabilities and target preconditions before ACT validates/applies an operation at its safe boundary.

## Dependencies and Implementation Placement

The dependency direction is visual_bench → engine_bridge → ACT. Only this area directly depends on ACT. Start with the necessary adapter code and neutral descriptions; validate packaging during the first implementation slice rather than introducing a multi-engine plugin system.

The bridge does not start a Web service. Workbench services/workers import it; the workbench owns long-running process lifecycle.

## First-slice Acceptance

Pin an ACT commit/environment and read a small real network/spec. Verify IDs, shapes, variables, and missing-data semantics against native ACT, including errors and unsupported cases. Do not expose mutable tensors. Exercise the integration without a browser or model provider.

## Maintenance

Update capability/version/semantic changes together with tests and workbench mappings. See [architecture](../docs/design.md), [plan](../docs/plan.md), and [rules](../AGENTS.md).
