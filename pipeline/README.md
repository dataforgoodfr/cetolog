# pipeline

Récupère les livraisons de photos, les transforme en données prêtes pour le ML, puis les publie sur le bucket.

## La logique

**`data/` est la réplique locale du bucket S3 :** mêmes dossiers, mêmes chemins. Ce dossier n'est jamais commité.

On travaille toujours en local d'abord, et on publie seulement quand le résultat est bon :

```text
S3  →  pull  →  data/raw/  →  run.py  →  data/curated/  →  push  →  S3
```

```text
data/
├── raw/
│   └── photos/<livraison>_photos.zip
└── curated/
    ├── photos/<livraison>/<dauphin>/...
    └── manifests/<livraison>.csv
```

## Avant de commencer

Installe le projet et crée ton `.env` avec le [README principal](../README.md). Les commandes se lancent depuis la racine du dépôt.

## Lancer

**1. Vérifier la connexion au bucket**

```bash
uv run python -m pipeline.storage check
```

**2. Récupérer les données**

```bash
uv run python -m pipeline.storage pull
```

`pull` copie `raw/` du bucket vers `data/raw/`, en sautant ce qui est déjà là.

Sans accès au bucket, copie le zip dans `data/raw/photos/`. Il doit être nommé `AAAA-MM-JJ_source_photos.zip`, avec un dossier par dauphin.

**3. Construire les données**

```bash
uv run python -m pipeline.photos.run
```

Le script dézippe le zip, construit le manifeste et remplit `data/curated/`. Aucune clé n'est nécessaire pour cette étape, et une livraison déjà traitée est sautée.

**4. Regarder le résultat dans `data/curated/`**

**5. Envoyer sur le bucket**

```bash
uv run python -m pipeline.storage push
```

`push` envoie uniquement `data/curated/`, sans jamais toucher à `raw/`. Ce qui existe déjà dans le bucket n'est pas écrasé.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `photos/manifest.py` | Décrire chaque photo et noter les anomalies |
| `photos/run.py` | Du zip à `data/curated/`, en local |
| `storage.py` | Se connecter au bucket, `pull` et `push` |

Le contenu du bucket est décrit dans [`docs/s3_bucket.md`](../docs/s3_bucket.md).

