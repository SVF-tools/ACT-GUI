---
layout: home

hero:
  name: ACT-GUI
  text: Voir l'intérieur de la vérification des réseaux neuronaux
  tagline: Un atelier dans le navigateur pour le vérificateur ACT. Chargez un réseau, testez-le par fuzzing, vérifiez-le et inspectez chaque borne calculée par ACT. ACT décide, l'atelier montre pourquoi.
  actions:
    - theme: brand
      text: Ouvrir l'atelier
      link: https://app.act-online.au
    - theme: alt
      text: Démarrer
      link: /fr/guide/
    - theme: alt
      text: GitHub
      link: https://github.com/guanqin-123/ACT-GUI

features:
  - title: Fuzzing en direct
    details: Lancez le fuzzer d'ACT et observez la mise à jour des images originales, modifiées et différentielles pendant la recherche. Mettez l'exécution en pause, reprenez-la, arrêtez-la ou réglez ses paramètres pendant qu'elle s'exécute.
  - title: Vérification et BaB
    details: Lancez la vérification en un passage d'ACT avec le domaine intervalle, dual ou HybridZ, ou sa séparation et évaluation par lots. Le verdict appartient toujours à ACT.
  - title: Bornes couche par couche
    details: Parcourez les bornes enregistrées par ACT à chaque couche, comparez-les avant et après, puis projetez une boîte d'intervalle à deux coordonnées.
  - title: Des contre-exemples exploitables
    details: Chaque violation acceptée par ACT est enregistrée avec l'exécution et exportée comme témoin VNN-COMP ou comme image.
  - title: Enregistrements reproductibles
    details: Chaque exécution conserve un manifeste, un journal d'événements en ajout seul et des artefacts scellés par sha256. Exportez l'enregistrement complet sous forme de fichier zip.
  - title: N'importe quelle branche ACT
    details: Basculez le moteur vers la base épinglée ou vers une branche de n'importe quel fork d'ACT. Les fonctions non prises en charge par le moteur actif sont désactivées, avec leur raison.
---

<div class="home-demo">

![Démonstration du fuzzing ACT-GUI](../fuzzingGuide.gif)

</div>
