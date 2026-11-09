# Le faire évoluer

D'autres modèles à tester, d'autres étapes à implémenter. Pour chacune : la brancher, la mesurer avec [le notebook](../../notebooks/baseline_ml.ipynb) sur les mêmes photos, et comparer à CetaceaNet.

## D'autres modèles

| Modèle | Poids | Où le brancher |
|---|---|---|
| MiewID | `conservationxlabs/miewid-msv3` | [`models/miewid.py`](../../dorsalmatch/models/miewid.py), en `TODO` |
| MegaDescriptor-L-384 | `BVRA/MegaDescriptor-L-384` | [`models/megadescriptor.py`](../../dorsalmatch/models/megadescriptor.py), en `TODO` |

Un modèle se branche avec son réseau et son prétraitement, comme [`cetaceanet.py`](../../dorsalmatch/models/cetaceanet.py), puis une ligne dans `MODELS` ([`models/__init__.py`](../../dorsalmatch/models/__init__.py)).

## D'autres étapes

Les pistes du bas du schéma et de la feuille de route :

| Piste | Objectif | Outils | Où |
|---|---|---|---|
| Recherche affinée | Chercher sur les deux côtés et regrouper par dauphin | | fait, dans [`propositions.py`](../../demo/propositions.py) |
| Re-ranking | Réordonner les candidats | ALIKED, LightGlue | après le top 10 |
| Top 10 expliqué | Montrer les zones qui justifient une proposition | Grad-CAM, LightGlue | la démo [`demo/app.py`](../../demo/app.py) |
| Nouveaux individus | Repérer un individu sans candidat assez proche | | [`propositions.py`](../../demo/propositions.py) |
| Validation humaine | Choisir un dauphin ou créer un identifiant | | [vers une base de données](../cetolog_pipeline/bdd.md) |
| Ajout à l'index | Rendre une photo validée cherchable aussitôt | | une nouvelle version du catalogue et de ses empreintes |
| Réentraînement | Adapter le modèle si le catalogue a grossi | | seulement si besoin |
| Contrastive learning : unsupervised | | | |
