# Architecture Baseline

**Baseline:** 2026-11-03; developer navigation and implementation distinctions updated 2026-11-04. ACT-GUI is the visualization and interaction interface for the ACT engine.

The primary boundaries are visual_bench, engine_bridge, and docs. FastAPI/React and browser/service processes are implementation details within those boundaries. A runnable workbench exists. This document owns cross-module invariants and design decisions; module READMEs distinguish implemented behavior from future designs.

For a feature change, start at the [development task chooser](README.md#choose-a-development-task), not by reading this document end to end. Parent READMEs identify collaborating modules; module Change Guides identify required edits, conditional edits, contracts and tests. The [documentation guide](README.md#module-readme-structure) defines this hierarchy.

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

- visual_bench: workspace, model_spec, verification, fuzzing, engine, bab, analysis, assistant, records, plus the shared kernels `wire.py`/`errors.py`/`config.py` (service) and `shared/` (browser).
- engine_bridge: engine_session, model_spec, execution, inspection, events, plus a shared contracts.py/contracts.md.

The fourteen modules each have a scope README. Parent READMEs own summaries and navigation; module READMEs own subproblems, patterns, feature behavior, current files and usage, dependency-linked implementation tasks, and acceptance evidence. fuzzing and engine were split out of verification on 2026-11-04 (see section 3) so that run lifecycle, fuzzing views, and engine/solver status can be owned and changed independently.

The two model_spec modules have distinct roles: visual_bench presents descriptions and input drafts; engine_bridge loads through ACT and converts engine descriptions. Both use the same source data without duplicating scientific processing.

Current inspection reads use module services: analysis reads a completed run's sealed layers.json; bab combines run results with bridge observation coverage. The worker collects interval layer states through engine_bridge.inspection, and verification seals the returned data through records. The assistant calls the same model/run/analysis/BaB services as HTTP routes. BaB runs on an ACT checkout with `act.pipeline.gui.bab_gui` record ACT's committed waves (bab.jsonl, written by the worker through engine_bridge.events) and the bab service projects them into a search tree. There is still no live node-inspection gateway and no node control; these remain future ACT-dependent capabilities.

## 3. Runtime and Implementation Boundaries

visual_bench has thin composition roots: `server.py` (FastAPI app, error rendering, router inclusion), `workbench.py` (constructs and wires the module services), and `app.tsx` (layout and shared selection). Module-specific TypeScript and Python code belongs in the corresponding module. Do not repeat web/service directories inside every module.

**Module slice (2026-11-04).** Each visual_bench module that serves data is a vertical slice with a fixed set of files, so one contributor can own a module end to end and the data middle layer is uniform:

| Layer | File | Rule |
| --- | --- | --- |
| Wire contract | `<module>/schemas.py` | Pydantic payloads of this module; `visual_bench/schemas.py` only re-exports them and lists `WIRE_MODELS` for generation. Shared primitives live in `wire.py`. |
| Service (middle layer, server) | `<module>/service.py` | Application use cases; the only code that calls engine_bridge or records for this module. Raises `errors.AppError`. Takes collaborators as constructor arguments built in `workbench.py`; never imports FastAPI. |
| HTTP | `<module>/routes.py` | `router(service) -> APIRouter`; maps HTTP to service calls only. |
| Client (middle layer, browser) | `<module>/api.ts`, `<module>/hooks.ts` | Endpoint calls on `shared/http.ts`; TanStack Query hooks with keys from `shared/queryClient.ts`. Mutations invalidate the keys they change. |
| Views | `<module>/*View.tsx`, panels | Presentation only: data from hooks or props, no fetch calls. |
| Tests | `<module>/test_*.py`, `*.test.ts` | Next to the code they verify. |

Dependency rules: a service may use another module's service through its constructor (verification uses model_spec and engine; fuzzing, analysis, and bab read runs through verification); routes never import another module's routes; a browser module may import another module's `hooks.ts` but not its views or internals; `shared/` and `wire.py` import no feature module. AI tools (assistant) call the same services the routes call. Server data reaches views only through TanStack Query: there is no second browser cache and no manual refresh counter. Live runs follow SSE and invalidate the affected run queries on each committed event.

ACT-specific knowledge (which methods a net supports, fuzz option split, provenance of fuzzing records) is reported by engine_bridge (`execution.methods`, `execution.fuzz`) instead of being encoded in the workbench, so an ACT change touches the bridge and its tests first.

The browser uses HTTP queries/commands and SSE events. The service calls engine_bridge; long computations execute in a separate worker. HTTP routes and AI tools reuse ordinary application use cases.

Workbench Pydantic schemas are the sole handwritten source for wire types. The current pipeline generates browser types in generated/wire.ts; module api.ts clients remain handwritten. REST OpenAPI alone does not define the event payload contract. The service maps neutral bridge data to the wire format; bridge code does not depend on upper-layer API schemas.

Service startup, configuration, records, and AI providers belong to visual_bench. ACT invocation and version differences are isolated in engine_bridge. Worker lifecycle is managed by the workbench; ACT calls inside the worker go through the bridge.

Start with a small real-data inspection slice. Propagation requirements live in analysis/README.md; no deeper propagation directory is needed yet. Keep tests near their modules, add cross-module E2E when a complete flow exists, and add deployment infrastructure when shipping. Do not prebuild shared packages, multi-engine plugins, or separate agent services.

## 4. Data and Execution Invariants

These are design constraints, not a claim that all associated APIs exist. Current run lifecycle events,
fuzz progress and capability-gated fuzz controls are implemented; revision-bound node snapshots and
verification/BaB pause/step/split remain planned. Use module Change Guides for today's paths.

- Bind queries to run/node/layer/revision. A late response must not replace a newer selection.
- Keep node identity separate from batch lane indices. Bounds retain scope, direction, computed/inherited origin, method, and provenance.
- Geometry states its coordinates, representation, projection, and guarantee. Samples are not sound outer approximations; a local visualization does not establish a global verdict.
- Fix model/spec/initial-config snapshots for a run. Model/spec changes create another run.
  Capability-gated live fuzz config changes retain that initial snapshot and append ACT's applied/rejected
  receipts; replay combines the initial live values and committed changes.
- Models come from two places: the pinned catalog (`fixtures/catalog.json`, ACT files by commit + sha256, with recorded native verdicts) and model sources (a VNN-COMP ONNX + VNN-LIB instance, or an ONNX image classifier with a chosen test image and eps). engine_bridge builds a source into an ACT net through ACT's own front end and `save_net_to_file`; the workbench stores it content-addressed (`<kind>-<sha12>`, `ACT_GUI_MODELS`, default next to the records root) with its build parameters. A different image or eps is a different model snapshot, never an edit of an existing one. Built models have no recorded native verdicts.
- Publish scientific state only after a valid observation boundary. Current lifecycle/progress events support ordered replay; committed node snapshots, gap protocols and rollback-aware scientific batches require future ACT interfaces.
- Replay reconstructs recorded display state, not solver memory. Missing historical bounds are not_recorded.
- Run creation checks supported methods and idempotency. Future engine commands must additionally check capabilities and expected_revision and distinguish accepted from applied. Enable pause/step/split only when ACT supports the stated semantics.
- Fetch large tensors and detailed tree data on demand instead of streaming everything.
- BaB search records (2026-11-12, ACT-03 via ACT #132): a node's identity is ACT's node_id (the root is 0 with parent -1). A node exists only once a committed record names it: as a child (pending or evicted), as a node solved in a wave with ACT's outcome, or as the terminal's deciding node. A wave is ACT's commit point (ACT discards a wave it rolls back), so the log holds committed state only and a replay to wave w shows exactly what ACT had committed by then. The verdict is ACT's (run result, terminal record); an empty frontier, a proved share or a node count is never presented as one. The closed share weights every split equally among its children: it describes the split tree, not input volume. The bridge reduces ACT's per-neuron node bounds to per-layer ranges and ReLU stability counts; per-neuron node bounds are not recorded.
- Propagation records (2026-11-05, ACT-06): every bound ACT reports carries a key of scope (run root now, BaB node later, with parent), domain, pass (forward/backward/refine), layer, stage, version and origin (computed/inherited); lanes stay separate from scope. Tensors are stored once, content-addressed, and referenced by key, so BaB nodes reuse unchanged parent tensors instead of copying them. A run shows only its own domain; cross-domain comparison is a separate future feature.
- Input provenance (2026-11-13, ACT-10): text shown for a VNN-LIB input comes only from ACT's provenance record for that exact instance file (`act.pipeline.gui.provenance_gui` checks the file's recorded sha256), together with ACT's match status: `verified` (the benchmark generator's own bookkeeping, replayed by ACT, fixes which sentence produced the box), `aligned` (the box is matched to a sentence by order-preserving nearest-box alignment of reconstructed embeddings, kept only when every other sentence is clearly farther from the box) or `unmatched` (no text is shown). A point of the model input space is never decoded into text: a counterexample is drawn as a point against its box, and the known examples nearest to it are labelled as neighbours with their distance.

