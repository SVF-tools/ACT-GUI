# Vérification et tests

ACT peut prouver une propriété, chercher un contre-exemple ou contrôler un autre vérificateur. Chaque tâche a sa propre commande ; toutes acceptent `--device {cpu,cuda,gpu,mps}` et `--dtype {float32,float64}`.

| Tâche | Commande | Résultats possibles |
| --- | --- | --- |
| [Vérification](#verification) | `python -m act.back_end --verify` | certified, falsified, unknown, timeout |
| [Séparation-évaluation](#branch-and-bound) | `python -m act.back_end --verify --bab` | certified, falsified, unknown, timeout |
| [Fuzzing](#fuzzing) | `python -m act.pipeline --fuzz` | contre-exemples trouvés, ou aucun |
| [Exécutions sur benchmark](#benchmark-runs) | `python -m act.pipeline --verify vnnlib` | un résultat par instance |
| [Validation des vérificateurs](#verifier-validation) | `python -m act.pipeline --verify ... --validate-soundness` | réussite, échec ou non concluant pour chaque contrôle |

---

## Vérification {#verification}

La vérification en une passe propage les bornes une seule fois et décide la propriété à partir d'elles.

```bash
# un ACT Net d'exemple (--list-examples affiche les noms générés)
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu

# un réseau ONNX avec une propriété VNN-LIB ; --save-net conserve le Net vérifié
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib \
  --solver torchlp --save-net verified.json --device cpu --dtype float64
```

- **`--solver`** choisit le moteur : `torchlp` (LP en PyTorch), `dual`, `hybridz`, `gurobi` (MILP/LP, licence requise) ou `auto`.
- **`--tf-mode`** choisit la fonction de transfert avant, `interval` ou `hybridz`.
- **`--timeout`** fixe le budget de temps en secondes.
- Un fichier VNN-LIB à plusieurs disjonctions est vérifié comme plusieurs Nets : `verified.d0.json`, `verified.d1.json`, etc.

---

## Séparation-évaluation {#branch-and-bound}

La séparation-évaluation (branch-and-bound) raffine une propriété que la vérification en une passe laisse indécise. Elle découpe le problème, borne chaque sous-problème par lots et s'arrête lorsque chaque branche est décidée, qu'un contre-exemple est trouvé ou que le budget est épuisé.

```bash
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --bab --device cpu
```

| Option | Valeurs |
| --- | --- |
| `--bab-solver-tier` | `lp`, `dual`, `dual_alpha`, `dual_alpha_eta` |
| `--bab-branching` | le choix de la prochaine découpe, par exemple `babsr`, `fsb`, `gain`, `width` ou `random` |
| `--bab-bounding` | les sous-problèmes développés en premier, par exemple `greedy` ou `depth_bound_blend` |
| `--bab-max-depth`, `--bab-max-subproblems` | limites de la recherche |

Les configurations BaB nommées (préréglages) se trouvent dans `act/config/backend.yaml` ; voir [Configuration](./configuration#configuration-files).

---

## Fuzzing {#fuzzing}

ACTFuzzer cherche des entrées qui violent la propriété. Il exécute le modèle concret sur GPU par lots, fait muter les entrées à l'intérieur de la spécification d'entrée et confronte chaque candidate à la propriété de sortie.

```bash
python -m act.pipeline --fuzz --category acasxu_2023 --iterations 5000
python -m act.pipeline --fuzz --creator torchvision --dataset MNIST
```

- **Mutations.** Cinq stratégies, dosées par `--mutation-weights` : `gradient` (un pas de type FGSM), `pgd` (pas PGD itératifs et projetés), `activation` (à la DeepXplore, cible les neurones peu activés), `boundary` (échantillonne près du bord de la spécification d'entrée) et `random` (bruit gaussien).
- **Taille des perturbations.** `--perturb-mode adaptive_scalar` (une échelle adaptative), `adaptive_perdim` (une échelle par dimension d'entrée) ou `fixed`, avec `--perturb-scale`.
- **Couverture.** Les entrées qui activent de nouveaux neurones sont conservées comme graines (`--coverage-strategy`, `--activation-threshold`).
- **Budget.** `--iterations`, `--timeout` et `--stop-on-first-violation`.
- **Sortie.** Les contre-exemples et un résumé sont enregistrés dans le répertoire de sortie (`--output` ; `--no-save` pour ne rien enregistrer).

Le fuzzing ne peut pas prouver une propriété : s'il ne trouve rien, la propriété reste unknown.

---

## Exécutions sur benchmark {#benchmark-runs}

Exécutez le vérificateur de bout en bout sur un benchmark téléchargé :

```bash
python -m act.pipeline --download acasxu_2023
python -m act.pipeline --verify vnnlib --category acasxu_2023 --max-instances 10
python -m act.pipeline --verify torchvision --dataset MNIST
```

`--tf-modes` et `--solvers` choisissent le domaine et le solveur ; une exécution utilise la première valeur de chacun.

---

## Validation des vérificateurs {#verifier-validation}

La validation contrôle qu'un vérificateur est correct et numériquement juste, sur les réseaux d'exemple générés par ACT ou sur un benchmark.

```bash
python -m act.pipeline --verify netfactory --validate-soundness --device cpu --dtype float64
python -m act.pipeline --verify netfactory --validate-soundness --tf-modes interval --solvers torchlp
python -m act.pipeline --verify vnnlib --category acasxu_2023 --validate-soundness
```

1. **Niveau 1 : correction.** Des contre-exemples concrets sont confrontés au verdict de chaque solveur. Un résultat `CERTIFIED` en présence d'un vrai contre-exemple est un défaut de correction.
2. **Niveau 2 : précision numérique.** Des entrées échantillonnées traversent le modèle concret, et les bornes abstraites de chaque couche doivent contenir les activations concrètes.

`--verify torch2act` et `--verify act2torch` contrôlent les conversions entre modèles PyTorch et ACT Nets.

Suite : [Configuration](./configuration).
