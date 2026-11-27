## Lancer l'application de review

L'application de review utilise [FiftyOne](https://docs.voxel51.com/user_guide/index.html) pour explorer visuellement les résultats du classement des photos d'historique.

### Avant de lancer : les données requises

L'application lit tout en local, dans `data/`. Il lui faut les empreintes et les photos de deux livraisons d'historique et d'un catalogue, dont les noms sont fixés dans [`ranking.py`](ranking.py) (`HISTORY_DELIVERIES` et `CATALOGUE_DELIVERY`) :

```text
data/
├── derived/embeddings/
│   ├── historique/2026-10-29_miraceti/               photos.csv + cetaceanet.npy
│   ├── historique/2026-11-06_bestof_20230307_sete/   photos.csv + cetaceanet.npy
│   └── catalogue/2026-11-06_catalogue_tt/            photos.csv + cetaceanet.npy
└── curated/
    ├── historique/photos/2026-10-29_miraceti/              ~350 Mo
    ├── historique/photos/2026-11-06_bestof_20230307_sete/  ~200 Mo
    └── catalogue/photos/2026-11-06_catalogue_tt/           ~2,5 Go
```

Sans ces dossiers, le lancement s'arrête sur une `FileNotFoundError`.

**1. Les accès au bucket** : suivre [Accéder aux données](../docs/miraceti_data/acces.md) (fichier `.env`, puis `uv run python -m pipeline.storage check`).

**2. Récupérer uniquement ce qu'il faut** (environ 3 Go), depuis la racine du dépôt :

```python
from pipeline.storage import connect

bucket = connect()  # lit .env
for prefix in (
    "derived/embeddings/historique/2026-10-29_miraceti/",
    "derived/embeddings/historique/2026-11-06_bestof_20230307_sete/",
    "derived/embeddings/catalogue/2026-11-06_catalogue_tt/",
    "curated/historique/photos/2026-10-29_miraceti/",
    "curated/historique/photos/2026-11-06_bestof_20230307_sete/",
    "curated/catalogue/photos/2026-11-06_catalogue_tt/",
):
    bucket.pull(prefix=prefix)  # saute ce qui est déjà là
```

**3. Les dépendances** : FiftyOne est dans le groupe `review`, installé par `uv sync --all-groups` (voir le README racine) ou seul avec `uv sync --group review`.

### Lancer

```bash
uv run python -m review.app
```

Cette commande charge les photos d'historique classées et leurs empreintes, puis ouvre FiftyOne sur l'interface de review avec les vues groupées par cas sur `localhost:5151`.

Voici la [documentation FiftyOne](https://docs.voxel51.com/user_guide/index.html) pour mieux comprendre les concepts de dataset, vues et filtres.

## Comparer les modèles

`review.compare` classe chaque photo d'historique notée avec les trois modèles (`cetaceanet`, `miewid`, `megadescriptor`) et montre où chacun regarde (Grad-CAM). Il faut les empreintes `<modèle>.npy` des trois modèles.

**1. Les cartes Grad-CAM** (environ 15 s par photo et par modèle sur CPU, quelques minutes en tout sur GPU). Une carte existante est sautée.

```bash
uv run --group ml python -m review.heatmaps --limit 50       # les 50 premières photos
uv run --group ml python -m review.heatmaps --model megadescriptor
```

**2. Les masques du dauphin** (U-2-Net, poids téléchargés au premier usage) :

```bash
uv run --group ml python -m review.masks
```

**3. L'application :**

```bash
uv run --group review python -m review.compare
```

Le dataset `cetolog_comparaison` a trois types de tranches :

| Tranche | Photo | Cartes |
|---|---|---|
| `requete` | la photo d'historique | `gradcam_<modèle>_bon` (contre le bon dauphin), `gradcam_<modèle>_faux` (contre le premier faux) |
| `bon` | le bon dauphin au catalogue, même côté | `gradcam_<modèle>` |
| `faux_<modèle>` | le premier faux candidat du modèle | `gradcam_<modèle>` |

Champs utiles : `<modèle>_rank`, `<modèle>_outcome`, `models_rank1` (nombre de modèles au rang 1), et `<modèle>_part_dauphin_bon` / `_faux` : part de la carte sur le dauphin ÷ part de la photo qu'il occupe (1 = hasard, au-dessus = le dauphin, en dessous = l'eau). Les vues enregistrées isolent les désaccords, par exemple « cetaceanet rang 1, megadescriptor hors top 10 ».

Sur les cartes, rouge = la zone fait monter le cosinus. Chaque carte est ramenée à son maximum.

Les tags sont gardés quand on relance (copie dans `data/derived/explications/tags_comparaison.json`) et comptés dans [`diagnostic_modeles`](../notebooks/diagnostic_modeles.ipynb) (6.5).

## Voir ce que le détourage change

`review.variants` montre chaque photo d'historique et son bon dauphin dans les cinq variantes de [`baseline_ml_v2`](../notebooks/baseline_ml_v2.ipynb), côte à côte (dataset `cetolog_detourage`). Il faut les empreintes des variantes (commandes dans le notebook).

```bash
uv run --group ml --group review python -m review.variants
```

- Les photos préparées sont enregistrées une fois dans `data/derived/variantes/`.
- `<modèle>_effet_<variante>` : gagne le rang 1, perd le rang 1, monte, descend, pareil.
- Vues enregistrées : `<modèle> · <variante> · perd le rang 1` et `... gagne le rang 1`.
- Les tags sont gardés quand on relance (copie dans `data/derived/explications/tags_detourage.json`).
