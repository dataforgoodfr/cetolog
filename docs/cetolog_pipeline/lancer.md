# Lancer la pipeline

Deux commandes, plus `storage` pour échanger avec le bucket. Elles se lancent toutes depuis la racine du dépôt.

| Commande | Quand | Ce qu'elle produit |
|---|---|---|
| `pipeline.bootstrap` | **Dormant** : une fois, puis à chaque nouvelle version du catalogue | Le catalogue prêt et ses empreintes : la référence |
| `pipeline.run` | **À chaque best-of** livré par Miraceti | Le best-of prêt, ses empreintes et ses propositions |

## 1. Avant de commencer

Installe le projet avec [le README principal](../../README.md), et mets les accès du bucket dans `.env` (voir [l'accès aux données](../miraceti_data/acces.md)). Le calcul des empreintes a besoin de PyTorch, dans le groupe `ml` :

```bash
uv sync --group ml
```

## 2. Récupérer les zips

```bash
uv run python -m pipeline.storage pull
```

`pull` copie `raw/` du bucket dans `data/raw/`, en sautant ce qui est déjà là. Sans accès au bucket, dépose les zips à la main :

| Zip | À mettre dans |
|---|---|
| Le catalogue | `data/raw/catalogue/AAAA-MM-JJ_catalogue_<nom>.zip` |
| Un best-of | `data/raw/best_of/AAAA-MM-JJ_bestof_<date>_<lieu>.zip` |

La date est celle de la réception. Le nom du zip devient le nom de la livraison dans toutes les couches.

## 3. Construire le catalogue : `bootstrap`

```bash
uv run --group ml python -m pipeline.bootstrap
```

Il dézippe le catalogue, écrit son manifeste, puis calcule une empreinte par photo avec CetaceaNet. Le premier lancement télécharge les poids du modèle.

**C'est un code dormant :** on ne le relance que quand Miraceti livre une nouvelle version du catalogue. Une version déjà construite est sautée.

**Pour reconstruire une version**, supprime son manifeste et ses empreintes, puis relance :

```bash
rm data/curated/catalogue/manifests/<version>.csv
```

```bash
rm -r data/derived/embeddings/catalogue/<version>
```

## 4. Traiter les best-of : `run`

```bash
uv run --group ml python -m pipeline.run
```

Pour chaque best-of de `data/raw/best_of/` : il le dézippe, calcule ses empreintes, puis le compare à **la version la plus récente du catalogue**. Le résultat :

```text
data/derived/propositions/<best_of>.csv
```

Un best-of déjà traité est sauté : on peut relancer après chaque nouvelle livraison, seuls les nouveaux sont calculés. Le format du fichier est décrit dans [comment elle marche](fonctionnement.md#le-résultat--les-propositions).

**Sans catalogue, `run` s'arrête tout de suite** et demande de lancer `bootstrap` d'abord.

## 5. Envoyer dans le bucket

> **NE JAMAIS supprimer `raw/` dans le bucket.** Ce sont les zips tels que livrés par Miraceti : la seule couche irremplaçable. Si on la perd, il faut tout redemander à Miraceti. `curated/` et `derived/` se reconstruisent avec la pipeline, `raw/` non.

```bash
uv run python -m pipeline.storage push
```

`push` envoie `curated/` puis `derived/` (empreintes et propositions), **sans rien écraser** et sans jamais toucher à `raw/`. Les photos partent avant leur manifeste : un manifeste dans le bucket veut dire que toutes ses photos y sont.

Avant d'envoyer, mets à jour [le catalogue des données](../miraceti_data/catalogue.md) si c'est une nouvelle livraison.

## Voir les propositions

Après `push`, [la démo](../cetolog_demo/README.md) affiche, pour chaque individu, ses photos à côté de celles des 10 candidats. Elle lit le bucket, pas `data/` :

```bash
uv run --group demo python -m demo.app
```

## Les pièges

- **Les commandes se lancent depuis la racine du dépôt** : les chemins `data/…` en dépendent.
- **Un résultat coupé en plein calcul est refait au prochain lancement.** Le manifeste, le `.npy` et le CSV des propositions sont écrits en dernier : un fichier présent veut dire une étape finie.
- **Un best-of déjà traité n'est pas recalculé avec un nouveau catalogue.** Pour le refaire, supprime son CSV dans `data/derived/propositions/`.
