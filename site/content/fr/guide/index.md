# Qu'est-ce qu'ACT ?

ACT (Abstract Constraint Transformation) est un cadre de test et de vérification pour les réseaux de neurones. À partir d'un modèle et d'une spécification des entrées qu'il peut recevoir et des sorties qu'il doit produire, ACT trouve un contre-exemple, c'est-à-dire une entrée qui viole la spécification, ou prouve qu'il n'en existe aucun.

ACT est natif PyTorch et fonctionne sur CPU ou GPU. Il lit des modèles PyTorch, des réseaux ONNX et des propriétés VNN-LIB, les convertit en une représentation intermédiaire unique (l'ACT Net) et vérifie cette représentation avec plusieurs domaines abstraits et solveurs.

---

## Démarrage rapide {#quick-start}

### Essayer en ligne {#try-it-online}

L'**[atelier en ligne d'ACT](https://app.act-online.au)** exécute ACT sur un serveur : un navigateur suffit. Choisissez un modèle, puis **Fuzzing**, **Vérification** ou **BaB**, et observez les résultats d'ACT, les bornes par couche et les contre-exemples.

### Exécuter en local {#run-it-locally}

```bash
git clone --recursive https://github.com/SVF-tools/ACT.git
cd ACT
conda env create -f environment.yml
conda activate act-py312

python -m act.back_end --generate --device cpu --dtype float64              # génère les réseaux d'exemple
python -m act.back_end --verify --network act/back_end/examples/nets/mlp_plain_3x8_64x64_3962224133.json --device cpu   # en vérifie un
```

Voir [Installation](./installation) pour Gurobi et le téléchargement des benchmarks.

### Vérifier votre propre modèle {#verify-your-own-model}

```bash
python -m act.back_end --verify --onnx model.onnx --vnnlib property.vnnlib --solver torchlp --device cpu
```

---

## Résultats d'ACT {#what-act-reports}

| Résultat | Signification |
| --- | --- |
| `CERTIFIED` | La propriété est vraie pour toute entrée de la spécification. |
| `FALSIFIED` | ACT a trouvé un contre-exemple et l'a vérifié sur le modèle concret. |
| `UNKNOWN` | L'abstraction était trop grossière pour décider, et aucun contre-exemple n'a été trouvé. |
| `TIMEOUT` | Le budget de temps a été épuisé avant. |

Le fuzzing ne peut que réfuter : une exécution de fuzzing sans contre-exemple se termine en unknown, jamais en certified.

---

## Ce que prend en charge ACT {#what-act-supports}

| Domaine | Pris en charge |
| --- | --- |
| Entrées | modules PyTorch, réseaux ONNX, propriétés VNN-LIB, paires jeu de données et modèle TorchVision, modèles de texte BERT compacts |
| Spécifications d'entrée | boîte, boule L∞, polytope linéaire |
| Propriétés de sortie | robustesse top-1, robustesse avec marge, contraintes linéaires, intervalles de sortie, régions linéaires dangereuses |
| Couches | couches MLP, CNN, RNN et Transformer |
| Domaines abstraits | intervalles, HybridZ (zonotopes), dual (relaxation linéaire) |
| Solveurs | TorchLP, dual, HybridZ, Gurobi MILP/LP (licence requise) |
| Tests | fuzzing en boîte blanche, validation de la correction des vérificateurs, contrôles de conversion PyTorch ↔ ACT |

---

## Publications {#publications}

- Kaijie Liu and Yulei Sui. [Detecting Unsoundness in Neural Network Verifiers via Concrete–Abstract Consistency](https://openreview.net/forum?id=6vjnMGdx5i). AIware 2026.
- Guanqin Zhang and Yulei Sui. [Tensor-Based Batch Fuzzing with Adaptive Perturbation Scaling for Deep Neural Networks](https://arxiv.org/abs/2606.25239). ASE 2026.

ACT est distribué sous la licence GNU Affero General Public License v3.0 (AGPL-3.0).

---

## Pour continuer {#whats-next}

- **[Installation](./installation)** : installer ACT, Gurobi et les benchmarks.
- **[Fonctionnement](./how-it-works)** : les niveaux front-end, back-end et pipeline.
- **[Vérification et tests](./modes)** : vérification, séparation-évaluation, fuzzing et validation.
- **[Configuration](./configuration)** : périphériques, fichiers de configuration et options de débogage.
- **[Documentation développeur](/README)** : le code source de l'atelier en ligne (en anglais).
