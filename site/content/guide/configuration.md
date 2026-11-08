# Configuration

Every setting is optional. Docker Compose reads them from `.env`. In development, export them before running `scripts/dev.sh`.

## Environment variables

### Service

| Variable | Default | Meaning |
| --- | --- | --- |
| `ACT_GUI_PORT` | `8080` | Host port of the container; it is bound to `127.0.0.1` only. |
| `ACT_GUI_IMAGE` | `act-gui:0.1.0` | Image name and tag to build or run. |
| `ACT_GUI_DEVICE` | `cpu` | Torch device for runs. `compose.gpu.yaml` sets `cuda`. The run result records the device ACT actually used. |
| `ACT_GUI_RECORDS` | `var/records` (`/data/records` in Docker) | Root directory for run records. |
| `ACT_GUI_MODELS` | next to the records root | Content-addressed store for built models. |
| `ACT_GUI_ENGINES` | next to the records root | Imported ACT branch checkouts and the active engine selection. |
| `ACT_GUI_SECRETS` | `/data/secrets` in Docker | Server-side storage for uploaded licenses. |

### ACT engine

| Variable | Default | Meaning |
| --- | --- | --- |
| `ACT_ROOT` | `/data1/guanqin/ACT` (`/opt/act` in Docker) | The baseline ACT checkout. Catalog nets, `data/` and `literature/` are read from here. |
| `ACT_GUI_ACT_REMOTES` | SVF-tools and guanqin-123 on GitHub | Preconfigured ACT repositories offered for branch switching, as `name=url,...`. |
| `ACT_GUI_ALLOW_CUSTOM_REMOTES` | `1` | Set `0` to stop users from entering other repository URLs. |

### Build

| Variable | Default | Meaning |
| --- | --- | --- |
| `ACT_SOURCE` | the local ACT checkout | Where `scripts/docker_build.sh` fetches the pinned ACT commit from; a path or git URL. |
| `ACT_NETS_FROM` | `$ACT_ROOT` | Where the build copies catalog nets from; each must match its pinned sha256. |
| `ACT_DATA_FROM` | `$ACT_ROOT` | Host source of `data/` and `literature/` for `compose.actdata.yaml`. |
| `GUROBIPY_VERSION` | `13.0.0` | gurobipy version installed in the image; match your license's major version. |
| `GUROBI_LICENSE_FILE` | empty | Host path of `gurobi.lic`, used with `compose.gurobi.yaml`. |

---

## Switching the ACT engine

The **Engine** tab chooses which ACT code the workbench imports: the pinned baseline, or a branch head of any ACT fork. Choose a preconfigured repository or enter an `https` URL.

- A switch restarts the service, because ACT cannot be re-imported in a running process.
- The workbench checks every feature against the APIs the selected engine provides. Features it cannot support are disabled, and the reason is shown.
- A built model that the new engine cannot load is marked **needs rebuild** and can be rebuilt from its recorded settings.
- Entering a URL runs that repository's code on the server. A public deployment needs access control, or `ACT_GUI_ALLOW_CUSTOM_REMOTES=0`.

---

## Gurobi

gurobipy is installed in the image. A license never is.

- **Upload.** Upload a `gurobi.lic` in the **Engine** tab. It is stored server-side with owner-only permissions and passed to each run worker. The API never returns its content.
- **Mount.** Set `GUROBI_LICENSE_FILE` and add `-f compose.gurobi.yaml`. An uploaded license takes precedence over a mounted one.
- The Engine tab shows Gurobi's own license check. WLS and token-server licenses work in containers. Host-bound licenses (named-user or academic) usually do not.
- The current interval and BaB methods do not call Gurobi, so a license changes no current verdict.
