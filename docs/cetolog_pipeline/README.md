# La chaîne de données de Cétolog

Ce qui doit transformer les zips de Miraceti en données prêtes pour le ML. Cette chaîne est **à construire** : `pipeline/` ne contient que l'accès au bucket, [`storage.py`](../../pipeline/storage.py).

Pour commencer, ouvre [le notebook de livraison](../../notebooks/data_livraison.ipynb) : il récupère les données et dit ce qu'on attend de chaque équipe. La qualité de ce que tu livres est ta responsabilité : à toi de définir tes contrôles et de les montrer dans ta PR.

Les données elles-mêmes (les jeux, leurs couches, leurs formats, leurs pièges) sont décrites dans [les données de Miraceti](../miraceti_data/README.md).

## Où on en est

**Disponible dans le bucket :** les zips (`raw/`), une version de référence des données prêtes (`curated/`), des empreintes et des propositions (`derived/`).

**À faire :**

- Construire la chaîne de `raw/` à `curated/` : voir [le notebook de livraison](../../notebooks/data_livraison.ipynb).
- Mettre les données qu'on a déjà dans une base : [vers une base de données](bdd.md).
