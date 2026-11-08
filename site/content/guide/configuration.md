# Configuration

Every setting has a default. Change one on the command line for a single run, or in a configuration file for every run.

**Precedence:** command-line flag > environment variable > BaB preset > configuration file > code default.

## Device and precision

All three command lines accept the same two options.

| Option | Values | Default |
| --- | --- | --- |
| `--device` | `cpu`, `cuda` (or `gpu`), `mps` | a CUDA GPU when one is available, otherwise `cpu` |
| `--dtype` | `float32`, `float64` | `float32` |

Use `float64` when you need tight numerical agreement, for example in verifier validation. The environment variables `ACT_DEVICE`, `ACT_DTYPE` and `ACT_SOLVER` set the same values for every back-end run.

---

## Configuration files

The defaults live in `act/config/`.

| File | Configures |
| --- | --- |
| `backend.yaml` | Verification: the solver cascade, TorchLP, Gurobi, HybridZ and dual settings, branch-and-bound, and named BaB presets (`bab_presets`, selected with `backend.bab_preset`) |
| `pipeline.yaml` | Fuzzing (iterations, time budget, mutation weights, perturbation mode, coverage), benchmark verification and validation |
| `frontend.yaml` | Spec creation: epsilons, margins, input and output kinds, and text verification |
| `gen_act_net.yaml` | The architectures of the generated example networks |

For example, the fuzzing defaults in `pipeline.yaml`:

```yaml
fuzzing:
  max_iterations: 10000
  timeout_seconds: 3600.0
  perturb_mode: "adaptive_scalar"
  perturb_scale: 0.1
```

---

## Gurobi

The `gurobi` solver needs a license at `modules/gurobi/gurobi.lic`. ACT finds it there automatically; without it, ACT prints a warning and the other solvers still work. Academic licenses are free from [Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/).

---

## Paths and logs

| Path | Contents |
| --- | --- |
| `data/` | Downloaded benchmarks, datasets and models |
| `act/back_end/examples/nets/` | Generated example ACT Nets |
| `act/pipeline/log/` | Execution logs, fuzzing results and the transfer function debug log |

---

## Debugging options

`PerformanceOptions` (`act/util/options.py`) holds global debugging flags for scripts that call ACT from Python.

| Flag | Default | Effect |
| --- | --- | --- |
| `debug_tf` | `True` | Logs every layer's bounds and constraints to `act/pipeline/log/act_debug_tf.log` |
| `debug_tf_max_constraints` | `50` | Constraints logged per layer |
| `validate_constraints` | `True` | Checks the constraints each transfer function produces |

The debug log is appended to on every run and is not rotated. Turn `debug_tf` off for long or large runs, or the log can fill the disk.
