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

dorsalmatch.search(query, catalogue, k=2)  # [[[indice, cosinus], [indice, cosinus]]]
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

Les deux pièges de CetaceaNet, réglés dans [`models/cetaceanet.py`](models/cetaceanet.py) : les bons poids sont dans `last.ckpt` (le `model.safetensors` donne des empreintes presque identiques d'un dauphin à l'autre), et les photos se normalisent avec les valeurs ImageNet, celles du code d'entraînement, pas avec une moyenne et un écart-type de 0,5.

## Détourage (prétraitement)

`Segmenter` isole la nageoire avant le calcul des empreintes. Il utilise U-2-Net, un détecteur d'objet saillant. Le fond devient blanc et la photo est recadrée sur l'objet. Un notebook montre son intérêt : [`remove-background-salient-object-detection`](../notebooks/remove-background-salient-object-detection.ipynb).

```python
segmenter = dorsalmatch.Segmenter()  # paramètres de segmenter.yaml
detourees = [segmenter.remove_background(photo) for photo in ["a.jpg", "b.jpg"]]
catalogue = embedder.embed(detourees)  # embed accepte des images PIL

dorsalmatch.Segmenter("mes_reglages.yaml")  # un autre fichier
dorsalmatch.Segmenter({"threshold": 0.5, "crop": False})  # ou quelques valeurs
```

| Méthode | Rôle |
|---|---|
| `mask(photo)` | Masque en niveaux de gris à la taille de la photo : 255 = objet, 0 = fond |
| `remove_background(photo)` | La photo sur fond uni, recadrée si `crop`. Rien de saillant : la photo telle quelle |

Tous les paramètres sont dans [`segmenter.yaml`](segmenter.yaml) : modèle (`u2net` ou `u2netp`), poids, taille d'entrée, carte de sortie, seuil, normalisation, rééchantillonnage du masque, couleur du fond, recadrage. Un dict ou un autre fichier ne remplace que les clés données. Une clé inconnue est refusée.

`output_index: 4` reprend la carte choisie par le notebook. Le réseau renvoie 7 cartes : la carte fusionnée (0), puis les 6 sorties latérales. Le notebook les numérote de 1 à 7 et prend « d5 ».

**Poids.** Ils ne sont pas encore sur le Hugging Face Hub. Il faut télécharger `u2net.pth` (176 Mo) ou `u2netp.pth` (4,7 Mo) depuis les liens du [README de U-2-Net](https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection), puis indiquer le chemin dans `weights.path`. Une fois les poids publiés sur le Hub, il suffira de remplacer `path` par `repo`, `filename` et `revision` (un commit figé). Le téléchargement et le cache sont alors automatiques, comme pour CetaceaNet. Les fichiers `.pth` et `.safetensors` sont acceptés.

## Fichiers vendorisés

| Fichier | Origine | Licence |
|---|---|---|
| [`models/u2net.py`](models/u2net.py) | `model/u2net.py` de [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net), commit `ac7e1c8` | Apache 2.0 |

**Ne pas modifier ce fichier.** C'est une copie conforme, avec un en-tête qui en donne l'origine. Les noms de ses attributs sont les clés des poids : un renommage ou un reformatage empêche de les charger. Ruff l'ignore (`extend-exclude` dans `pyproject.toml`) et [`tests/test_vendored.py`](../tests/test_vendored.py) vérifie son empreinte SHA-256. Pour suivre l'amont, recopier le fichier, garder l'en-tête et mettre à jour le commit et l'empreinte.

## Résultats

Les résultats sont dans [le notebook](../notebooks/baseline_ml.ipynb) : c'est la mesure de référence pour comparer les modèles. Il cherche chaque photo de l'historique dans le catalogue, avec le même classement que la démo, et met de côté les photos que le catalogue a reprises.

Les photos sont utilisées telles quelles, sans recadrage automatique : elles sont déjà cadrées par Miraceti.

## Limites

- 50 dauphins seulement dans la baseline : les 11 de Sète, passés en historique, restent à y ajouter.
- Tous les dauphins de l'historique sont déjà au catalogue : la détection des nouveaux individus ne peut pas encore être mesurée.
- Il reste à vérifier que ces photos n'ont pas servi à entraîner CetaceaNet.
- Les versions des poids ne sont pas figées.

## Crédits

- U-2-Net : Xuebin Qin et al., « U2-Net: Going Deeper with Nested U-Structure for Salient Object Detection », *Pattern Recognition*, 2020. Code [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net), licence Apache-2.0. Les poids sont publiés par les auteurs sans licence propre. Ils sont lus comme relevant de la licence du dépôt. Ils ont été entraînés sur DUTS, un jeu de données de recherche.
- Le détourage reprend le notebook Kaggle [Remove background - Salient Object Detection](https://www.kaggle.com/code/remekkinas/remove-background-salient-object-detection) de remekkinas, licence Apache-2.0.
- La solution gagnante de Kaggle Happywhale : knshnb et charmq (Preferred Dolphin). Poids : [Saving-Willy/cetacean-classifier](https://huggingface.co/Saving-Willy/cetacean-classifier), licence Apache-2.0.
- Les pièges de CetaceaNet ont été décrits par The Dolphin Project dans [`happywhale`](https://github.com/The-Dolphin-Project/cetamatch/tree/main/happywhale).
