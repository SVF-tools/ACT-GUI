# Developer Guide

[Project overview](../README.md) → **choose a development task** → a module's Change Guide.

Documentation should let a developer find the smallest correct change without reading the entire repository. This guide maps a goal to its owning module, parent scopes explain collaboration, and module guides connect the goal to files, contracts and tests. Setup, deployment and checks are in [development.md](development.md). Keep technical documentation in English.

## Choose a Development Task

Start with the row matching your intended behavior. Follow its module guide for the concrete files, handoff contracts, and tests; you do not need to read every module.

| I want to change... | Start here | Cross the boundary only when... |
| --- | --- | --- |
| Layout, selection, mode switching, or the guided tour | [workspace](../visual_bench/workspace/README.md#change-guide) | A selected object needs new server data, rather than just a new presentation. |
| Model loading, input images, or specifications | [visual_bench/model_spec](../visual_bench/model_spec/README.md#change-guide) | ACT source loading or model descriptions change: [engine_bridge/model_spec](../engine_bridge/model_spec/README.md#change-guide). |
| Run start/stop, run settings, time budgets, history, or lifecycle events | [verification](../visual_bench/verification/README.md#change-guide) | ACT invocation changes: [execution](../engine_bridge/execution/README.md#change-guide). |
| Captured ACT errors/warnings or the reproduction snapshot | [verification diagnostics](../visual_bench/verification/README.md#diagnostics-and-reproduction-snapshot) | Storage guarantees change: [records](../visual_bench/records/README.md#change-guide). |
| Fuzz settings, live mutations, or saved counterexamples | [fuzzing](../visual_bench/fuzzing/README.md#change-guide) | New ACT data/options are needed, or the shared run lifecycle changes. |
| Propagation views or layer bounds | [analysis](../visual_bench/analysis/README.md#change-guide) | Recorded data is insufficient: [inspection](../engine_bridge/inspection/README.md#change-guide). |
| BaB search tree, coverage or final summaries | [bab](../visual_bench/bab/README.md#change-guide) | New ACT record fields: [events](../engine_bridge/events/README.md#change-guide). Node controls require new ACT support first. |
| Explanations and evidence navigation | [assistant](../visual_bench/assistant/README.md#change-guide) | An evidence source needs a new application query; do not bypass its service. |
| Persistence, integrity, replay, or export | [records](../visual_bench/records/README.md#change-guide) | A feature needs a new artifact or annotation; keep its meaning in the producing module. |
| Engine diagnostics, branch switching, or Gurobi licensing | [engine](../visual_bench/engine/README.md#change-guide) | The actual engine/license probe changes: [engine_session](../engine_bridge/engine_session/README.md#change-guide). |
| ACT compatibility or scientific result adaptation | [Engine Bridge](../engine_bridge/README.md#change-guide) | ACT itself lacks the required algorithm or public capability. |
| Setup, deployment, settings, or checks | [development.md](development.md) | A setting changes a module's behavior: document that behavior in the module guide. |
| The public website or user guide | [site](../site/README.md#change-guide) | A guide page describes new behavior: change the owning module first, then the guide and its translations. |
| Architecture, planning, or documentation | [Change Guide](#change-guide) below | A decision spans modules; local feature evidence stays in its module README. |

## Reading and Change Order

1. Choose a task above. The module's **Change Guide** distinguishes required edits, conditional edits, and code the request only passes through.
2. Follow that module's **Flow Diagram** and block-to-code table. Cross-module handoffs link to the neighboring guide; the parent maps ([visual_bench](../visual_bench/README.md#flow-diagram), [engine_bridge](../engine_bridge/README.md#flow-diagram)) intentionally omit internal calls.
3. Check **Validation**, then open the reference/backlog only if you need contract rationale or future tasks. A planned API is not an existing entry point.

When a wire payload changes, edit the owning module's Pydantic schema, run `npm run gen:types`, and include the generated `visual_bench/generated/wire.ts`. Do not hand-edit generated types. A route, worker, or shared transport on the path is not automatically a modification target.

## Change Guide

Where each kind of documentation lives:

| Information to change | Authoritative location | Also update only when needed |
| --- | --- | --- |
| Product overview, highlights, or quick start | [Root README](../README.md) | Keep it high-level: link to the owning guide instead of copying detail. |
| Task entry | [Choose a development task](#choose-a-development-task) | Parent/module links if entry points moved. |
| Setup, deployment, settings, or checks | [development.md](development.md) | The root quick start when its commands change. |
| Module responsibility or neighbor handoff | [visual_bench](../visual_bench/README.md) or [engine_bridge](../engine_bridge/README.md) | The producer and consumer module guides. |
| Feature path, files, routes, tests or acceptance evidence | Owning module README | Parent summary if its responsibility or boundary contract changed. |
| Cross-module invariant or architecture decision | [design.md](design.md) | Affected module guides and integration prerequisites. |
| Task dependency or cross-repository prerequisite | [plan.md](plan.md) for the index; module README for detailed task | Keep stable task IDs and link the acceptance evidence. |
| Repository-wide contributor behavior | [AGENTS.md](../AGENTS.md) | Scope-specific rules only if genuinely distinct. |

## Flow Diagram

Arrows here mean **read next**, not runtime calls. A developer should follow one branch until the intended change and its validation are clear.


```mermaid
flowchart TB
  Goal["Developer guide<br/>Choose a development goal"] --> Scope["Parent README<br/>Find owner and handoffs"]
  Scope --> Module["Module README<br/>Change Guide"]
  Module --> Path["Scenario diagram<br/>Block-to-code mapping"]
  Path --> Check["Validation<br/>Test and observable result"]
  Module -. "Only when needed" .-> Detail["Reference and backlog<br/>Rationale, task evidence, future work"]

```

| Block | What the reader must learn | What to leave for the next level |
| --- | --- | --- |
| Developer guide | Which feature owns the intended change | Detailed API fields and file inventories |
| Parent | Which modules collaborate and what crosses their boundaries | Internal helper calls and every import edge |
| Module | Required edits, conditional edits, reused path, exact code/contract links, validation | Lengthy rationale and unimplemented design |
| Reference/backlog | Constraints, stable task IDs, dependencies, acceptance evidence, future extraction criteria | Nothing here should masquerade as a current capability |

The root README stays a product overview (what ACT-GUI is, highlights, architecture, quick start) and links here instead of repeating developer routing.

## Module README Structure

Use a short current responsibility/status paragraph followed by:

1. **Change Guide:** concrete developer goals mapped to required edits, conditional edits and existing pass-through code. Do not turn the runtime path into a mandatory edit checklist.
2. **Flow Diagram:** one compact top-down Mermaid diagram per distinct use case. Follow requests through execution and show how the result reaches the user; separate live and recorded paths when their semantics differ.
3. **Block mapping:** beside the diagram, link each block to its code entry, contract/artifact and neighbor guide. A file name in a box alone is not a development instruction.
4. **Validation:** focused existing commands and an observable end-to-end result, including errors and unavailable data. Commands are not evidence until actually run.
5. **Reference/backlog:** current file/route inventory, rationale, detailed task IDs/dependencies/evidence, and clearly labeled future plans. Use GitHub details disclosures for long material, not for the primary development path.

Browser-only modules do not need invented service layers. Storage and assistant modules use their actual store.py and explain.py entries. Preserve task IDs and evidence when reorganizing sections; repair inbound anchors when headings move.

### Diagram Correspondence

- Parent blocks represent responsibilities; child diagrams expand the selected responsibility. They need not repeat every internal edge in the parent.
- Use the same module names at each level. Qualify visual_bench/model_spec versus engine_bridge/model_spec whenever both scopes could be meant.
- Label arrow meaning: request/call, result, event, artifact, or navigation. A return arrow is not an import dependency. Explain the legend locally rather than relying on color alone.
- Every cross-module handoff links to the receiving module's guide and names its public contract. Do not maintain a duplicate field catalog: link executable schemas or bridge dataclasses.
- Keep current and proposed flows separate. Short labels and small top-down charts must remain readable in GitHub's README column; split an overloaded graph by scenario before shrinking text.

## Validation

For a documentation change:

- Follow at least one concrete task from this guide to its module and test entry. Confirm both the request and result paths, not only a list of filenames.
- Compare code links and public operations with the implementation. Check required versus conditional edits against actual forwarding behavior.
- Validate local file links and heading anchors, Mermaid syntax/rendering, and disclosure markup. Inspect rendered diagrams, not just fenced text.
- Check that no stable task ID, dependency or acceptance evidence was accidentally removed and that historical test results remain dated evidence, not current claims.

Examples for this repository: expose a fuzz hyperparameter; add a live fuzz metric; adjust an existing layer view; change run stop behavior. Each should lead to a different edit scope. A task that changes only presentation should not send the developer through the whole engine stack.

## Reference

<details>
<summary>Ownership and maintenance boundaries</summary>

B coordinates cross-module consistency. A, C and D maintain the scientific semantics, interaction and validation content affected by their work. READMEs explain responsibility and development; AGENTS.md defines contributor behavior.

Inputs are confirmed requirements, decisions, constraints and actual evidence. Outputs are navigable scope, implementation guidance and acceptance criteria. Mark unresolved items explicitly and revise the original decision when facts change; do not append contradictory histories to current instructions.

Feature plans and task evidence stay with the owning module. Cross-module decisions stay in design.md; the task index and integration order stay in plan.md. Do not add a parallel document tree or empty implementation directories merely to fit a template. Extract detail into another file only when its size or independent maintenance warrants it.

</details>
