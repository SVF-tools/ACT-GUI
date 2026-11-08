---
layout: home

hero:
  name: ACT-GUI
  text: See inside neural network verification
  tagline: A browser workbench for the ACT verifier. Load a network, fuzz it, verify it, and inspect every bound ACT computes. ACT decides; the workbench shows you why.
  actions:
    - theme: brand
      text: Open Workbench
      link: https://app.act-online.au
    - theme: alt
      text: Get Started
      link: /guide/
    - theme: alt
      text: GitHub
      link: https://github.com/guanqin-123/ACT-GUI

features:
  - title: Live fuzzing
    details: Run ACT's fuzzer and watch the original, mutated and difference images update as it searches. Pause, resume, stop or retune the run while it is still running.
  - title: Verification and BaB
    details: Run ACT's single-pass verification with the interval, dual or HybridZ domain, or its batched branch-and-bound. The verdict is always ACT's own.
  - title: Layer-by-layer bounds
    details: Step through the bounds ACT recorded at each layer, compare them before and after, and project a two-coordinate interval box.
  - title: Counterexamples you can use
    details: Every violation ACT accepts is saved with the run and exports as a VNN-COMP witness or an image.
  - title: Reproducible records
    details: Each run keeps a manifest, an append-only event log and sha256-sealed artifacts. Export the whole record as a zip.
  - title: Any ACT branch
    details: Switch the engine to the pinned baseline or a branch of any ACT fork. Features the active engine cannot support are disabled, with the reason shown.
---

<div class="home-demo">

![ACT-GUI fuzzing walkthrough](./fuzzingGuide.gif)

</div>
