# Comment ça marche

Les étapes du [schéma](../assets/dorsalmatch.png), et où elles sont dans le code. Dans Cétolog, les empreintes de référence sont dans le bucket, et [la démo](../cetolog_demo/README.md) cherche et propose à partir d'elles.

| Étape | Entrée | Sortie | Code |
|---|---|---|---|
| Prétraitement | Une photo recadrée | Un tableau de 3 × 768 × 768 nombres | [`models/common.py`](../../dorsalmatch/models/common.py) |
| Modèle (CetaceaNet) | Ce tableau | Une empreinte de 688 nombres | [`models/cetaceanet.py`](../../dorsalmatch/models/cetaceanet.py) |
| Index | Les empreintes et le `photos.csv` du catalogue | Le catalogue cherchable | Les empreintes de référence, dans `derived/embeddings/` |
| Recherche k-NN | Une empreinte et l'index | Les photos les plus proches et leur cosinus | [`match.py`](../../dorsalmatch/match.py) |
| Top 10 | Les résultats de la recherche | Les 10 dauphins à présenter | [`demo/propositions.py`](../../demo/propositions.py) |

## A. Transformer : la photo devient une empreinte

**1. La photo.** Déjà recadrée par Miraceti. Le modèle ne reçoit que l'image : ni le nom du dauphin, ni la date.

**2. Le prétraitement.** La photo est mise en carré de 768 × 768, sans recadrage, et ses couleurs passent de 0-255 à -1..1. Attention : CetaceaNet attend une moyenne et un écart-type de 0,5, pas les valeurs ImageNet.

**3. Le modèle.** CetaceaNet, un EfficientNetV2-M issu de la solution gagnante de Kaggle Happywhale, utilisé tel quel. Attention : les bons poids sont dans `last.ckpt`, pas dans `model.safetensors`.

**4. L'empreinte.** 688 nombres, ramenés à une norme de 1 dans [`embedder.py`](../../dorsalmatch/embedder.py). Elles sont rangées dans `data/derived/embeddings/<jeu>/<livraison>/cetaceanet.npy`, avec `photos.csv` : ligne N = photo N.

## B. Comparer : quelles empreintes se ressemblent ?

**5-6. Le cosinus.** Chaque empreinte est une direction : plus l'angle entre deux empreintes est petit, plus le cosinus est proche de 1. Les empreintes étant de norme 1, c'est un simple produit scalaire.

**7. La carte.** Le nuage de points du schéma compresse les 688 nombres sur 2 axes : c'est une aide visuelle. La vraie recherche se fait sur les 688 nombres.

**La recherche.** `search` dans [`match.py`](../../dorsalmatch/match.py) : le k-NN exact de scikit-learn, en distance cosinus, sur les empreintes du catalogue.

## C. Résultat : ce que le ML renvoie

**8. Le top 10.** Pour chaque individu d'un best-of, [`propositions.py`](../../demo/propositions.py) compare ses droites aux droites du catalogue et ses gauches aux gauches, garde le meilleur cosinus par dauphin, puis fait la moyenne des côtés en commun. Il écrit les 10 meilleurs dans `data/derived/propositions/<best_of>.csv`.

C'est l'index, pas le modèle, qui donne le nom du dauphin.

Ce que ça donne sur nos données : [le notebook](../../notebooks/baseline_ml.ipynb).
