# dorsalmatch

La lib ML de Cétolog. Pour une photo de nageoire dorsale, elle calcule une empreinte et cherche les plus proches. Elle ne connaît ni le bucket ni l'interface : elle reçoit des images et renvoie des vecteurs et des indices.

La chaîne expliquée avec le schéma, les résultats et les pistes : [docs/cetolog_ml](../docs/cetolog_ml/README.md).

## Utilisation

```bash
uv sync --group ml
```

```python
import dorsalmatch

embedder = dorsalmatch.Embedder("cetaceanet")

catalogue = embedder.embed(["a.jpg", "b.jpg"])  # une ligne par photo
query = embedder.embed(["nouvelle.jpg"])

dorsalmatch.search(query, catalogue, k=2)       # [[[indice, cosinus], [indice, cosinus]]]
```

| Fonction | Rôle |
|---|---|
| `Embedder(nom).embed(photos)` | Les empreintes, vecteurs de norme 1. Une photo est un chemin ou une image PIL |
| `search(requêtes, catalogue, k)` | Les k photos les plus proches du catalogue |
| `neighbors(empreintes, k)` | Les k plus proches de chaque photo parmi les autres |
| `evaluate(empreintes, dauphins)` | Top-1, top-5, top-10 et mAP |
| `pairs(empreintes, dauphins)` | Cosinus entre photos du même dauphin, puis de dauphins différents |

Les empreintes sont de norme 1 : le cosinus entre deux empreintes est un simple produit scalaire. Plus il est proche de 1, plus les photos se ressemblent pour le modèle.

`search` et `neighbors` sont le k-NN exact de scikit-learn, en distance cosinus : chaque photo est comparée à tout le catalogue, rien n'est approché.

## Les modèles

Utilisés tels quels, sans réentraînement. Les poids sont téléchargés depuis le Hugging Face Hub au premier usage, puis gardés en cache.

| Nom | Modèle | Empreinte | Poids |
|---|---|---|---|
| `cetaceanet` | EfficientNetV2-M, solution gagnante de Kaggle Happywhale | 688 nombres | `Saving-Willy/cetacean-classifier` |

**Ajouter un modèle :** un fichier dans [`models/`](models), avec son réseau et son prétraitement, puis une ligne dans `MODELS` ([`models/__init__.py`](models/__init__.py)).

Les deux pièges de CetaceaNet, réglés dans [`models/cetaceanet.py`](models/cetaceanet.py) : les bons poids sont dans `last.ckpt` (le `model.safetensors` donne des empreintes presque identiques d'un dauphin à l'autre), et les photos se normalisent avec une moyenne et un écart-type de 0,5, pas avec les valeurs ImageNet.

## Résultats

Les résultats sont dans [le notebook](../notebooks/metriques_catalogue.ipynb) : c'est la mesure de référence pour comparer les modèles. Il cherche chaque photo de l'historique dans le catalogue, avec la même fonction que la pipeline, et met de côté les photos que le catalogue a reprises.

Les photos sont utilisées telles quelles, sans recadrage automatique : elles sont déjà cadrées par Miraceti.

## Limites

- 50 dauphins seulement.
- Tous les dauphins de l'historique sont déjà au catalogue : la détection des nouveaux individus ne peut pas encore être mesurée.
- Il reste à vérifier que ces photos n'ont pas servi à entraîner CetaceaNet.
- Les versions des poids ne sont pas figées.

## Crédits

- La solution gagnante de Kaggle Happywhale : knshnb et charmq (Preferred Dolphin). Poids : [Saving-Willy/cetacean-classifier](https://huggingface.co/Saving-Willy/cetacean-classifier), licence Apache-2.0.
- Les pièges de CetaceaNet ont été décrits par The Dolphin Project dans [`happywhale`](https://github.com/The-Dolphin-Project/cetamatch/tree/main/happywhale).
