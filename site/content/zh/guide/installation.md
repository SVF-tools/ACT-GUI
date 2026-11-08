# 安装

ACT-GUI 有三种使用方式。

| 你的目标 | 使用方式 | 所需条件 |
| --- | --- | --- |
| 立即试用 | [托管工作台](#hosted-workbench) | 浏览器 |
| 使用自己的服务器 | [Docker](#run-with-docker) | Docker 与 Compose v2.24+（GPU 还需要 NVIDIA Container Toolkit） |
| 修改代码 | [开发环境](#development-setup) | Linux、ACT 及其 conda 环境、Node 22+、uv |

---

## 托管工作台 {#hosted-workbench}

打开 **[app.act-online.au](https://app.act-online.au)**。无需在本机安装任何软件。

---

## 使用 Docker 运行 {#run-with-docker}

一个镜像包含工作台提供的全部内容：浏览器应用、API、实时更新和固定版本的 ACT 代码库。

```bash
cp .env.example .env                      # optional settings (port, image tag, Gurobi, AI key)
scripts/docker_build.sh                   # stage the pinned ACT commit, then docker compose build
docker compose up -d                      # CPU; open http://127.0.0.1:8080
docker compose -f compose.yaml -f compose.gpu.yaml up -d      # NVIDIA GPU
```

- **端口。** 工作台只监听 `127.0.0.1:${ACT_GUI_PORT:-8080}`。如果 8080 已被占用，请设置 `ACT_GUI_PORT`。如需从其他机器访问，请将其置于 HTTPS 和身份验证代理之后。
- **ACT 源码。** `scripts/docker_build.sh` 读取 `fixtures/catalog.json` 中固定的 ACT 提交，并从 `$ACT_SOURCE` 获取。默认值是本地代码库，也可以是 git URL。
- **基准和数据集。** **Load model** 从 ACT 的 `data/` 和 `literature/` 目录构建模型，镜像不包含这些目录。使用 `-f compose.actdata.yaml` 以只读方式挂载。没有这些目录时，目录模型仍可使用。
- **持久化。** 记录、构建的模型和上传的许可证保存在 `act-gui-data` 卷中。
- **Gurobi（可选）。** 在 **Engine** 标签页上传 `gurobi.lic`，或设置 `GUROBI_LICENSE_FILE` 并添加 `-f compose.gurobi.yaml`。参阅[配置](./configuration#gurobi)。

---

## 开发环境 {#development-setup}

```bash
# once
uv venv --python "$(conda run -n act-py312 which python)" --system-site-packages .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-dev.txt
npm install

# run (ACT_ROOT defaults to /data1/guanqin/ACT)
./scripts/dev.sh
# then open http://127.0.0.1:5173
```

`dev.sh` 在 `127.0.0.1:18765` 启动 API 服务，在 `127.0.0.1:5173` 启动 Vite 开发服务器，并将 `/api` 转发到服务。两者都只监听回环地址。在远程机器上，可使用 `ssh -L 5173:127.0.0.1:5173 <host>` 转发端口。

### 检查

```bash
.venv/bin/python -m pytest      # bridge parity against real ACT + service tests
npm test                        # browser tests (vitest)
npm run typecheck               # TypeScript
npm run check:types             # generated wire types match the Python schemas
```

下一步：[工作原理](./how-it-works)。
