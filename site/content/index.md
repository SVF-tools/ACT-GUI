---
layout: home

hero:
  name: ACT
  text: Abstract Constraint Transformation
  tagline: A testing and verification framework for neural networks. Load a model and a specification, search for counterexamples, and prove properties with sound abstract interpretation and branch-and-bound.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/
    - theme: alt
      text: Try it online
      link: https://app.act-online.au
    - theme: alt
      text: GitHub
      link: https://github.com/SVF-tools/ACT

features:
  - title: One IR for every model
    details: PyTorch models, ONNX networks and VNN-LIB properties become one ACT Net, with the input and output specification embedded as layers, so every backend verifies the same thing.
  - title: Three abstract domains
    details: Propagate bounds with interval, HybridZ zonotopes or linear-relaxation dual bounds, through MLP, CNN, RNN and Transformer layers.
  - title: Branch-and-bound
    details: Refine undecided properties by splitting neurons or inputs, with batched subproblems, several branching heuristics and LP, dual or MILP bounding.
  - title: Whitebox fuzzing
    details: ACTFuzzer searches for violations on the GPU with gradient-guided mutations, adaptive perturbation scaling and neuron coverage.
  - title: Checked counterexamples
    details: Every counterexample, from fuzzing or verification, is checked on the concrete model against the same input and output specification before it is reported.
  - title: Verifier validation
    details: Cross-check verdicts against concrete counterexamples and check that abstract bounds contain every concrete activation, layer by layer.
---

<div class="home-demo">

![ACT fuzzing in the online workbench](./fuzzingGuide.gif)

</div>
