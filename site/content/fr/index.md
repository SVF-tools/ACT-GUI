---
layout: home

hero:
  name: ACT
  text: Abstract Constraint Transformation
  tagline: Un cadre de test et de vérification pour les réseaux de neurones. Chargez un modèle et une spécification, cherchez des contre-exemples et prouvez des propriétés par interprétation abstraite correcte et séparation-évaluation.
  actions:
    - theme: brand
      text: Commencer
      link: /fr/guide/
    - theme: alt
      text: Essayer en ligne
      link: https://app.act-online.au
    - theme: alt
      text: GitHub
      link: https://github.com/SVF-tools/ACT

features:
  - title: Une seule représentation pour tous les modèles
    details: Les modèles PyTorch, les réseaux ONNX et les propriétés VNN-LIB deviennent un même ACT Net, dans lequel les spécifications d'entrée et de sortie sont des couches ; chaque moteur vérifie donc le même problème.
  - title: Trois domaines abstraits
    details: Propagez des bornes par intervalles, par zonotopes HybridZ ou par bornes duales issues d'une relaxation linéaire, à travers des couches MLP, CNN, RNN et Transformer.
  - title: Séparation-évaluation
    details: Raffinez les propriétés non décidées en scindant des neurones ou des entrées, avec des sous-problèmes en lots, plusieurs heuristiques de branchement et des bornes LP, duales ou MILP.
  - title: Fuzzing en boîte blanche
    details: ACTFuzzer cherche des violations sur GPU avec des mutations guidées par le gradient, une mise à l'échelle adaptative des perturbations et la couverture des neurones.
  - title: Contre-exemples vérifiés
    details: Chaque contre-exemple, issu du fuzzing ou de la vérification, est contrôlé sur le modèle concret avec les mêmes spécifications d'entrée et de sortie avant d'être signalé.
  - title: Validation des vérificateurs
    details: Confrontez les verdicts à des contre-exemples concrets et vérifiez, couche par couche, que les bornes abstraites contiennent chaque activation concrète.
---

<div class="home-demo">

![Fuzzing ACT dans l'atelier en ligne](../fuzzingGuide.gif)

</div>