## 5. First AI-native Workflow

Select a node → ask a question → freeze context → query ACT records → answer with evidence → navigate to the cited object. The first target is a layer/stage of a completed run, which needs no committed BaB events; committed BaB nodes follow once ACT exposes them.

AI context includes the selected network/spec/run/node/layer/revision. Answers distinguish engine observations, interpretations, and hypotheses, and state when evidence is missing.

Later plans use structured steps, parameters, preconditions, and budgets. AI and manual actions share execution entry points. Action records preserve requests and actual receipts; ACT retains authority over scientific conclusions.

Provider adapters execute in the workbench service; credentials never enter the browser. Start with one selected provider and one orchestration flow. Manual workflows remain available when AI is unavailable. Deliver read-only explanation before capability-gated execution plans.

Evidence is data, not authority to change tool permissions. Model retries must not reapply completed commands. A multi-agent framework and vector database are not initial requirements.

## 6. Cross-platform Access and Deployment

The first release targets browser access on Windows, macOS, and Linux without client-side Python, Node, ACT, or solver installation. Local computation still requires a compatible ACT environment. GUI platform support and native engine compatibility are separate claims.

During development, contributors open the workbench in a local browser at a documented localhost URL; the browser dev server and the FastAPI service may run as separate processes. Distribution provides one origin for assets, workers, API, and SSE. Development services bind to loopback by default. Remote single-user deployment uses HTTPS and an established access-authentication mechanism; multi-tenancy is outside the initial scope.

