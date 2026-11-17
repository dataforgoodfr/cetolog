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
catalogue = np.load(folder + "cetaceanet.npy")

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

## Expliquer un matching

[`dorsalmatch/explain.py`](../../dorsalmatch/explain.py) montre quelles zones des deux photos font le score. Il lui faut PyTorch (groupe `ml`).

| Méthode | Ce qu'elle montre | Coût sur CPU, par paire |
|---|---|---|
| Occlusion | La baisse du cosinus quand on cache chaque carré d'une grille 8 × 8, calculée en lots : la référence | environ 5 min |
| Grad-CAM | Les zones dont le gradient fait monter le cosinus : à utiliser si l'occlusion est trop lente | moins d'une minute |
| Zones réciproques | Les zones qui se désignent l'une l'autre comme les plus ressemblantes, reliées par un trait | quelques secondes |
| Courbe de suppression | Le cosinus quand on cache les zones de la carte, les plus importantes d'abord, contre un ordre au hasard. Une carte fidèle fait chuter le cosinus plus vite : son aire sous la courbe est plus basse | environ 1 min |

```python
from PIL import Image
from dorsalmatch import Embedder
from dorsalmatch.explain import explain

result = explain(
    Embedder("cetaceanet"), Image.open("a.jpg"), Image.open("b.jpg"), "occlusion"
)
result["requete"].save(
    "carte_a.jpg"
)  # aussi : candidat, liens, suppression, aire_carte, aire_hasard
```

**Revue en équipe** : 25 paires connues de l'historique (deux photos du même dauphin, du même côté), une image par paire et un `resume.csv` dans `data/derived/explications/` :

```bash
uv run --group ml python -m pipeline.explanations
uv run --group ml python -m pipeline.explanations --pairs 30 --method gradcam
```

**Dans la démo** : sous les candidats, choisir la photo, le candidat et la technique, puis « Générer l'explicabilité ». Il faut lancer la démo avec le groupe `ml` :

```bash
uv run --group demo --group ml python -m demo.app
```

## Seuil « nouveau dauphin »

Pour voir si un seuil sur le score peut repérer un dauphin absent du catalogue :

```bash
uv run --group notebook python -m pipeline.similarities
```

Chaque photo notée de l'historique est cherchée dans le catalogue, comme dans la démo. Résultat dans `data/derived/similarites/<catalogue>/` :
- `scores.csv` : par photo, le rang du bon dauphin, le score du premier candidat, et le meilleur score sans le bon dauphin (ce qu'on verrait si le dauphin était nouveau) ;
- `distribution.png` : les deux distributions et le seuil qui équilibre dauphins connus gardés et nouveaux repérés.

Avec CetaceaNet sur les photos entières, les deux distributions se chevauchent beaucoup : aucun seuil ne sépare bien. À relancer après chaque amélioration des empreintes (recadrage de la dorsale, autre modèle) pour mesurer l'effet.

Le re-ranking (query expansion, k-reciprocal) a été essayé : il n'améliorait pas le classement (top-1 de 68 % sans, 65 à 66 % avec), il a donc été retiré.
