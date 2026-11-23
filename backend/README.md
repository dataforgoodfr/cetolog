# La base de Cétolog : Focus ML

Trois tables PostgreSQL, `photos`, `empreintes` et `propositions`, remplacent les fichiers de `derived/` : les `.npy`, les `photos.csv` et le CSV de propositions. La recherche devient une requête SQL, grâce à l'extension pgvector.

Les images restent dans le bucket. La base ne garde que les métadonnées, les empreintes et les résultats.

Le SQL : [`schema.sql`](schema.sql). Le contexte : [vers une base de données](../docs/cetolog_pipeline/bdd.md).

## Les tables

### `photos` : une ligne par photo

Les colonnes du [contrat du manifeste](../docs/cetolog_pipeline/contrat_manifeste.yaml), plus `id` et `jeu`.

| Colonne | Type | Rôle |
|---|---|---|
| `id` | serial, clé primaire | identifiant interne, repris par `empreintes` |
| `jeu` | text | `catalogue`, `best_of` ou `historique` : aujourd'hui, le nom du dossier |
| `livraison` | text | nom du zip, sans extension (`2026-11-06_catalogue_tt`) |
| `fichier_origine` | text | nom de la photo, tel que reçu |
| `individu` | text | `TUTR1835` dans le catalogue, `IND1` dans un best-of |
| `cote` | char(1) | `D` ou `G` |
| `date` | date, vide possible | celle du nom de fichier, à défaut celle de l'EXIF |
| `sha256` | text | empreinte du fichier : écarte les doublons |
| `anomalies` | text, vide possible | ce qui cloche |

`UNIQUE (jeu, sha256)` : une photo identique n'entre qu'une fois par jeu.

### `empreintes` : une ligne par photo et par modèle

| Colonne | Type | Rôle |
|---|---|---|
| `photo_id` | int, vers `photos.id` | la photo |
| `modele` | text | `cetaceanet`, `miewid` |
| `vecteur` | vector | l'empreinte, de norme 1 (688 nombres pour CetaceaNet) |

Clé primaire `(photo_id, modele)` : plusieurs modèles cohabitent pour la même photo.

### `propositions` : le résultat du calcul

| Colonne | Type | Rôle |
|---|---|---|
| `best_of` | text | la livraison du best-of |
| `individu` | text | l'individu provisoire (`IND1`) |
| `modele` | text | le modèle utilisé |
| `rang` | int | 1 à 10 |
| `candidat` | text | le dauphin du catalogue proposé (`TUTR0465`) |
| `score` | real | le meilleur cosinus entre ses photos et celles du candidat |
| `cosinus_d`, `cosinus_g` | real | le détail par côté |
| `calcule_le` | timestamptz | date du calcul |

Clé primaire `(best_of, individu, modele, rang)`.

## Le traitement

Chaque livraison, catalogue, best-of ou historique, suit les mêmes étapes :

1. Le zip est rangé dans `raw/`.
2. Il est dézippé vers `curated/`, et le manifeste est créé.
3. Les photos du manifeste entrent dans `photos`. `ON CONFLICT DO NOTHING` ignore les doublons.
4. Les empreintes entrent dans `empreintes`, seulement pour les photos qui n'en ont pas encore pour ce modèle.

Puis, pour un best-of :

5. Le calcul compare ses photos à celles du catalogue et écrit le top 10 dans `propositions`.

Chaque étape peut être relancée : ce qui est déjà en base est ignoré. Pour recalculer un best-of, on supprime ses lignes de `propositions`, puis on relance le calcul.

## Le calcul

Pour un individu d'un best-of, le meilleur cosinus par dauphin du catalogue, comme [la démo](../demo/propositions.py) :

```sql
SELECT c.individu AS candidat,
       max(1 - (ec.vecteur <=> eq.vecteur)) AS score
FROM photos q
JOIN empreintes eq ON eq.photo_id = q.id AND eq.modele = 'cetaceanet'
JOIN empreintes ec ON ec.modele = eq.modele
JOIN photos c      ON c.id = ec.photo_id AND c.jeu = 'catalogue'
WHERE q.jeu = 'best_of'
  AND q.livraison = '2026-11-06_bestof_20230307_sete'
  AND q.individu = 'IND1'
GROUP BY c.individu
ORDER BY score DESC
LIMIT 10;
```

`<=>` est la distance cosinus de pgvector : `1 - distance` donne le cosinus.

**Pour vérifier la bascule :** cette requête doit redonner le top 10 de `derived/propositions/2026-11-06_bestof_20230307_sete.csv`. Pour `IND1` : `TUTR0465` à 0,459, puis `TUTR0534` à 0,428.

## Les choix

- **Doublons.** `UNIQUE (jeu, sha256)` garde la première photo. Le catalogue passe de 2 457 lignes de manifeste à 2 451 photos.
- **Pas de colonne `chemin`.** Le chemin dans le bucket se recalcule : `curated/<jeu>/photos/<livraison>/<individu>/<fichier_origine>`. Changer de bucket ne touche donc pas la base.
- **Une seule colonne `date`.** Celle du nom, à défaut celle de l'EXIF, comme le contrat du manifeste.
- **`individu` en texte.** Pas encore de table des dauphins. Elle viendra avec les décisions de Miraceti.
- **Recherche exacte, sans index sur les vecteurs.** Comme le k-NN de scikit-learn aujourd'hui, et instantanée à 2 451 photos. Un index approché (HNSW) ne sert qu'à partir de quelques dizaines de milliers de photos.

## Ensuite

Sans toucher à ces trois tables, on pourra ajouter :
- les décisions de Miraceti (recapture, nouvel individu, doute) ;
- l'historique de la photo de référence de chaque dauphin ;
- les observations QGIS, pour la carte.
