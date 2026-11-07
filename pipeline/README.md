# pipeline

Les commandes de la pipeline. Ce qu'elle fait, comment et ce qui reste sont dans [docs/cetolog_pipeline](../docs/cetolog_pipeline/README.md).

## Avant de commencer

Installe le projet et crée ton `.env` avec le [README principal](../README.md). Les commandes se lancent depuis la racine du dépôt.

## Lancer

Deux commandes, et `storage` pour le bucket :

| Commande | Quand | Ce qu'elle fait |
|---|---|---|
| `pipeline.bootstrap` | **Dormant** : une fois, puis à chaque nouvelle version du catalogue | Construit la référence : le catalogue et ses empreintes |
| `pipeline.run` | **À chaque best-of** livré par Miraceti | Le best-of, ses empreintes et ses propositions : les 10 dauphins du catalogue les plus ressemblants pour chaque individu |

**1. Récupérer les données** : copie `raw/` du bucket dans `data/raw/`, en sautant ce qui est déjà là.

```bash
uv run python -m pipeline.storage pull
```

Sans accès au bucket, copie les zips dans `data/raw/catalogue/` et `data/raw/best_of/`, nommés `AAAA-MM-JJ_<nom>.zip`.

**2. Construire le catalogue**, une seule fois :

```bash
uv run --group ml python -m pipeline.bootstrap
```

**3. Traiter les best-of** :

```bash
uv run --group ml python -m pipeline.run
```

Résultat : `data/derived/propositions/<best_of>.csv`, une ligne par candidat (`individu`, `rang`, `candidat`, `score`, `cosinus_D`, `cosinus_G`). Le premier lancement télécharge les poids de CetaceaNet. Tout ce qui est déjà fait est sauté : on peut relancer sans risque.

**4. Envoyer dans le bucket** : `curated/` puis `derived/`, sans rien écraser et sans toucher à `raw/`.

```bash
uv run python -m pipeline.storage push
```

## Les fichiers

| Fichier | Rôle |
|---|---|
| `bootstrap.py` | Dormant : le catalogue, du zip aux empreintes |
| `run.py` | Le quotidien : un best-of, du zip aux propositions |
| `storage.py` | Se connecter au bucket, `pull` et `push` |
| `photos/manifest.py` | Les outils communs : du zip à `data/curated/`, manifeste et anomalies |
| `photos/catalogue.py` | Lire les noms du catalogue : `DD_TUTR0001_…` |
| `photos/best_of.py` | Lire les noms d'un best-of : `IND3/D_3_20230307_…` |
| `embeddings.py` | Les empreintes d'un type de livraison |
| `propositions.py` | Pour chaque individu d'un best-of, les dauphins du catalogue les plus ressemblants |
