# Visual Bench Scope

**Status:** first version: service (`server.py`, `workbench.py`) and browser (`app.tsx`) run on localhost; restructured into module slices on 2026-11-04 (see [plan status](../docs/plan.md#first-version-status)). **Owner:** C owns interaction and product consistency; B owns application services and AI orchestration; D, when available, owns visualization and test integration.

## Purpose

Provide a complete interactive environment connecting networks, specifications, verification state, BaB, approximation sets, and AI plans within one research context.

## Responsibilities

- Research context: selected model/spec/run/node/layer/revision and linked views.
- Visualization: networks, specifications, search, layer bounds/geometry, experiments, and research figures.
- Operations: runs, queries, inspection, capability-gated controls, plans, and execution receipts.
- AI collaboration: context assembly, evidence-based explanations, provider integration, tools, and action records.
- Application state and persistence: requests, snapshots/events, reconnect, replay, import, and export.
- Product delivery: layout, errors, accessibility, browser compatibility, service configuration, and distribution entry points.

A feature may include both browser presentation and service-side use cases.

## Modules

Each of the nine modules has a README covering its subproblems, current files and usage, patterns, implementation sequence, and acceptance criteria.

| Module | Scope | Main inputs/outputs | First delivery |
| --- | --- | --- | --- |
| [workspace](workspace/README.md) | Layout, research context, selection, linked panels | User selection → model/spec/run/node/layer/revision context | Basic page and selection |
| [model_spec](model_spec/README.md) | Network/layer/specification inspection and input drafts | Engine descriptions → views and explicit model/spec references | Real-data inspection |
| [verification](verification/README.md) | Run lifecycle: start/stop, worker supervision, run state, SSE events, verdict banner | User/AI run requests → run_id, committed events, results | First real run |
| [fuzzing](fuzzing/README.md) | ACTFuzzer options, live/recorded fuzzing views, saved counterexamples and export | Fuzz runs and their records → Fuzzing mode, VNN-LIB/PNG exports | Live fuzzing demo |
| [engine](engine/README.md) | ACT engine status, engine gate for other services, Gurobi license | Bridge probe, license uploads → status badges, Engine tab, worker env | Engine diagnostics |
| [bab](bab/README.md) | Search tree, local subtrees, paths, node details, branch actions | Nodes/edges/events → selection and commands via verification | BaB observability |
| [analysis](analysis/README.md) | Propagation, bounds/set views, node/method/experiment comparisons | ACT numerical/geometry data → views with coordinates, guarantees, and provenance | Inspection integration |
| [assistant](assistant/README.md) | Context, provider, explanations, plans, tools, interaction | Frozen context/questions → evidence, plans, navigation, use-case requests | Real-node read-only explanations |
| [records](records/README.md) | Snapshots/events/artifacts, experiment index, replay, exports | Committed records and fixed queries/plot settings → traceable bundles | First saved run |

### Module Slice and Shared Layers

Every module follows the same file pattern ([design section 3](../docs/design.md#3-runtime-and-implementation-boundaries)): `schemas.py` (wire payloads) → `service.py` (use cases; the only caller of engine_bridge and records for this module) → `routes.py` (HTTP) on the service, and `api.ts` (endpoints) → `hooks.ts` (TanStack Query) → views in the browser, with tests next to them. One contributor can own a module without touching another module's files.

| Root file | Responsibility |
| --- | --- |
| `server.py` | FastAPI app: error rendering, `/api/health`, includes each module's router, serves the production build. |
| `workbench.py` | Builds the module services and wires their constructor dependencies; the assistant and routes use the same instances. |
| `schemas.py` | Re-exports every module's payloads and lists `WIRE_MODELS` for `npm run gen:types` (never add models here; add them in the module). |
| `wire.py`, `errors.py`, `config.py` | Shared service kernel: wire primitives (`Wire`, `WireNumber`, `ErrorBody`), `AppError`, paths and `ACT_GUI_*` settings. |
| `conftest.py`, `testing.py` | Shared test fixture (`client`) and helpers (`follow_to_end`, `sources_or_skip`). |
| `app.tsx`, `main.tsx` | Browser composition root (layout, selection, mode registry) and the `QueryClientProvider`. |
| `generated/wire.ts` | Generated browser types; do not edit. |

#### Shared browser layer

`shared/` imports no feature module: `http.ts` (`call`, `ApiError`, `followRun` SSE), `wire.ts` (`num`, `fmt`, `indexRanges`), `queryClient.ts` (the `QueryClient` and the `keys` factory: run projections are keyed under `["runs", "detail", id]`, so one committed run event refreshes the run, its fuzzing record, layers, coverage, and records views), and `ui/` (`Empty`, `StopButton`, image rendering).

### State Ownership and Shared Entry Points

workspace owns user selection, layout, and the mode registry. verification owns runs and run commands. ACT owns scientific state. records persists committed records. Panels consume server data only through TanStack Query (one cache, keyed by run), never through private copies or refresh counters.

verification exposes application queries and commands backed by the bridge. bab, analysis, and assistant use these entry points. Pure navigation stays within workspace.

BaB layout/expansion are display state; actual node resolution comes from ACT. analysis prepares views, while ACT performs scientific projections, bound calculations, and proof evaluation.

assistant uses the same entry points and does not directly modify engine state or records. AI session events remain distinct from ACT run events. records stores plot data/settings and coordinates export; the owning view renders the figure.

### Acceptance Overview

Test stale selection responses in workspace; variable/layer mapping in model_spec; lifecycle, failure, and idempotency in verification; identity/events in bab; provenance/coordinates/guarantees in analysis; evidence/capabilities/failures in assistant; and availability/replay/export provenance in records.

Detailed propagation navigation, set views, playback, and comparison requirements live in [analysis](analysis/README.md).

## Non-goals

- Do not implement verification algorithms, bound solving, or scientific projections, or infer verdicts from pictures or model-generated text.
- Do not access ACT tensors/frontiers directly or handle internal ACT version differences.
- Do not treat display state as engine state or replay as solver checkpoint recovery.

## Inputs, Outputs, and State

Inputs are user intent and engine_bridge descriptions, capabilities, committed results/events, and artifacts with provenance. Outputs are views, explanations, evidence, receipts, and validated queries/commands with explicit targets and revision preconditions.

Owned state includes selection, layout, plans, requests, and record indexes. Scientific state is recorded or projected, never independently inferred. Bind queries and evidence to their original context; distinguish accepted from applied.

The workbench manages authorization scope, budgets, and idempotency. engine_bridge/ACT additionally validate actual capabilities and current engine preconditions.

## Dependencies and Implementation Placement

visual_bench uses the bridge's GUI-independent integration contract. The bridge does not import visual_bench.

`app.tsx`, `server.py`, and `workbench.py` stay thin composition roots. Keep feature code in its owning module without duplicating web/service subtrees everywhere. TypeScript does not import Python; Python use cases do not depend on React. Validate build and packaging choices during bootstrap.

The service maps neutral bridge data to wire schemas. The browser uses generated contracts and does not access ACT. Provider credentials/calls remain in the service. The workbench manages task/worker lifecycle and records; worker ACT calls go through the bridge, and ACT defines scientific commit points.

## First-slice Acceptance

Load a small real ACT model/spec through the bridge and display structure, constraints, provenance, and error states. Full docking and AI are not first-slice requirements. Then deliver layer/stage selection → evidence query → AI explanation → navigation on a completed run, extend it to committed BaB nodes, and follow with supported execution plans.

During development the workbench is opened at the localhost URL printed by `scripts/dev.sh`. Tests: `.venv/bin/python -m pytest visual_bench` (or one module directory) and `npm test`. No platform compatibility certification exists yet.

## Maintenance

Keep overall ownership here and detailed behavior in module READMEs. See [architecture](../docs/design.md), [plan](../docs/plan.md), and [rules](../AGENTS.md). Update scope when ownership or integration boundaries change; keep renderer internals with their code.
