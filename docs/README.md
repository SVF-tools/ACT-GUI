# Documentation Scope

**Owner:** B coordinates cross-module consistency. A, C, and D maintain the scientific semantics, interaction, and validation content affected by their changes.

## Purpose

Use a small set of documents to explain boundaries, decisions, and current work, so contributors can determine where an implementation belongs, who owns it, and how it will be accepted.

## Responsibilities

- [design.md](design.md): system boundaries, cross-module data/execution semantics, AI-native behavior, cross-platform access, and structure evolution.
- [plan.md](plan.md): implementation order, role assignments, testing strategy, and completion criteria.
- This README: documentation ownership, information placement, and maintenance rules.

## Non-goals

- Do not maintain a complete API field catalog independently of executable schemas. Once implemented, Pydantic owns the wire schema.
- Document the defined major modules without prebuilding deeper component directories, an ADR collection, or task-generation machinery.
- Do not present planned capabilities as implemented or unexecuted checks as test results.

## Inputs and Outputs

Inputs are confirmed requirements, design decisions, implementation constraints, and actual validation evidence. Outputs are the current scope, boundaries, plan, and acceptance criteria.

Mark unresolved items explicitly. Update the original decision when new evidence changes it; do not accumulate contradictory appendices. Technical documents are maintained in English.

## Information Ownership

| Information | Authoritative location |
| --- | --- |
| Project navigation and overall startup entry point | Root README.md |
| Repository-wide contributor rules | Root AGENTS.md |
| Workbench scope and module navigation | visual_bench/README.md |
| ACT integration scope and module navigation | engine_bridge/README.md |
| Module subproblems, patterns, and implementation sequence | The owning module's README.md |
| Cross-module architecture and decisions | design.md |
| Cross-module task index, bootstrap, release, and validation strategy | plan.md |
| Detailed feature tasks and completion evidence | The owning module’s README.md |

Link to the owning document instead of maintaining independent copies. READMEs define responsibility; AGENTS.md defines contributor behavior.

## Module README Structure

Each defined module documents its status/owner, subproblems and objective, scope/non-goals, inputs/outputs/state, design patterns and rationale, dependencies and implementation placement, implementation sequence, acceptance tests, and future extraction criteria.

Each module also includes a functional implementation specification: feature triggers/results, processing flow, proposed public operations, planned files, state/failure rules, and a task table with stable IDs, dependencies, and completion evidence. Proposed interfaces are labeled as design targets. Replace them with actual public interfaces and working commands when code exists. A pattern must explain the problem it solves; ordinary functions and small interfaces are sufficient unless a framework has demonstrated value.

## Acceptance and Extraction Criteria

Local links must resolve, current state must be distinguishable from planned work, and responsibilities must not conflict. Contributors should be able to identify the first implementation slice from these documents.

Module entry points are listed in [visual_bench](../visual_bench/README.md) and [engine_bridge](../engine_bridge/README.md). Parent documents retain summaries and navigation; detailed requirements live in the owning module README.

Only one level of major modules is expanded. Subproblems such as analysis/propagation remain README sections until implementation complexity justifies extraction. Split architecture or decision documents when their size or ownership requires it.
