# ACT 是什么？

ACT（Abstract Constraint Transformation，抽象约束变换）是一个面向神经网络的测试与验证框架。给定一个模型，以及它可能接收的输入和必须产生的输出的规约，ACT 要么找到一个反例，即违反规约的输入，要么证明不存在这样的输入。

ACT 原生基于 PyTorch，可在 CPU 或 GPU 上运行。它读取 PyTorch 模型、ONNX 网络和 VNN-LIB 性质，把它们转换成同一种中间表示（ACT Net），再用多种抽象域和求解器验证这个表示。

---

## 快速开始

### 在线试用

**[ACT 在线工作台](https://app.act-online.au)** 在服务器上运行 ACT，你只需要一个浏览器。选择模型，再选择**模糊测试**、**验证**或 **BaB**，即可查看 ACT 的结果、逐层上下界和反例。

### 在本地运行

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312

python -m act.back_end --generate --device cpu --dtype float64              # 生成示例网络
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu   # 验证其中一个
```

Gurobi 和基准下载见[安装](./installation)。

### 验证你自己的模型

```bash
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib --solver torchlp --device cpu
```

---

## ACT 报告的结果

| 结果 | 含义 |
| --- | --- |
| `CERTIFIED` | 对规约中的每个输入，性质都成立。 |
| `FALSIFIED` | ACT 找到了反例，并已在具体模型上检查过。 |
| `UNKNOWN` | 抽象过于粗糙，无法判定，也没有找到反例。 |
| `TIMEOUT` | 时间预算先用完了。 |

模糊测试只能证伪：没有找到反例的模糊测试运行结论为 unknown，绝不会是 certified。

---

## ACT 支持的内容

| 方面 | 支持 |
| --- | --- |
| 输入 | PyTorch 模块、ONNX 网络、VNN-LIB 性质、TorchVision 数据集与模型对、紧凑 BERT 文本模型 |
| 输入规约 | 盒（box）、L∞ 球、线性多面体 |
| 输出性质 | top-1 鲁棒性、间隔（margin）鲁棒性、线性约束、输出范围、不安全线性区域 |
| 层 | MLP、CNN、RNN 和 Transformer 层 |
| 抽象域 | 区间、HybridZ（带形）、对偶（线性松弛） |
| 求解器 | TorchLP、对偶、HybridZ、Gurobi MILP/LP（需要许可证） |
| 测试 | 白盒模糊测试、验证器可靠性校验、PyTorch ↔ ACT 转换检查 |

---

## 论文

- Kaijie Liu and Yulei Sui. [Detecting Unsoundness in Neural Network Verifiers via Concrete–Abstract Consistency](https://openreview.net/forum?id=6vjnMGdx5i). AIware 2026.
- Guanqin Zhang and Yulei Sui. [Tensor-Based Batch Fuzzing with Adaptive Perturbation Scaling for Deep Neural Networks](https://arxiv.org/abs/2606.25239). ASE 2026.

ACT 采用 GNU Affero 通用公共许可证 v3.0（AGPL-3.0）。

---

## 接下来

- **[安装](./installation)**：安装 ACT、Gurobi 和基准。
- **[工作原理](./how-it-works)**：前端、后端和流水线三层。
- **[验证与测试](./modes)**：验证、分支定界、模糊测试和校验。
- **[配置](./configuration)**：设备、配置文件和调试选项。
- **[开发者文档](/README)**：在线工作台的源代码文档（英文）。
