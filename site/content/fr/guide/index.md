# Qu'est-ce qu'ACT-GUI ?

ACT-GUI est l'atelier de visualisation et d'interaction du vérificateur de réseaux neuronaux [ACT](https://github.com/SVF-tools/ACT). ACT effectue le travail scientifique : il propage les bornes, recherche des contre-exemples et décide des verdicts. ACT-GUI permet d'observer ce travail. Il charge les modèles et les spécifications, exécute ACT, affiche les preuves produites par ACT et conserve l'enregistrement de chaque exécution.

Un navigateur suffit. L'atelier s'exécute sur un serveur où ACT est installé, et tous les calculs y sont réalisés.

---

## Démarrage rapide

### Ouvrir l'atelier

L'atelier hébergé est disponible à **[app.act-online.au](https://app.act-online.au)**. Pour exécuter votre propre copie, consultez l'[installation](./installation).

### Votre première exécution

1. **Choisissez un modèle.** Sélectionnez un modèle du catalogue dans la barre latérale, ou utilisez **Load model** pour en construire un à partir d'une instance de référence VNN-COMP (ONNX + VNN-LIB) ou d'un classifieur d'images ONNX avec une image de test et un epsilon.
2. **Choisissez un mode.** Les modes disponibles sont **Fuzzing**, **Verification** et **BaB**.
3. **Démarrez l'exécution.** Les contrôles se trouvent sous la vue du réseau. Le fuzzing diffuse sa progression et les images modifiées en direct. Verification et BaB affichent le verdict d'ACT à la fin.
4. **Inspectez les preuves.** Ouvrez les bornes des couches, les contre-exemples ou l'historique des exécutions. L'onglet **Records** affiche la provenance de chaque exécution et permet d'exporter l'exécution dans un fichier zip.

La commande **Guide** de la barre supérieure relance la visite introductive à tout moment.

---

## Le principe : ACT décide

L'atelier ne calcule ni ne remplace jamais un verdict.

- **Les verdicts viennent d'ACT.** L'interface affiche seulement ce qu'ACT rapporte.
- **Le fuzzing ne certifie rien.** Une exécution de fuzzing est `falsified` uniquement lorsque le vérificateur de propriétés d'ACT accepte un contre-exemple. Toutes les autres se terminent par `unknown`.
- **L'assistant explique, il ne décide pas.** Ses réponses citent les preuves enregistrées et ne remplacent jamais le résultat d'ACT.
- **Les données absentes restent absentes.** Une valeur non enregistrée par ACT est affichée comme non enregistrée, jamais complétée ni estimée.

---

## Fonctionnalités disponibles aujourd'hui

| Disponible | Pas encore disponible |
| --- | --- |
| Chargement de modèles depuis le catalogue, les instances VNN-LIB et les classifieurs ONNX | Historique et contrôles BaB au niveau des nœuds |
| Vérification avec le domaine intervalle, dual ou HybridZ, et résumés finaux de BaB | Géométrie au-delà des boîtes d'intervalles |
| Fuzzing en direct avec contrôles d'exécution et contre-exemples enregistrés | Un vrai fournisseur d'IA (l'assistant utilise un fournisseur déterministe factice) |
| Bornes d'intervalles enregistrées couche par couche | |
| Enregistrements d'exécution, diagnostics et export zip | |
| Changement de branche ACT et gestion des licences Gurobi | |

---

## Suite du parcours

- **[Installation](./installation)** : utilisez l'atelier hébergé, exécutez-le avec Docker ou préparez un checkout de développement.
- **[Fonctionnement](./how-it-works)** : découvrez comment le navigateur, le service de l'atelier et ACT se répartissent le travail.
- **[Modes de travail](./modes)** : fuzzing, vérification, BaB, analyse des couches, assistant et enregistrements.
- **[Configuration](./configuration)** : variables d'environnement, changement de moteur et Gurobi.
- **[Documentation développeur](/README)** : trouvez le module responsable du comportement à modifier.
