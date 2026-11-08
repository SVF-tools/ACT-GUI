# Modes de travail

Choisissez un mode dans la colonne centrale, définissez ses options et démarrez l'exécution sous la vue du réseau. Tous les modes utilisent le même cycle de vie. Chaque exécution bénéficie donc de la même isolation du worker, des événements en direct, des enregistrements et de l'export.

| Mode | Entrée ACT | Verdicts possibles |
| --- | --- | --- |
| [Fuzzing](#fuzzing) | ACTFuzzer | `falsified` ou `unknown` |
| [Verification](#verification) | `verify_once` avec intervalle, dual ou HybridZ | Verdict d'ACT |
| [BaB](#bab) | `verify_bab_batched` | Verdict d'ACT |

---

## Fuzzing {#fuzzing}

Le fuzzing recherche des entrées qui violent la spécification. Il ne peut pas prouver qu'il n'en existe aucune.

- **Options.** Chaque paramètre d'ACTFuzzer apparaît avec la valeur par défaut d'ACT et peut être modifié. Le mode de perturbation est **isotropic**, **anisotropic** ou **fixed**.
- **Lots.** Pour un modèle partagé, définissez une taille de lot afin de tester plusieurs lignes d'entrée dans une même exécution, ou sélectionnez des entrées précises.
- **Vue en direct.** Pour les modèles d'images, les images originale, modifiée et différentielle se mettent à jour pendant le fuzzing, avec la progression et la couverture.
- **Contrôle de l'exécution.** Lorsque le moteur actif le permet, vous pouvez mettre en pause, reprendre ou arrêter un fuzzing en cours, ou modifier ses paramètres. ACT indique si chaque changement a été appliqué ou refusé, et l'enregistrement conserve chaque décision.
- **Contre-exemples.** Chaque violation acceptée par ACT est enregistrée avec l'exécution. Elle est exportable comme affectation VNN-LIB ou image PNG.

---

## Verification {#verification}

Lance la vérification en un passage d'ACT avec le domaine abstrait choisi : **interval**, **dual** ou **HybridZ**.

- **Verdict.** La bannière affiche le résultat d'ACT.
- **Contre-exemple.** Une exécution `falsified` conserve le contre-exemple d'ACT, que vous pouvez exporter comme témoin VNN-COMP ou comme image.
- **Diagnostics.** Toute exécution qui atteint un worker enregistre les avertissements, les erreurs imprimées par ACT et la chaîne d'exceptions, située à la frame ACT la plus interne. L'historique affiche ces informations et propose un instantané de reproduction : un zip contenant la requête, le réseau ACT, les informations du moteur et `reproduce.py`.

---

## BaB {#bab}

Lance la séparation et évaluation par lots d'ACT, avec le même point d'entrée que la ligne de commande du pipeline ACT.

- **Résumé final.** L'onglet BaB affiche le résumé final d'ACT et les données d'observation disponibles pour l'exécution.
- **Pas encore disponible.** L'arbre de recherche, l'historique des nœuds et leurs contrôles nécessitent des événements de nœuds validés par ACT, que le moteur épinglé ne fournit pas encore. L'atelier ne reconstruit pas l'arbre lui-même.

---

## Analyse des couches

Après une exécution, parcourez les bornes d'intervalle enregistrées par ACT pour chaque couche.

- Comparez les bornes d'une couche avant et après son traitement et sélectionnez des valeurs individuelles.
- Projetez une boîte d'intervalle à deux coordonnées.
- La vue affiche uniquement les données enregistrées. Elle ne recalcule jamais les bornes dans le navigateur.

---

## Assistant

Posez une question sur la sélection actuelle, par exemple un modèle, une exécution, une couche ou une valeur. L'assistant fige ce contexte, recueille des preuves typées par l'intermédiaire des mêmes services que les vues et répond avec des citations cliquables pour accéder à l'objet cité.

Le fournisseur actuel est un espace réservé déterministe. Aucun véritable modèle de langage n'est encore connecté.

---

## Enregistrements et export

Chaque exécution conserve :

- un **manifeste** immuable avec la requête et l'instantané du moteur ;
- un **journal d'événements** en ajout seul, rejoué lors de la reconnexion du navigateur ;
- des **artefacts scellés**, chacun vérifié par son hash sha256 à chaque lecture.

L'onglet **Records** affiche la provenance et les hash. **Export** télécharge l'enregistrement complet dans un fichier zip sans chemins absolus du serveur.

Suite : [Configuration](./configuration).
