# ACT-GUI

A visualization and interaction interface for the [ACT](https://github.com/SVF-tools/ACT) engine. Researchers can inspect networks and specifications, observe verification and branch-and-bound (BaB), analyze layer-wise overapproximation, and conduct experiments through direct interaction or AI assistance.

This repository contains the GUI product. ACT remains a separate computation engine. React/TypeScript and FastAPI/Pydantic are implementation technologies within the workbench.

**Status:** architecture and scope documentation only. No application or model-provider integration has been implemented.

```text
ACT-GUI/
  README.md
  AGENTS.md
  LICENSE
  .gitignore
  visual_bench/       # Parent scope and seven module READMEs
  engine_bridge/      # Parent scope, five module READMEs, and contracts.md
  docs/
    README.md
    design.md
    plan.md
```

- [Visual Bench](visual_bench/README.md): views, research context, application operations, records, and AI collaboration.
- [Engine Bridge](engine_bridge/README.md): ACT integration and compatibility; no verification algorithm implementations.
- [Documentation scope](docs/README.md): ownership and maintenance of design information.
- [Architecture](docs/design.md) · [Development plan](docs/plan.md) · [Contributor rules](AGENTS.md).

Top-level boundaries follow product responsibilities. One level of module documentation is defined; deeper directories and implementation files are added as needed. Browser and service execution boundaries remain explicit. Module READMEs now include concrete feature plans, proposed interfaces/files, dependency-linked tasks, and acceptance evidence. Installation, startup, and test commands will be documented when implemented.
