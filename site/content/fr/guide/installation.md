# Installation

Il y a deux façons d'utiliser ACT.

| Vous voulez | Utilisez | Il vous faut |
| --- | --- | --- |
| Essayer tout de suite | [L'atelier en ligne](#online-workbench) | Un navigateur |
| Exécuter ACT vous-même | [Une installation locale](#local-install) | Linux, Miniconda, git (GPU CUDA facultatif) |

---

## Atelier en ligne {#online-workbench}

Ouvrez **[app.act-online.au](https://app.act-online.au)**. L'atelier exécute ACT sur son serveur ; vous n'avez rien à installer.

---

## Installation locale {#local-install}

### 1. Créer l'environnement {#_1-create-the-environment}

Installez [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install), puis clonez ACT avec ses sous-modules et créez l'environnement `act-py312` (Python 3.12 et PyTorch) :

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312
```

Lancez toutes les commandes ACT depuis la racine du dépôt.

### 2. Gurobi (facultatif) {#_2-gurobi-optional}

Gurobi n'est nécessaire que pour le solveur `gurobi` (MILP/LP). Obtenez une [licence Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/) et placez-la ici :

```bash
cp /path/to/gurobi.lic ./modules/gurobi/gurobi.lic
```

Sans licence, ACT affiche un avertissement et utilise ses autres solveurs.

### 3. Vérifier l'installation {#_3-check-the-install}

```bash
python -m act.back_end --generate --device cpu --dtype float64     # génère les réseaux d'exemple
python -m act.back_end --list-examples                              # les liste
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu
```

Chaque niveau a sa propre ligne de commande ; `--help` liste toutes les options :

```bash
python -m act.front_end --help    # jeux de données, benchmarks et spécifications
python -m act.back_end --help     # vérification et réseaux d'exemple
python -m act.pipeline --help     # fuzzing, validation et tests de conversion
```

### 4. Benchmarks et jeux de données {#_4-benchmarks-and-datasets}

ACT télécharge les benchmarks dans son répertoire `data/` à la demande.

```bash
python -m act.front_end --list                  # jeux de données TorchVision et catégories VNN-LIB
python -m act.front_end --search acas           # recherche par nom
python -m act.front_end --download acasxu_2023  # modèles ONNX et propriétés VNN-LIB
python -m act.front_end --download MNIST        # jeu de données et ses modèles recommandés
python -m act.front_end --list-downloads        # ce qui est déjà téléchargé
```

### 5. Notebooks {#_5-notebooks}

Le répertoire `ipynb/` contient de petites démonstrations, dont un [exemple de fuzzer](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_fuzzer.ipynb) et un [exemple de vérificateur](https://github.com/SVF-tools/ACT/blob/main/ipynb/vnnlib_verifier.ipynb).

Suite : [Fonctionnement](./how-it-works).