Maintainers deploy the computation service. Distinguish uploading a client file from selecting a server artifact; client absolute paths are not server paths. Desktop packaging and first-launch offline access can be added when required.

**Container distribution (2026-11-03).** The one-origin build ships as one Docker image run by Docker Compose, so a user needs only Docker (plus the NVIDIA Container Toolkit for GPU) and a browser:

- One image, one service. A Node build stage produces the browser assets; the runtime stage holds Python 3.12, the GUI's ACT runtime dependencies, the pinned ACT checkout, and the workbench, and FastAPI serves assets, API, and SSE from one origin. The Vite dev server is not in the image; development keeps `scripts/dev.sh`.
- GPU. The image carries the CUDA 12.8 torch wheel, which also runs on CPU. `compose.yaml` runs on CPU; adding `deploy/compose.gpu.yaml` reserves the NVIDIA GPUs and sets `ACT_GUI_DEVICE=cuda`. The run result records the torch device ACT actually used, so a GPU claim is evidence, not configuration.
- ACT source. The image contains a shallow git checkout of exactly the commit pinned in `fixtures/catalog.json`, so the engine probe reports a real commit and a clean tree. `scripts/docker_build.sh` stages it from a local ACT checkout or a git URL. ACT is AGPL-3.0: a published image must have the pinned commit available as source (pushed upstream) before release.
- Gurobi is optional and user-licensed. gurobipy is installed (version is a build argument) but no license is ever built into the image. A user supplies one either by mounting a license file (`deploy/compose.gurobi.yaml`, `GRB_LICENSE_FILE`) or by uploading it through the workbench, which stores it server-side with owner-only permissions next to the records and passes it to each run worker. An uploaded license takes precedence over a mounted one; the content is never returned by the API. The service reports Gurobi's own license check result; host-bound licenses generally fail inside containers, while WLS and token-server licenses work. The current interval and BaB paths use ACT's TorchLPSolver, so a license changes no current verdict.
- Loopback by default. Compose publishes the port on `127.0.0.1` only. Remote access still requires the HTTPS and authentication front end described above (DIST-01).

