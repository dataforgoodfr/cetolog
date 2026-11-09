# L'utiliser

## Installer

```bash
uv sync --group ml
```

PyTorch, dans le groupe `ml`, ne sert qu'à calculer les empreintes. Chercher et mesurer n'ont besoin que de numpy et scikit-learn.

## Récupérer les empreintes

Les empreintes de référence du catalogue, de l'historique et des best-of sont dans le bucket : [le notebook de livraison](../../notebooks/data_livraison.ipynb) les télécharge.

## En Python

```python
import csv
import numpy as np
import dorsalmatch

# Les empreintes déjà calculées : ligne N de photos.csv = empreinte N du .npy
folder = "data/derived/embeddings/catalogue/2026-11-06_catalogue_tt/"
photos = list(csv.DictReader(open(folder + "photos.csv")))
catalogue = np.load(folder + "cetaceanet_v2.npy")

# Une nouvelle photo
query = dorsalmatch.Embedder("cetaceanet").embed(["nouvelle.jpg"])

# Les 10 plus proches : [[indice, cosinus], ...]
for index, cosine in dorsalmatch.search(query, catalogue, k=10)[0]:
    print(photos[index]["individu"], cosine)
```

| Fonction | Rôle |
|---|---|
| `Embedder(nom).embed(photos)` | Les empreintes, une ligne par photo, de norme 1 |
| `search(requêtes, catalogue, k)` | Les k photos du catalogue les plus proches |
| `neighbors(empreintes, k)` | Les k plus proches de chaque photo parmi les autres |
| `evaluate(empreintes, dauphins)` | Top-1, top-5, top-10 et mAP, chaque photo cherchée parmi les autres |
| `pairs(empreintes, dauphins)` | Les cosinus entre photos du même dauphin, puis de dauphins différents |

## Mesurer

[Le notebook](../../notebooks/baseline_ml.ipynb) reconstruit l'historique à partir du catalogue et note la reconstruction grâce aux annotations : bon dauphin au rang 1, dans le top 10 mais plus bas, ou hors du top 10. C'est le point de départ pour comparer un autre modèle.

## Tester

```bash
uv run pytest tests/test_dorsalmatch.py
```
