# What is ACT-GUI?

ACT-GUI is the visualization and interaction workbench for [ACT](https://github.com/SVF-tools/ACT), a neural network verifier. ACT does the scientific work: it propagates bounds, searches for counterexamples, and decides verdicts. ACT-GUI lets you see that work. It loads models and specifications, runs ACT, shows the evidence ACT produces, and keeps a record of every run.

You need nothing but a browser. The workbench runs on a server with ACT installed, and every computation happens there.

---

## Quick Start

### Open the workbench

The hosted workbench is at **[app.act-online.au](https://app.act-online.au)**. To run your own copy, see [Installation](./installation).

### Your first run

1. **Pick a model.** Select a catalog model in the sidebar, or use **Load model** to build one from a VNN-COMP benchmark instance (ONNX + VNN-LIB) or an ONNX image classifier with a test image and an epsilon.
2. **Choose a mode.** The modes are **Fuzzing**, **Verification** and **BaB**.
3. **Start the run.** The controls sit below the network view. Fuzzing streams its progress and mutated images live. Verification and BaB report ACT's verdict when they finish.
4. **Inspect the evidence.** Open the layer bounds, the counterexamples, or the run history. The **Records** tab shows each run's provenance, and you can export the run as a zip.

**Guide** in the top bar replays the introductory tour at any time.

---

## The principle: ACT decides

The workbench never computes or overrides a verdict.

- **Verdicts come from ACT.** The GUI only displays what ACT reports.
- **Fuzzing never certifies.** A fuzz run is `falsified` only when ACT's property checker accepts a counterexample. Every other fuzz run ends as `unknown`.
- **The assistant explains; it does not decide.** Its answers cite recorded evidence and never replace ACT's result.
- **Missing data stays missing.** A value ACT did not record is shown as not recorded, never filled in or estimated.

---

## What is available today

| Available | Not yet available |
| --- | --- |
| Model loading from the catalog, VNN-LIB instances and ONNX classifiers | Node-level BaB history and controls |
| Verification with the interval, dual or HybridZ domain, and BaB final summaries | Geometry beyond interval boxes |
| Live fuzzing with run controls and saved counterexamples | A real AI provider (the assistant uses a deterministic placeholder) |
| Recorded layer-by-layer interval bounds | |
| Run records, diagnostics and zip export | |
| ACT branch switching and Gurobi license management | |

---

## What's next

- **[Installation](./installation)**: use the hosted workbench, run it with Docker, or set up a development checkout.
- **[How it works](./how-it-works)**: how the browser, the workbench service and ACT divide the work.
- **[Working modes](./modes)**: fuzzing, verification, BaB, layer analysis, the assistant and records.
- **[Configuration](./configuration)**: environment variables, engine switching and Gurobi.
- **[Developer docs](/README)**: find the module that owns the behavior you want to change.