**Public website (2026-11-08).** The product overview, user guide (English, Chinese, French) and developer docs are a separate static VitePress site in `site/`, served by its own container (`site/compose.yaml`) at `act-online.au`; the workbench is served at `app.act-online.au`. The site copies the repository's Markdown at build time instead of keeping a second copy, so module READMEs remain the single source for developer documentation. It shares no code, dependencies or process with the workbench.

## 7. Technology Decisions and Open Items

FastAPI/Pydantic and React/TypeScript are the baseline. Evaluate and introduce layout, network/BaB rendering, and plotting dependencies when their features start.

Dockview, Model Explorer, React Flow/ELK, and Plotly are candidates, not installed or validated capabilities. ACT observer/control APIs, the model provider, supported browser versions, and performance thresholds require implementation-time validation.

First-version implementation decisions (2026-11-03): development uses the Vite dev server with a `^/api/` proxy to FastAPI (a bare `/api` prefix also matched the module `/api.ts`); each run executes in a separate Python worker process launched by the workbench and writes its result to a file, because ACT prints to stdout; records are per-run directories with an immutable manifest, an append-only event log, and sha256-sealed artifacts; non-finite numbers cross the wire as the strings `"Infinity"`, `"-Infinity"`, `"NaN"`; browser types are generated with json-schema-to-typescript from `models_json_schema` over `visual_bench/schemas.py`; the network view is a small in-house SVG DAG until MSV-02 evaluates renderers. Container distribution and Gurobi license handling follow section 6 (DIST-02, ES-04, VER-05).

Fuzzing decision (2026-11-03): ACT's fuzzer is a third run method (`fuzz`) on the existing run lifecycle rather than a separate subsystem, so it inherits the worker, idempotency, records, SSE replay, and export. The worker reports progress as JSON lines over an inherited pipe, because ACT owns stdout; the supervisor commits each line as a `fuzz.progress` event. A fuzzing verdict is `falsified` only when ACT's PropertyChecker accepted a counterexample and is otherwise `unknown`; the workbench never presents fuzzing as certification (EXE-04, VER-06).

Record decision changes here first. Extract ADRs when independent maintenance becomes useful.

Live fuzz control decision (2026-11-06, ACT-08): `fuzz.control` independently gates the public ACT
option registry, observation records and thread-safe batch-boundary controls. The pinned baseline
retains its private observation seams and stop fallback. The workbench sends JSON commands over a
second inherited worker pipe; ACT change records and worker pause flags return on the progress pipe
and become committed fuzz events. The run manifest freezes initial live values, applied updates
reconstruct current state, and persisted per-run request-ID receipts prevent retry duplication.
Queued responses are distinct from ACT's applied/rejected changes. The supervisor excludes pause
time and uses applied timeout changes when enforcing its outer deadline. Workbench code imports
only bridge controls; it never imports ACT.
