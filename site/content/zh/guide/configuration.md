# 配置

所有设置都是可选的。Docker Compose 从 `.env` 读取这些设置。开发时，请在运行 `scripts/dev.sh` 前导出它们。

## 环境变量

### 服务

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `ACT_GUI_PORT` | `8080` | 容器的主机端口，仅绑定到 `127.0.0.1`。 |
| `ACT_GUI_IMAGE` | `act-gui:0.1.0` | 要构建或运行的镜像名称和标签。 |
| `ACT_GUI_DEVICE` | `cpu` | 运行使用的 Torch 设备。`compose.gpu.yaml` 设置为 `cuda`。运行结果会记录 ACT 实际使用的设备。 |
| `ACT_GUI_RECORDS` | `var/records`（Docker 中为 `/data/records`） | 运行记录的根目录。 |
| `ACT_GUI_MODELS` | 与记录根目录相邻 | 构建模型的内容寻址存储。 |
| `ACT_GUI_ENGINES` | 与记录根目录相邻 | 导入的 ACT 分支代码库和当前引擎选择。 |
| `ACT_GUI_SECRETS` | Docker 中为 `/data/secrets` | 服务器端存储上传的许可证。 |

### ACT 引擎

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `ACT_ROOT` | `/data1/guanqin/ACT`（Docker 中为 `/opt/act`） | 基线 ACT 代码库。目录网络、`data/` 和 `literature/` 从这里读取。 |
| `ACT_GUI_ACT_REMOTES` | GitHub 上的 SVF-tools 和 guanqin-123 | 预配置的 ACT 仓库，格式为 `name=url,...`，用于切换分支。 |
| `ACT_GUI_ALLOW_CUSTOM_REMOTES` | `1` | 设置为 `0` 可禁止用户输入其他仓库 URL。 |

### 构建

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `ACT_SOURCE` | 本地 ACT 代码库 | `scripts/docker_build.sh` 获取固定提交的位置，可以是路径或 git URL。 |
| `ACT_NETS_FROM` | `$ACT_ROOT` | 构建复制目录网络的位置，每个网络都必须匹配固定的 sha256。 |
| `ACT_DATA_FROM` | `$ACT_ROOT` | `compose.actdata.yaml` 使用的 `data/` 和 `literature/` 主机源目录。 |
| `GUROBIPY_VERSION` | `13.0.0` | 镜像中安装的 gurobipy 版本，应与许可证主版本匹配。 |
| `GUROBI_LICENSE_FILE` | 空 | 与 `compose.gurobi.yaml` 一起使用的 `gurobi.lic` 主机路径。 |

---

## 切换 ACT 引擎

**Engine** 标签页用于选择工作台导入的 ACT 代码，可以是固定基线，也可以是任意 ACT 派生仓库的分支头。选择预配置仓库，或输入 `https` URL。

- 切换会重启服务，因为 ACT 无法在运行中的进程里重新导入。
- 工作台会根据所选引擎提供的 API 检查每项功能。不支持的功能会被禁用，并显示原因。
- 新引擎无法加载的构建模型会标记为 **needs rebuild**，并可根据已记录的设置重新构建。
- 输入 URL 会在服务器上运行该仓库的代码。公开部署需要访问控制，或将 `ACT_GUI_ALLOW_CUSTOM_REMOTES` 设置为 `0`。

---

## Gurobi {#gurobi}

gurobipy 安装在镜像中，但镜像中从不包含许可证。

- **上传。** 在 **Engine** 标签页上传 `gurobi.lic`。文件会以仅所有者可读的权限存储在服务器端，并传给每个运行工作进程。API 不会返回其内容。
- **挂载。** 设置 `GUROBI_LICENSE_FILE` 并添加 `-f compose.gurobi.yaml`。上传的许可证优先于挂载的许可证。
- Engine 标签页显示 Gurobi 自己的许可证检查结果。WLS 和令牌服务器许可证可以在容器中使用。绑定主机的许可证（命名用户或学术许可证）通常无法使用。
- 当前的 interval 和 BaB 方法不会调用 Gurobi，因此许可证不会改变当前结论。
