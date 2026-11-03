# Architecture Baseline

**Date:** 2026-11-03. ACT-GUI is the AI-native visualization and interaction interface for the ACT engine.

The primary boundaries are visual_bench, engine_bridge, and docs. FastAPI/React and browser/service processes are implementation details within those boundaries. This repository currently contains scope and design documents only. Earlier comprehensive blueprints remain references, not a requirement to create every planned directory.

## 1. Product Boundaries

```text
ACT-GUI
  Visual Bench: research context, views, operations, records, AI collaboration
       | integration contract
  Engine Bridge: ACT compatibility, capability adaptation, and invocation
       |
ACT engine: separate repository
```

The workbench is one product, from input inspection to results. ACT owns scientific computation and verification verdicts. engine_bridge is a focused integration boundary; application orchestration, records, and AI logic belong to visual_bench.

## 2. Structure and Scope Ownership

The root contains README.md, AGENTS.md, LICENSE, and .gitignore. The two product areas each have a parent README and one level of module READMEs. docs contains its README, this architecture document, and the development plan.

See [Visual Bench](../visual_bench/README.md), [Engine Bridge](../engine_bridge/README.md), and [Documentation](README.md).

- visual_bench: workspace, model_spec, verification, bab, analysis, assistant, records.
- engine_bridge: engine_session, model_spec, execution, inspection, events, plus a shared contracts.md.

The twelve modules have scope documents, not implementations. Parent READMEs own summaries and navigation; module READMEs own subproblems, patterns, feature behavior, proposed operations/files, dependency-linked implementation tasks, and acceptance evidence.

The two model_spec modules have distinct roles: visual_bench presents descriptions and input drafts; engine_bridge loads through ACT and converts engine descriptions. Both use the same source data without duplicating scientific processing.

A typical query flows from workspace node selection through the verification query entry point to engine_bridge.inspection and ACT, then back to analysis/bab. AI uses that same entry point. Committed ACT changes flow through bridge.events into verification/records before updating views.

## 3. Runtime and Implementation Boundaries

The first code slice may introduce thin app.tsx and server.py composition roots in visual_bench. Module-specific TypeScript and Python code belongs in the corresponding module. Do not repeat web/service directories inside every module. Build and Python packaging configuration must be validated during bootstrap; these files do not exist yet.

The browser uses HTTP queries/commands and SSE events. The service calls engine_bridge; long computations execute in a separate worker. HTTP routes and AI tools reuse ordinary application use cases.

Workbench Pydantic schemas are the sole handwritten source for wire types, generating browser clients/types and event validators. REST OpenAPI alone does not define the event payload contract. The service maps neutral bridge data to the wire format; bridge code does not depend on upper-layer API schemas.

Service startup, configuration, records, and AI providers belong to visual_bench. ACT invocation and version differences are isolated in engine_bridge. Worker lifecycle is managed by the workbench; ACT calls inside the worker go through the bridge.

Start with a small real-data inspection slice. Propagation requirements live in analysis/README.md; no deeper propagation directory is needed yet. Keep tests near their modules, add cross-module E2E when a complete flow exists, and add deployment infrastructure when shipping. Do not prebuild shared packages, multi-engine plugins, or separate agent services.

## 4. Data and Execution Invariants

- Bind queries to run/node/layer/revision. A late response must not replace a newer selection.
- Keep node identity separate from batch lane indices. Bounds retain scope, direction, computed/inherited origin, method, and provenance.
- Geometry states its coordinates, representation, projection, and guarantee. Samples are not sound outer approximations; a local visualization does not establish a global verdict.
- Fix model/spec/config snapshots for a run. Changes create another run.
- Publish scientific state only after ACT commits it. Snapshots and ordered events support reconnect/replay with explicit duplicate, gap, and rollback handling.
- Replay reconstructs recorded display state, not solver memory. Missing historical bounds are not_recorded.
- Commands check capabilities, expected_revision, and idempotency. Distinguish accepted from applied. Enable pause/step/split only when ACT supports the stated semantics.
- Fetch large tensors and detailed tree data on demand instead of streaming everything.

## 5. First AI-native Workflow

Select a node → ask a question → freeze context → query ACT records → answer with evidence → navigate to the cited object.

AI context includes the selected network/spec/run/node/layer/revision. Answers distinguish engine observations, interpretations, and hypotheses, and state when evidence is missing.

Later plans use structured steps, parameters, preconditions, and budgets. AI and manual actions share execution entry points. Action records preserve requests and actual receipts; ACT retains authority over scientific conclusions.

Provider adapters execute in the workbench service; credentials never enter the browser. Start with one selected provider and one orchestration flow. Manual workflows remain available when AI is unavailable. Deliver read-only explanation before capability-gated execution plans.

Evidence is data, not authority to change tool permissions. Model retries must not reapply completed commands. A multi-agent framework and vector database are not initial requirements.

## 6. Cross-platform Access and Deployment

The first release targets browser access on Windows, macOS, and Linux without client-side Python, Node, ACT, or solver installation. Local computation still requires a compatible ACT environment. GUI platform support and native engine compatibility are separate claims.

Browser and service processes may run separately during development. Distribution provides one origin for assets, workers, API, and SSE. Development services bind to loopback by default. Remote single-user deployment uses HTTPS and an established access-authentication mechanism; multi-tenancy is outside the initial scope.

Maintainers deploy the computation service. Distinguish uploading a client file from selecting a server artifact; client absolute paths are not server paths. Desktop packaging and first-launch offline access can be added when required.

## 7. Technology Decisions and Open Items

FastAPI/Pydantic and React/TypeScript are the baseline. Evaluate and introduce layout, network/BaB rendering, and plotting dependencies when their features start.

Dockview, Model Explorer, React Flow/ELK, and Plotly are candidates, not installed or validated capabilities. ACT observer/control APIs, the model provider, supported browser versions, and performance thresholds require implementation-time validation.

Record decision changes here first. Extract ADRs when independent maintenance becomes useful.
