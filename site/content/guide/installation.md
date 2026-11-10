# Installation

There are two ways to use ACT.

| You want | Use | You need |
| --- | --- | --- |
| To try it now | [The online workbench](#online-workbench) | A browser |
| To run ACT yourself | [A local install](#local-install) | Linux, Miniconda, git (a CUDA GPU is optional) |

---

## Online workbench

Open **[app.act-online.au](https://app.act-online.au)**. The workbench runs ACT on its server; you do not need to install anything.

---

## Local install

### 1. Create the environment

Install [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install), then clone ACT with its submodules and create the `act-py312` environment (Python 3.12 and PyTorch):

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312
```

Run every ACT command from the repository root.

### 2. Gurobi (optional)

Gurobi is only needed for the `gurobi` solver (MILP/LP). Get a [Gurobi license](https://www.gurobi.com/academia/academic-program-and-licenses/) and place it here:

```bash
cp /path/to/gurobi.lic ./modules/gurobi/gurobi.lic
```

Without a license, ACT prints a warning and uses its other solvers.

### 3. Check the install

```bash
python -m act.back_end --generate --device cpu --dtype float64     # build the example networks
python -m act.back_end --list-examples                              # list them
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu
```

Each tier has its own command line; `--help` lists every option:

```bash
python -m act.front_end --help    # datasets, benchmarks and specifications
python -m act.back_end --help     # verification and example networks
python -m act.pipeline --help     # fuzzing, validation and conversion tests
```

### 4. Benchmarks and datasets

ACT downloads benchmarks into its `data/` directory on request.

```bash
python -m act.front_end --list                  # TorchVision datasets and VNN-LIB categories
python -m act.front_end --search acas           # search by name
python -m act.front_end --download acasxu_2023  # ONNX models and VNN-LIB properties
python -m act.front_end --download MNIST        # dataset and its recommended models
python -m act.front_end --list-downloads        # what is already downloaded
```

### 5. Notebooks

The `ipynb/` directory has small demos, including a [fuzzer example](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_fuzzer.ipynb) and a [verifier example](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_verifier.ipynb).

Next: [How it works](./how-it-works).
