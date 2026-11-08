# Configuration

Chaque réglage a une valeur par défaut. Modifiez-le en ligne de commande pour une seule exécution, ou dans un fichier de configuration pour toutes.

**Priorité :** option de ligne de commande > variable d'environnement > préréglage BaB > fichier de configuration > valeur par défaut du code.

## Périphérique et précision {#device-and-precision}

Les trois lignes de commande acceptent les deux mêmes options.

| Option | Valeurs | Par défaut |
| --- | --- | --- |
| `--device` | `cpu`, `cuda` (ou `gpu`), `mps` | un GPU CUDA s'il y en a un, sinon `cpu` |
| `--dtype` | `float32`, `float64` | `float32` |

Utilisez `float64` lorsque vous avez besoin d'un accord numérique serré, par exemple pour la validation des vérificateurs. Les variables d'environnement `ACT_DEVICE`, `ACT_DTYPE` et `ACT_SOLVER` fixent les mêmes valeurs pour toutes les exécutions du back-end.

---

## Fichiers de configuration {#configuration-files}

Les valeurs par défaut se trouvent dans `act/config/`.

| Fichier | Configure |
| --- | --- |
| `backend.yaml` | La vérification : la cascade de solveurs, les réglages TorchLP, Gurobi, HybridZ et dual, la séparation-évaluation et les préréglages BaB nommés (`bab_presets`, choisis par `backend.bab_preset`) |
| `pipeline.yaml` | Le fuzzing (itérations, budget de temps, poids des mutations, mode de perturbation, couverture), la vérification sur benchmark et la validation |
| `frontend.yaml` | La création de spécifications : epsilons, marges, types d'entrée et de sortie, et vérification de texte |
| `gen_act_net.yaml` | Les architectures des réseaux d'exemple générés |

Par exemple, les valeurs par défaut du fuzzing dans `pipeline.yaml` :

```yaml
fuzzing:
  max_iterations: 10000
  timeout_seconds: 3600.0
  perturb_mode: "adaptive_scalar"
  perturb_scale: 0.1
```

---

## Gurobi {#gurobi}

Le solveur `gurobi` a besoin d'une licence dans `modules/gurobi/gurobi.lic`. ACT l'y trouve automatiquement ; sans elle, ACT affiche un avertissement et les autres solveurs fonctionnent toujours. Les licences académiques sont gratuites chez [Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/).

---

## Chemins et journaux {#paths-and-logs}

| Chemin | Contenu |
| --- | --- |
| `data/` | Benchmarks, jeux de données et modèles téléchargés |
| `act/back_end/examples/nets/` | ACT Nets d'exemple générés |
| `act/pipeline/log/` | Journaux d'exécution, résultats de fuzzing et journal de débogage des fonctions de transfert |

---

## Options de débogage {#debugging-options}

`PerformanceOptions` (`act/util/options.py`) regroupe les indicateurs globaux de débogage pour les scripts qui appellent ACT depuis Python.

| Indicateur | Par défaut | Effet |
| --- | --- | --- |
| `debug_tf` | `True` | Journalise les bornes et contraintes de chaque couche dans `act/pipeline/log/act_debug_tf.log` |
| `debug_tf_max_constraints` | `50` | Nombre de contraintes journalisées par couche |
| `validate_constraints` | `True` | Contrôle les contraintes produites par chaque fonction de transfert |

Le journal de débogage est complété à chaque exécution et n'est jamais tourné. Désactivez `debug_tf` pour les exécutions longues ou volumineuses, sinon le journal peut remplir le disque.
