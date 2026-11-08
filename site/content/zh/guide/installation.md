# 安装

使用 ACT 有两种方式。

| 你想要 | 使用 | 你需要 |
| --- | --- | --- |
| 立即试用 | [在线工作台](#online-workbench) | 浏览器 |
| 自己运行 ACT | [本地安装](#local-install) | Linux、Miniconda、git（CUDA GPU 可选） |

---

## 在线工作台 {#online-workbench}

打开 **[app.act-online.au](https://app.act-online.au)**。工作台在服务器上运行 ACT，你不需要安装任何东西。

---

## 本地安装 {#local-install}

### 1. 创建环境

安装 [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install)，然后连同子模块一起克隆 ACT，并创建 `act-py312` 环境（Python 3.12 和 PyTorch）：

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312
```

所有 ACT 命令都在仓库根目录运行。

### 2. Gurobi（可选）

只有 `gurobi` 求解器（MILP/LP）需要 Gurobi。申请 [Gurobi 许可证](https://www.gurobi.com/academia/academic-program-and-licenses/)，然后放到这里：

```bash
cp /path/to/gurobi.lic ./modules/gurobi/gurobi.lic
```

没有许可证时，ACT 会打印警告，并使用其他求解器。

### 3. 检查安装

```bash
python -m act.back_end --generate --device cpu --dtype float64     # 生成示例网络
python -m act.back_end --list-examples                              # 列出示例网络
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu
```

每一层都有自己的命令行，`--help` 会列出全部选项：

```bash
python -m act.front_end --help    # 数据集、基准和规约
python -m act.back_end --help     # 验证和示例网络
python -m act.pipeline --help     # 模糊测试、校验和转换测试
```

### 4. 基准和数据集

ACT 按需把基准下载到 `data/` 目录。

```bash
python -m act.front_end --list                  # TorchVision 数据集和 VNN-LIB 类别
python -m act.front_end --search acas           # 按名称搜索
python -m act.front_end --download acasxu_2023  # ONNX 模型和 VNN-LIB 性质
python -m act.front_end --download MNIST        # 数据集及其推荐模型
python -m act.front_end --list-downloads        # 已下载的内容
```

### 5. Notebook 示例

`ipynb/` 目录有一些小型演示，包括一个[模糊测试示例](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_fuzzer.ipynb)和一个[验证器示例](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_verifier.ipynb)。

下一步：[工作原理](./how-it-works)。
