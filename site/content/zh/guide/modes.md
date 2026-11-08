# 验证与测试

ACT 可以证明性质、搜索反例，也可以检查验证器本身。每项任务都有自己的命令，所有命令都接受 `--device {cpu,cuda,gpu,mps}` 和 `--dtype {float32,float64}`。

| 任务 | 命令 | 可能的结果 |
| --- | --- | --- |
| [验证](#verification) | `python -m act.back_end --verify` | certified、falsified、unknown、timeout |
| [分支定界](#branch-and-bound) | `python -m act.back_end --verify --bab` | certified、falsified、unknown、timeout |
| [模糊测试](#fuzzing) | `python -m act.pipeline --fuzz` | 找到反例，或没有找到 |
| [基准运行](#benchmark-runs) | `python -m act.pipeline --verify vnnlib` | 每个实例一个结果 |
| [验证器校验](#verifier-validation) | `python -m act.pipeline --verify ... --validate-soundness` | 每项检查为通过、失败或无法判定 |

---

## 验证 {#verification}

单次验证只传播一次上下界，并据此判定性质。

```bash
# 一个示例 ACT Net（--list-examples 会列出生成的网络名）
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu

# ONNX 网络加 VNN-LIB 性质；--save-net 保存实际验证的 Net
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib \
  --solver torchlp --save-net verified.json --device cpu --dtype float64
```

- **`--solver`** 选择后端：`torchlp`（PyTorch LP）、`dual`、`hybridz`、`gurobi`（MILP/LP，需要许可证）或 `auto`。
- **`--tf-mode`** 选择前向传递函数，`interval` 或 `hybridz`。
- **`--timeout`** 设置以秒为单位的时间预算。
- 含多个析取分支的 VNN-LIB 文件会作为多个 Net 验证：`verified.d0.json`、`verified.d1.json`，依此类推。

---

## 分支定界 {#branch-and-bound}

分支定界用于细化单次验证判定不了的性质。它把问题拆分开，批量地为每个子问题定界，直到每个分支都得到判定、找到反例或预算用完为止。

```bash
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --bab --device cpu
```

| 选项 | 取值 |
| --- | --- |
| `--bab-solver-tier` | `lp`、`dual`、`dual_alpha`、`dual_alpha_eta` |
| `--bab-branching` | 如何选择下一次拆分，例如 `babsr`、`fsb`、`gain`、`width` 或 `random` |
| `--bab-bounding` | 先展开哪些子问题，例如 `greedy` 或 `depth_bound_blend` |
| `--bab-max-depth`、`--bab-max-subproblems` | 搜索的上限 |

命名的 BaB 配置（预设）位于 `act/config/backend.yaml`，见[配置](./configuration#configuration-files)。

---

## 模糊测试 {#fuzzing}

ACTFuzzer 搜索违反性质的输入。它在 GPU 上批量运行具体模型，在输入规约内对输入做变异，并用输出性质检查每个候选。

```bash
python -m act.pipeline --fuzz --category acasxu_2023 --iterations 5000
python -m act.pipeline --fuzz --creator torchvision --dataset MNIST
```

- **变异。** 五种策略，由 `--mutation-weights` 控制比例：`gradient`（一步 FGSM 风格扰动）、`pgd`（迭代并投影的 PGD 步）、`activation`（DeepXplore 风格，针对低激活神经元）、`boundary`（在输入规约边界附近采样）和 `random`（高斯噪声）。
- **扰动大小。** `--perturb-mode adaptive_scalar`（一个自适应尺度）、`adaptive_perdim`（每个输入维度一个尺度）或 `fixed`，配合 `--perturb-scale`。
- **覆盖率。** 激活新神经元的输入会被保留为种子（`--coverage-strategy`、`--activation-threshold`）。
- **预算。** `--iterations`、`--timeout` 和 `--stop-on-first-violation`。
- **输出。** 反例和摘要保存在输出目录下（`--output`；用 `--no-save` 跳过保存）。

模糊测试无法证明性质：什么也没找到时，性质仍然是 unknown。

---

## 基准运行 {#benchmark-runs}

在已下载的基准上端到端地运行验证器：

```bash
python -m act.pipeline --download acasxu_2023
python -m act.pipeline --verify vnnlib --category acasxu_2023 --max-instances 10
python -m act.pipeline --verify torchvision --dataset MNIST
```

`--tf-modes` 和 `--solvers` 选择抽象域和求解器；一次运行使用各自的第一个值。

---

## 验证器校验 {#verifier-validation}

校验在 ACT 生成的示例网络或某个基准上，检查验证器是否可靠、数值是否正确。

```bash
python -m act.pipeline --verify netfactory --validate-soundness --device cpu --dtype float64
python -m act.pipeline --verify netfactory --validate-soundness --tf-modes interval --solvers torchlp
python -m act.pipeline --verify vnnlib --category acasxu_2023 --validate-soundness
```

1. **第一层：可靠性。** 用具体反例交叉检查每个求解器的结论。存在真实反例却得到 `CERTIFIED`，就是可靠性错误。
2. **第二层：数值精度。** 采样输入在具体模型上运行，每一层的抽象上下界都必须包含具体激活值。

`--verify torch2act` 和 `--verify act2torch` 检查 PyTorch 模型与 ACT Net 之间的转换。

下一步：[配置](./configuration)。
