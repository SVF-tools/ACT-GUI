# Development and Deployment

[Project overview](../README.md) → [developer guide](README.md#choose-a-development-task) → **setup, deployment and checks**.

The workbench is a FastAPI service with a browser app and isolated run workers, next to an ACT checkout. Use local development to change code and Docker to serve it.

## Local Development

Requirements: Linux with the ACT checkout and its conda environment (`act-py312`, see the ACT README), Node 22+, and [uv](https://docs.astral.sh/uv/).

```bash
# once
uv venv --python "$(conda run -n act-py312 which python)" --system-site-packages .venv   # ACT, torch from the conda env
VIRTUAL_ENV=.venv uv pip install -r requirements/dev.txt                                # FastAPI etc. into .venv only
npm install

# run (ACT_ROOT defaults to /data1/guanqin/ACT)
./scripts/dev.sh
# then open http://127.0.0.1:5173
```

`dev.sh` starts the FastAPI service on 127.0.0.1:18765 and the Vite dev server on 127.0.0.1:5173, which proxies `/api` to the service; `ACT_GUI_SERVICE_PORT` and `ACT_GUI_WEB_PORT` change the ports. Both bind to loopback only. If the workbench runs on a remote machine, forward the port: `ssh -L 5173:127.0.0.1:5173 <host>` and open the same URL locally. Runs execute on CPU by default; records go to `var/records/` and loaded models to `var/models/`.

In the browser, load or select a model, choose Fuzzing, Verification, or BaB, and start a run below the network. The right column holds the Engine, Records and Assistant tabs (plus Neuron once a run is selected outside Fuzzing) and run history. Use **Guide** to revisit the introductory tour.

## Docker

Requirements: Docker with Compose v2.24+; for GPU, an NVIDIA driver and the NVIDIA Container Toolkit. Nothing else is installed on the host.

```bash
cp .env.example .env                      # optional settings (port, image tag, Gurobi, AI key)
scripts/docker_build.sh                   # stage the pinned ACT commit into build/act, then docker compose build
docker compose up -d                      # CPU; open http://127.0.0.1:8080
docker compose -f compose.yaml -f deploy/compose.gpu.yaml up -d  # NVIDIA GPU (ACT_GUI_DEVICE=cuda)
```

The image serves the built browser app, the API, and SSE from one origin on `127.0.0.1:${ACT_GUI_PORT:-8080}`; records, loaded models, staged engines and uploaded licenses persist in the `act-gui-data` volume (`/data`). `scripts/docker_build.sh` reads the ACT commit from `fixtures/catalog.json` and fetches it from `$ACT_SOURCE` (a local checkout by default, or a git URL). The catalog models are generated, git-ignored ACT files, so the script also copies them from `$ACT_NETS_FROM` (default `$ACT_ROOT`) and fails unless each matches its pinned sha256.

**ACT data.** The **Load model** panel builds models from ACT's git-ignored `data/` (VNN-LIB benchmarks, MNIST/CIFAR-10 test sets) and `literature/` (ONNX classifiers) directories, which the image does not contain. Mount them read-only with `-f deploy/compose.actdata.yaml` (`ACT_DATA_FROM` defaults to `$ACT_ROOT`); without them the panel lists no sources and the catalog still works.

**Gurobi.** Gurobi is optional; the image contains gurobipy (`GUROBIPY_VERSION`) but never a license. Either upload your `gurobi.lic` in the **Engine** tab, or mount it with `GUROBI_LICENSE_FILE=/path/to/gurobi.lic` in `.env` and `-f deploy/compose.gurobi.yaml`. The Engine tab shows Gurobi's own license check. WLS and token-server licenses work in containers; host-bound (named-user/academic) licenses usually do not. The current interval and BaB methods do not call Gurobi.

## Settings

Every setting is optional. Compose passes `.env` into the container; `dev.sh` and the service read the environment.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ACT_ROOT` | `/data1/guanqin/ACT` (`/opt/act` in the image) | Baseline ACT checkout: catalog nets, `data/` and `literature/` |
| `ACT_GUI_PORT` | `8080` | Docker host port, published on 127.0.0.1 only |
| `ACT_GUI_IMAGE` | `act-gui:0.1.0` | Image tag to build and run |
| `ACT_GUI_DEVICE` | `cpu` | Torch device for run workers; `deploy/compose.gpu.yaml` sets `cuda` |
| `ACT_GUI_RECORDS` | `var/records` (`/data/records` in the image) | Run records |
| `ACT_GUI_MODELS` | `models` next to the records root | Nets built from model sources |
| `ACT_GUI_ENGINES` | `engines` next to the records root | Staged ACT branch checkouts and the active engine |
| `ACT_GUI_SECRETS` | `secrets` next to the records root | Uploaded solver licenses |
| `ACT_GUI_ACT_REMOTES` | The SVF-tools and guanqin-123 ACT repositories | Repositories offered for branch switching, as `name=url,...` |
| `ACT_GUI_ALLOW_CUSTOM_REMOTES` | `1` | `0` stops users from entering their own repository URL |
| `ACT_SOURCE`, `ACT_NETS_FROM`, `ACT_DATA_FROM` | `$ACT_ROOT` | Where the Docker build and `deploy/compose.actdata.yaml` read ACT from |
| `GUROBIPY_VERSION`, `GUROBI_LICENSE_FILE` | `13.0.0`, unset | gurobipy in the image; a license mounted by `deploy/compose.gurobi.yaml` |
| `ANTHROPIC_API_KEY` | unset | Reserved for a real AI provider; the adapter is not implemented yet |

Entering a repository URL runs that repository's code on the server, so a public deployment needs access control or `ACT_GUI_ALLOW_CUSTOM_REMOTES=0`. Engine switching is described in [visual_bench/engine](../visual_bench/engine/README.md).

## Configuration Files

| Path | Configures |
| --- | --- |
| `compose.yaml`, `Dockerfile`, `.dockerignore`, `.env.example` | The workbench image and service; copy `.env.example` to `.env` next to `compose.yaml` |
| `deploy/compose.*.yaml` | Optional overlays, each added with `-f` after `compose.yaml`: `gpu` (NVIDIA GPUs), `actdata` (ACT's `data/` and `literature/`), `gurobi` (a mounted license file) |
| `requirements/dev.txt`, `requirements/runtime.txt` | Python pins for `.venv` and for the image |
| `pyproject.toml` | pytest and pyright settings |
| `package.json`, `tsconfig.json`, `vite.config.ts` | Browser dependencies, type check, dev server, build and tests |
| `site/compose.yaml` | The website container ([site](../site/README.md)) |

## Checks

```bash
.venv/bin/python -m pytest      # bridge parity against real ACT + service tests (CPU: CUDA_VISIBLE_DEVICES=)
.venv/bin/python -m pytest visual_bench/fuzzing   # one module's tests (any module directory works)
npm test                        # browser tests: selection, mode registry, query keys, wire helpers (vitest)
npm run typecheck               # tsc
npm run check:types             # generated wire.ts matches visual_bench/schemas.py
.venv/bin/python scripts/gen_image_nets.py    # (re)generate the MNIST/CIFAR-10 catalog nets into ACT's examples/nets/
.venv/bin/python scripts/record_fixtures.py   # re-record fixtures/catalog.json from native ACT calls
```

Each module guide's **Validation** section names its focused tests and the observable result to check. These are commands to run, not results.
