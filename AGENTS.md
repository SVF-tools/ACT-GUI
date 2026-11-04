# Contributor and Agent Rules

Read the root README, docs/design.md, docs/plan.md, and the README of each affected module before making changes. The primary scopes are visual_bench, engine_bridge, and docs.

- Maintain technical documentation in English, including module READMEs, architecture, development plans, and contributor rules.
- ACT-GUI is the complete visualization and interaction interface to ACT. Organize product boundaries by responsibility, rather than programming language or deployment process.
- ACT owns verification algorithms, scientific computation, and verification verdicts. Only engine_bridge may depend directly on ACT; visual_bench accesses the engine through the integration contract.
- visual_bench owns research context, interaction, application orchestration, records, and AI collaboration. engine_bridge owns ACT version/capability adaptation and invocation.
- FastAPI provides the workbench service interface; React provides browser presentation. Keep process, type, and test boundaries explicit instead of merging all logic into an entry-point file.
- Workbench Pydantic schemas are the sole handwritten source for wire types. Generate browser types/clients once the generation pipeline exists. engine_bridge must not depend on workbench views or API schemas.
- AI tools and manual controls use the same application query and command entry points. Preserve context, evidence, capability/revision checks, and idempotency. AI explanations must not override ACT verdicts.
- Parent READMEs define overall scope and navigation. Module READMEs define subproblems, scope/non-goals, inputs/outputs/state, design patterns and rationale, dependencies, implementation sequence, acceptance criteria, and extraction criteria.
- Maintain scope READMEs for the fourteen defined modules (nine in visual_bench, five in engine_bridge). Each README lists the module's current files, routes, and test command. Add deeper directories, code, shared packages, tooling, and dependencies when needed; do not prebuild empty implementations or a multi-agent platform.
- Keep each visual_bench module a vertical slice (docs/design.md section 3): `schemas.py` → `service.py` → `routes.py` on the service, `api.ts` → `hooks.ts` → views in the browser. Views never fetch directly; server data goes through the module's TanStack Query hooks. A change that crosses modules goes through a service constructor or a public `hooks.ts`, never through another module's internals.
- After changing any `schemas.py`, run `npm run gen:types` and commit the regenerated `visual_bench/generated/wire.ts`; never edit it by hand.
- Add tests with the behavior they verify and keep them close to the relevant module. Distinguish synthetic fixtures from ACT recordings and fake-provider tests from real-provider evaluations.
- Report checks actually run and any unverified behavior. There is currently no runnable application; do not invent startup or test results.
- Keep feature implementation plans and task evidence in module READMEs. Each task needs a stable ID, dependencies, observable deliverable, and acceptance evidence; proposed APIs/files are not implemented capabilities.
- Keep cross-module decisions in docs/design.md and the task index/integration order in docs/plan.md. Add scoped AGENTS.md files only when distinct, stable local rules justify them.

These rules do not introduce an additional approval workflow. Work within the scope already authorized by the user.
