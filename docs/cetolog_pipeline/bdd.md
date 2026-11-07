# Vers une base de données

![Les données qu'on a déjà : la pipeline et ses fichiers, ceux de Miraceti dont QGIS, puis une base de données et une couche gold à construire](../assets/cetolog_donnees.png)

Le schéma se modifie dans [cetolog_donnees.excalidraw](../assets/cetolog_donnees.excalidraw), à ouvrir sur [le tableau Excalidraw de Data For Good](https://tableau.services.dataforgood.fr/).

L'idée : les fichiers de la pipeline, ceux de Miraceti et leur projet **QGIS** (dont on ne connaît pas encore le contenu) vont dans **une base de données**. De là, une **couche gold** valorise la donnée : la carte des observations, le suivi de chaque dauphin, des statistiques.

C'est la suite des couches de `data/` : `raw/` → `curated/` → `derived/` → base → gold.

**Où on en est :** le schéma de la base reste à concevoir, à partir des fichiers ci-dessus.
