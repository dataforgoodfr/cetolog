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
