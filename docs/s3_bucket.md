# Bucket S3

`cetolog-data` stocke les données de Cétolog. Il est hébergé sur Clever Cloud (Cellar).

Le dossier local `data/`, jamais commité, en est la réplique : mêmes dossiers, mêmes chemins.

## Structure

```text
cetolog-data/
├── raw/
│   ├── photos/
│   └── observations/ # partie 2 : portail de données, à définir
└── curated/
    ├── photos/
    └── manifests/
```

## Catalogue des données

| Donnée | Chemin | Format | Créée par |
|---|---|---|---|
| Photos livrées | `raw/photos/<livraison>_photos.zip` | Zip, un dossier par dauphin | Dépôt à la main |
| Observations | `raw/observations/` | CSV, Excel | À définir (API ?) |
| Photos prêtes | `curated/photos/<livraison>/<dauphin>/` | JPG, PNG | Script 1, puis `push` |
| Manifestes | `curated/manifests/<livraison>.csv` | CSV, une ligne par photo | Script 1, puis `push` |

## Le manifeste

| Colonne | Contenu |
|---|---|
| `livraison` | Nom de la livraison, lu dans celui du zip |
| `fichier_origine` | Nom du fichier livré |
| `individu` | Identifiant du dauphin, lu dans le nom du dossier |
| `cote` | `D` pour droit, `G` pour gauche |
| `date_nom` | Date lue dans le nom du fichier |
| `date_exif` | Date lue dans les métadonnées de la photo |
| `largeur`, `hauteur` | Taille de la photo, en pixels |
| `sha256` | Empreinte du fichier, pour repérer les doublons |
| `anomalies` | Écarts au format attendu, notés sans être corrigés |

## Règles

- `raw/` ne se modifie jamais : une correction est une nouvelle livraison.
- Une livraison se nomme `AAAA-MM-JJ_<source>`, par exemple `2026-10-29_miraceti`.
- Tout ce qui est dans `curated/` peut être reconstruit depuis `raw/`.
- Le bucket reste privé, et ses données ne vont pas dans Git.
