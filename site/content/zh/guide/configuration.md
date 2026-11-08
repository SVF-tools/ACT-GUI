# 配置

每项设置都有默认值。只影响一次运行时在命令行修改；影响所有运行时在配置文件中修改。

**优先级：** 命令行参数 > 环境变量 > BaB 预设 > 配置文件 > 代码默认值。

## 设备与精度 {#device-and-precision}

三个命令行都接受同样的两个选项。

| 选项 | 取值 | 默认值 |
| --- | --- | --- |
| `--device` | `cpu`、`cuda`（或 `gpu`）、`mps` | 有 CUDA GPU 时使用 GPU，否则 `cpu` |
| `--dtype` | `float32`、`float64` | `float32` |

需要严格的数值一致性时（例如验证器校验）请使用 `float64`。环境变量 `ACT_DEVICE`、`ACT_DTYPE` 和 `ACT_SOLVER` 为所有后端运行设置相同的值。

---

## 配置文件 {#configuration-files}

默认值位于 `act/config/`。

| 文件 | 配置内容 |
| --- | --- |
| `backend.yaml` | 验证：求解器级联，TorchLP、Gurobi、HybridZ 和对偶设置，分支定界，以及命名的 BaB 预设（`bab_presets`，用 `backend.bab_preset` 选择） |
| `pipeline.yaml` | 模糊测试（迭代次数、时间预算、变异权重、扰动模式、覆盖率）、基准验证和校验 |
| `frontend.yaml` | 规约创建：epsilon、间隔、输入和输出类型，以及文本验证 |
| `gen_act_net.yaml` | 生成的示例网络的结构 |

例如 `pipeline.yaml` 中的模糊测试默认值：

```yaml
fuzzing:
  max_iterations: 10000
  timeout_seconds: 3600.0
  perturb_mode: "adaptive_scalar"
  perturb_scale: 0.1
```

---

## Gurobi {#gurobi}

`gurobi` 求解器需要位于 `modules/gurobi/gurobi.lic` 的许可证。ACT 会自动在这里查找；没有许可证时，ACT 会打印警告，其他求解器照常可用。学术许可证可以从 [Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/) 免费申请。

---

## 路径与日志 {#paths-and-logs}

| 路径 | 内容 |
| --- | --- |
| `data/` | 下载的基准、数据集和模型 |
| `act/back_end/examples/nets/` | 生成的示例 ACT Net |
| `act/pipeline/log/` | 运行日志、模糊测试结果和传递函数调试日志 |

---

## 调试选项 {#debugging-options}

`PerformanceOptions`（`act/util/options.py`）保存全局调试开关，供从 Python 调用 ACT 的脚本使用。

| 开关 | 默认值 | 作用 |
| --- | --- | --- |
| `debug_tf` | `True` | 把每一层的上下界和约束记录到 `act/pipeline/log/act_debug_tf.log` |
| `debug_tf_max_constraints` | `50` | 每层记录的约束数 |
| `validate_constraints` | `True` | 检查每个传递函数生成的约束 |

调试日志在每次运行时追加写入，不会轮转。长时间或大规模运行时请关闭 `debug_tf`，否则日志可能写满磁盘。
