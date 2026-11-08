# What is ACT?

ACT (Abstract Constraint Transformation) is a testing and verification framework for neural networks. Given a model and a specification of the inputs it may receive and the outputs it must produce, ACT either finds a counterexample, an input that violates the specification, or proves that none exists.

ACT is PyTorch-native and runs on CPU or GPU. It reads PyTorch models, ONNX networks and VNN-LIB properties, converts them into one intermediate representation (the ACT Net), and verifies that representation with several abstract domains and solvers.

---

## Quick Start

### Try it online

The **[ACT online workbench](https://app.act-online.au)** runs ACT on a server, so you only need a browser. Pick a model, choose **Fuzzing**, **Verification** or **BaB**, and watch ACT's results, layer bounds and counterexamples.

### Run it locally

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312

python -m act.back_end --generate --device cpu --dtype float64              # build the example networks
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu   # verify one of them
```

See [Installation](./installation) for Gurobi and benchmark downloads.

### Verify your own model

```bash
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib --solver torchlp --device cpu
```

---

## What ACT reports

| Result | Meaning |
| --- | --- |
| `CERTIFIED` | The property holds for every input in the specification. |
| `FALSIFIED` | ACT found a counterexample and checked it on the concrete model. |
| `UNKNOWN` | The abstraction was too coarse to decide, and no counterexample was found. |
| `TIMEOUT` | The time budget ran out first. |

Fuzzing can only falsify: a fuzz run without a counterexample ends as unknown, never certified.

---

## What ACT supports

| Area | Supported |
| --- | --- |
| Inputs | PyTorch modules, ONNX networks, VNN-LIB properties, TorchVision dataset and model pairs, compact BERT text models |
| Input specifications | box, L∞ ball, linear polytope |
| Output properties | top-1 robustness, margin robustness, linear constraints, output ranges, unsafe linear regions |
| Layers | MLP, CNN, RNN and Transformer layers |
| Abstract domains | interval, HybridZ (zonotopes), dual (linear relaxation) |
| Solvers | TorchLP, dual, HybridZ, Gurobi MILP/LP (license required) |
| Testing | whitebox fuzzing, verifier soundness validation, PyTorch ↔ ACT conversion checks |

---

## Publications

- Kaijie Liu and Yulei Sui. [Detecting Unsoundness in Neural Network Verifiers via Concrete–Abstract Consistency](https://openreview.net/forum?id=6vjnMGdx5i). AIware 2026.
- Guanqin Zhang and Yulei Sui. [Tensor-Based Batch Fuzzing with Adaptive Perturbation Scaling for Deep Neural Networks](https://arxiv.org/abs/2606.25239). ASE 2026.

ACT is licensed under the GNU Affero General Public License v3.0.

---

## What's next

- **[Installation](./installation)**: set up ACT, Gurobi and the benchmarks.
- **[How it works](./how-it-works)**: the front-end, back-end and pipeline tiers.
- **[Verification and testing](./modes)**: verification, branch-and-bound, fuzzing and validation.
- **[Configuration](./configuration)**: devices, configuration files and debugging options.
- **[Developer docs](/README)**: the source of the online workbench.
