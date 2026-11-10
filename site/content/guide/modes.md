# Verification and testing

ACT can prove a property, search for a counterexample, or check another verifier. Each task has its own command; all of them accept `--device {cpu,cuda,gpu,mps}` and `--dtype {float32,float64}`.

| Task | Command | Possible results |
| --- | --- | --- |
| [Verification](#verification) | `python -m act.back_end --verify` | certified, falsified, unknown, timeout |
| [Branch-and-bound](#branch-and-bound) | `python -m act.back_end --verify --bab` | certified, falsified, unknown, timeout |
| [Fuzzing](#fuzzing) | `python -m act.pipeline --fuzz` | counterexamples found, or none |
| [Benchmark runs](#benchmark-runs) | `python -m act.pipeline --verify vnnlib` | one result per instance |
| [Verifier validation](#verifier-validation) | `python -m act.pipeline --verify ... --validate-soundness` | pass, fail or inconclusive per check |

---

## Verification

Single-pass verification propagates bounds once and decides the property from them.

```bash
# an example ACT Net (--list-examples shows the generated names)
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu

# an ONNX network with a VNN-LIB property; --save-net keeps the Net that was verified
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib \
  --solver torchlp --save-net verified.json --device cpu --dtype float64
```

- **`--solver`** chooses the backend: `torchlp` (PyTorch LP), `dual`, `hybridz`, `gurobi` (MILP/LP, license required) or `auto`.
- **`--tf-mode`** chooses the forward transfer function, `interval` or `hybridz`.
- **`--timeout`** sets the time budget in seconds.
- A VNN-LIB file with several disjuncts is verified as several Nets: `verified.d0.json`, `verified.d1.json`, and so on.

---

## Branch-and-bound

Branch-and-bound refines a property that single-pass verification leaves unknown. It splits the problem, bounds each subproblem in batches, and stops when every branch is decided, a counterexample is found, or the budget runs out.

```bash
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --bab --device cpu
```

| Option | Choices |
| --- | --- |
| `--bab-solver-tier` | `lp`, `dual`, `dual_alpha`, `dual_alpha_eta` |
| `--bab-branching` | how the next split is chosen, for example `babsr`, `fsb`, `gain`, `width` or `random` |
| `--bab-bounding` | which subproblems are expanded first, for example `greedy` or `depth_bound_blend` |
| `--bab-max-depth`, `--bab-max-subproblems` | limits on the search |

Named BaB configurations (presets) live in `act/config/backend.yaml`; see [Configuration](./configuration#configuration-files).

---

## Fuzzing

ACTFuzzer searches for inputs that violate the property. It runs the concrete model on the GPU in batches, mutates inputs inside the input specification, and checks each candidate against the output property.

```bash
python -m act.pipeline --fuzz --category acasxu_2023 --iterations 5000
python -m act.pipeline --fuzz --creator torchvision --dataset MNIST
```

- **Mutations.** Five strategies, mixed by `--mutation-weights`: `gradient` (one FGSM-style step), `pgd` (iterative, projected PGD steps), `activation` (DeepXplore-style, targets low-activation neurons), `boundary` (samples near the input specification's boundary) and `random` (Gaussian noise).
- **Perturbation size.** `--perturb-mode adaptive_scalar` (one adaptive scale), `adaptive_perdim` (one scale per input dimension) or `fixed`, with `--perturb-scale`.
- **Coverage.** Inputs that activate new neurons are kept as seeds (`--coverage-strategy`, `--activation-threshold`).
- **Budget.** `--iterations`, `--timeout`, and `--stop-on-first-violation`.
- **Output.** Counterexamples and a summary are saved under the output directory (`--output`, `--no-save` to skip).

Fuzzing cannot prove a property: when it finds nothing, the property is still unknown.

---

## Benchmark runs

Run the verifier end to end on a downloaded benchmark:

```bash
python -m act.pipeline --download acasxu_2023
python -m act.pipeline --verify vnnlib --category acasxu_2023 --max-instances 10
python -m act.pipeline --verify torchvision --dataset MNIST
```

`--tf-modes` and `--solvers` choose the domain and solver; one run uses the first value of each.

---

## Verifier validation

Validation checks that a verifier is sound and numerically correct, on ACT's generated example networks or on a benchmark.

```bash
python -m act.pipeline --verify netfactory --validate-soundness --device cpu --dtype float64
python -m act.pipeline --verify netfactory --validate-soundness --tf-modes interval --solvers torchlp
python -m act.pipeline --verify vnnlib --category acasxu_2023 --validate-soundness
```

1. **Level 1: soundness.** Concrete counterexamples are cross-checked against every solver's verdict. A `CERTIFIED` result next to a real counterexample is a soundness bug.
2. **Level 2: numerical precision.** Sampled inputs are run through the concrete model, and every layer's abstract bounds must contain the concrete activations.

`--verify torch2act` and `--verify act2torch` check the conversions between PyTorch models and ACT Nets.

Next: [Configuration](./configuration).
