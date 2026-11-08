# Installation

ACT-GUI peut être utilisé de trois façons.

| Objectif | Utiliser | Pré-requis |
| --- | --- | --- |
| L'essayer maintenant | [Atelier hébergé](#hosted-workbench) | Un navigateur |
| Votre propre serveur | [Docker](#run-with-docker) | Docker avec Compose v2.24+ (et le NVIDIA Container Toolkit pour le GPU) |
| Modifier le code | [Configuration de développement](#development-setup) | Linux, ACT et son environnement conda, Node 22+, uv |

---

## Atelier hébergé {#hosted-workbench}

Ouvrez **[app.act-online.au](https://app.act-online.au)**. Rien n'a besoin d'être installé sur votre machine.

---

## Exécuter avec Docker {#run-with-docker}

Une image contient tout ce que l'atelier sert : l'application du navigateur, l'API, les mises à jour en direct et un checkout ACT épinglé.

```bash
cp .env.example .env                      # optional settings (port, image tag, Gurobi, AI key)
scripts/docker_build.sh                   # stage the pinned ACT commit, then docker compose build
docker compose up -d                      # CPU; open http://127.0.0.1:8080
docker compose -f compose.yaml -f compose.gpu.yaml up -d      # NVIDIA GPU
```

- **Port.** L'atelier écoute uniquement sur `127.0.0.1:${ACT_GUI_PORT:-8080}`. Si le port 8080 est déjà utilisé, définissez `ACT_GUI_PORT`. Pour y accéder depuis d'autres machines, placez-le derrière HTTPS et un proxy d'authentification.
- **Source ACT.** `scripts/docker_build.sh` lit le commit ACT épinglé dans `fixtures/catalog.json` et le récupère depuis `$ACT_SOURCE`, qui est par défaut un checkout local ou peut être une URL git.
- **Benchmarks et jeux de données.** **Load model** construit les modèles depuis les répertoires `data/` et `literature/` d'ACT, qui ne sont pas inclus dans l'image. Montez-les en lecture seule avec `-f compose.actdata.yaml`. Sans eux, le catalogue reste fonctionnel.
- **Persistance.** Les enregistrements, les modèles construits et les licences importées sont conservés dans le volume `act-gui-data`.
- **Gurobi (facultatif).** Importez `gurobi.lic` dans l'onglet **Engine**, ou montez-le avec `GUROBI_LICENSE_FILE` et `-f compose.gurobi.yaml`. Consultez la [configuration](./configuration#gurobi).

---

## Configuration de développement {#development-setup}

```bash
# once
uv venv --python "$(conda run -n act-py312 which python)" --system-site-packages .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-dev.txt
npm install

# run (ACT_ROOT defaults to /data1/guanqin/ACT)
./scripts/dev.sh
# then open http://127.0.0.1:5173
```

`dev.sh` démarre le service API sur `127.0.0.1:18765` et le serveur de développement Vite sur `127.0.0.1:5173`, qui transmet `/api` au service. Les deux n'écoutent que sur l'interface locale. Sur une machine distante, transférez le port avec `ssh -L 5173:127.0.0.1:5173 <host>`.

### Vérifications

```bash
.venv/bin/python -m pytest      # bridge parity against real ACT + service tests
npm test                        # browser tests (vitest)
npm run typecheck               # TypeScript
npm run check:types             # generated wire types match the Python schemas
```

Suite : [Fonctionnement](./how-it-works).
