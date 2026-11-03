# Visual Bench Scope

**Status:** first version: service (`server.py`, `schemas.py`) and browser (`app.tsx`) run on localhost (see [plan status](../docs/plan.md#first-version-status)). **Owner:** C owns interaction and product consistency; B owns application services and AI orchestration; D, when available, owns visualization and test integration.

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

Each of the seven modules has a README covering its subproblems, patterns, implementation sequence, and acceptance criteria. There are no application implementations or deeper component scaffolds yet.

| Module | Scope | Main inputs/outputs | First delivery |
| --- | --- | --- | --- |
| [workspace](workspace/README.md) | Layout, research context, selection, linked panels | User selection → model/spec/run/node/layer/revision context | Basic page and selection |
| [model_spec](model_spec/README.md) | Network/layer/specification inspection and input drafts | Engine descriptions → views and explicit model/spec references | Real-data inspection |
| [verification](verification/README.md) | Application use cases, tasks/workers, query/command entry points, results | User/AI requests → bridge calls, run_id, committed state, receipts | First real run |
| [bab](bab/README.md) | Search tree, local subtrees, paths, node details, branch actions | Nodes/edges/events → selection and commands via verification | BaB observability |
| [analysis](analysis/README.md) | Propagation, bounds/set views, node/method/experiment comparisons | ACT numerical/geometry data → views with coordinates, guarantees, and provenance | Inspection integration |
| [assistant](assistant/README.md) | Context, provider, explanations, plans, tools, interaction | Frozen context/questions → evidence, plans, navigation, use-case requests | Real-node read-only explanations |
| [records](records/README.md) | Snapshots/events/artifacts, experiment index, replay, exports | Committed records and fixed queries/plot settings → traceable bundles | First saved run |

### State Ownership and Shared Entry Points

workspace owns user selection and layout. verification owns current tasks and commands. ACT owns scientific state. records persists committed records. Panels consume one run-state projection rather than maintaining independent scientific-state copies.

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

Introduce thin app.tsx and server.py composition roots when implementation starts. Keep feature code in its owning module without duplicating web/service subtrees everywhere. TypeScript does not import Python; Python use cases do not depend on React. Validate build and packaging choices during bootstrap.

The service maps neutral bridge data to wire schemas. The browser uses generated contracts and does not access ACT. Provider credentials/calls remain in the service. The workbench manages task/worker lifecycle and records; worker ACT calls go through the bridge, and ACT defines scientific commit points.

## First-slice Acceptance

Load a small real ACT model/spec through the bridge and display structure, constraints, provenance, and error states. Full docking and AI are not first-slice requirements. Then deliver layer/stage selection → evidence query → AI explanation → navigation on a completed run, extend it to committed BaB nodes, and follow with supported execution plans.

During development the workbench is opened in a local browser at the localhost URL printed by the BASE-02 development commands. Tests grow with implementation. No startup commands, application test results, or platform compatibility certification exist yet.

## Maintenance

Keep overall ownership here and detailed behavior in module READMEs. See [architecture](../docs/design.md), [plan](../docs/plan.md), and [rules](../AGENTS.md). Update scope when ownership or integration boundaries change; keep renderer internals with their code.
