# Installation

There are three ways to use ACT-GUI.

| You want | Use | You need |
| --- | --- | --- |
| To try it now | [The hosted workbench](#hosted-workbench) | A browser |
| Your own server | [Docker](#run-with-docker) | Docker with Compose v2.24+ (and the NVIDIA Container Toolkit for GPU) |
| To change the code | [Development setup](#development-setup) | Linux, ACT and its conda environment, Node 22+, uv |

---

## Hosted workbench

Open **[app.act-online.au](https://app.act-online.au)**. You do not need to install anything on your machine.

---

## Run with Docker

One image contains everything the workbench serves: the browser app, the API, live updates, and a pinned ACT checkout.

```bash
cp .env.example .env                      # optional settings (port, image tag, Gurobi, AI key)
scripts/docker_build.sh                   # stage the pinned ACT commit, then docker compose build
docker compose up -d                      # CPU; open http://127.0.0.1:8080
docker compose -f compose.yaml -f compose.gpu.yaml up -d      # NVIDIA GPU
```

- **Port.** The workbench listens on `127.0.0.1:${ACT_GUI_PORT:-8080}` only. If 8080 is taken, set `ACT_GUI_PORT`. To reach it from other machines, put it behind HTTPS and an authentication proxy.
- **ACT source.** `scripts/docker_build.sh` reads the ACT commit pinned in `fixtures/catalog.json` and fetches it from `$ACT_SOURCE`, which is a local checkout by default or a git URL.
- **Benchmarks and datasets.** **Load model** builds models from ACT's `data/` and `literature/` directories, and the image does not include them. Mount them read-only with `-f compose.actdata.yaml`. Without them, the catalog still works.
- **Persistence.** Records, built models and uploaded licenses are kept in the `act-gui-data` volume.
- **Gurobi (optional).** Upload a `gurobi.lic` in the **Engine** tab, or mount one with `GUROBI_LICENSE_FILE` and `-f compose.gurobi.yaml`. See [Configuration](./configuration#gurobi).

---

## Development setup

```bash
# once
uv venv --python "$(conda run -n act-py312 which python)" --system-site-packages .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-dev.txt
npm install

# run (ACT_ROOT defaults to /data1/guanqin/ACT)
./scripts/dev.sh
# then open http://127.0.0.1:5173
```

`dev.sh` starts the API service on `127.0.0.1:18765` and the Vite dev server on `127.0.0.1:5173`, which forwards `/api` to the service. Both listen on loopback only. On a remote machine, forward the port with `ssh -L 5173:127.0.0.1:5173 <host>`.

### Checks

```bash
.venv/bin/python -m pytest      # bridge parity against real ACT + service tests
npm test                        # browser tests (vitest)
npm run typecheck               # TypeScript
npm run check:types             # generated wire types match the Python schemas
```

Next: [How it works](./how-it-works).
