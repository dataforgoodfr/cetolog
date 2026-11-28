# Version BDD

La base PostgreSQL de Cétolog, et ses migrations avec [Alembic](https://alembic.sqlalchemy.org/).

Pour l'instant, la base sert l'écran « Catalogue des individus » : deux tables, `individuals` et `photos`.

## Le dossier

```
backend/
├── .env.example        ← à copier en .env (jamais versionné)
├── alembic.ini         ← configuration d'Alembic (sans URL ni mot de passe)
├── alembic/
│   ├── env.py          ← lit DATABASE_URL et models.py
│   ├── script.py.mako  ← modèle des fichiers de migration
│   └── versions/       ← les migrations, une par changement de schéma
├── models.py           ← les tables, en SQLAlchemy
└── seed_catalog.py     ← charge le catalogue en base
```

## Les tables

| Table | Une ligne = | Colonnes |
|---|---|---|
| `individuals` | un dauphin du catalogue | `id`, `code` (`TUTR0025`, unique) |
| `photos` | un fichier photo livré | `id`, `delivery`, `original_filename`, `individual_id` → `individuals.id`, `side`, `date`, `site`, `sha256` |

Les colonnes de `photos` suivent le tableau d'extraction du data contract catalogue, en anglais.

## Installer

**1. Les dépendances**, depuis la racine de la repo. `--inexact` garde les autres groupes installés :

```bash
uv sync --group db --inexact
```

**2. Le fichier `.env`**, dans `backend/` :

```bash
cp backend/.env.example backend/.env
```

Puis remplir `DATABASE_URL` avec la valeur de `POSTGRESQL_ADDON_URI` de l'add-on Clever (les accès sont à demander à mandresyandri). Pour la retrouver avec le CLI Clever :

```bash
clever addon env <addon-id> | grep POSTGRESQL_ADDON_URI
```

L'URL reste au format `postgresql://…` : SQLAlchemy 2.1 utilise psycopg par défaut.

**Toutes les commandes qui suivent se lancent depuis `backend/`.**

## Les commandes Alembic

| Pour | Commande |
|---|---|
| Voir la version de la base | `uv run --group db alembic current` |
| Voir toutes les migrations | `uv run --group db alembic history` |
| Lire le SQL d'une mise à jour, sans l'exécuter | `uv run --group db alembic upgrade head --sql` |
| Mettre la base à jour | `uv run --group db alembic upgrade head` |
| Annuler la dernière migration | `uv run --group db alembic downgrade -1` |
| Vérifier que la base et `models.py` concordent | `uv run --group db alembic check` |
| Créer une migration à partir de `models.py` | `uv run --group db alembic revision --autogenerate -m "ce qui change"` |

`alembic current` affiche `<id> (head)` quand la base est à jour.

## Changer le schéma

1. Modifier `models.py`.
2. Générer la migration :

   ```bash
   uv run --group db alembic revision --autogenerate -m "add sex to individuals"
   ```

3. **Relire le fichier créé dans `alembic/versions/`.** L'autogenerate se trompe parfois :
   - un renommage de colonne devient une suppression puis un ajout : les données de la colonne seraient perdues ;
   - les contraintes `CHECK` ne sont pas toujours détectées ;
   - aucune ligne ne doit supprimer `spatial_ref_sys` (voir « La base sur Clever »).
4. Lire le SQL, sans l'exécuter :

   ```bash
   uv run --group db alembic upgrade head --sql
   ```

5. Appliquer :

   ```bash
   uv run --group db alembic upgrade head
   ```

6. Vérifier : la commande doit répondre `No new upgrade operations detected.`

   ```bash
   uv run --group db alembic check
   ```

7. Committer `models.py` et la migration dans la même PR.

### Les règles

- **Le schéma ne change que par une migration.** Jamais de `CREATE`, `ALTER` ou `DROP` à la main.
- **Une migration fusionnée ne se modifie plus.** Pour corriger, on en écrit une nouvelle.
- **Une seule personne applique les migrations sur la base Clever**, pour que deux versions du code ne s'y croisent pas.
- **`.env` n'est jamais versionné.** L'URL contient le mot de passe.

## Charger le catalogue

`seed_catalog.py` lit le dossier `data/catalogue_20261029_miraceti/`, écrit `data/seed/individuals.csv` et `data/seed/photos.csv` pour les relire, puis remplit la base.

```bash
uv run --group db python seed_catalog.py
```

Le script s'arrête si la livraison est déjà en base.

**Pour recharger après une correction**, supprimer d'abord les photos de la livraison, puis relancer le script. `individuals` est conservée : seuls les codes manquants sont ajoutés.

```bash
set -a && source .env && set +a
```

```bash
psql "$DATABASE_URL" -c "DELETE FROM photos WHERE delivery = 'catalogue_20261029_miraceti';"
```

```bash
uv run --group db python seed_catalog.py
```

Ce rechargement ne vaut que tant qu'aucune autre table ne pointe vers `photos`.

## Interroger la base avec psql

Charger le `.env` dans le terminal, une fois par terminal :

```bash
set -a && source .env && set +a
```

Puis, par exemple :

```bash
psql "$DATABASE_URL" -P pager=off -c "\dt"
```

```bash
psql "$DATABASE_URL" -P pager=off -c "\d photos"
```

```bash
psql "$DATABASE_URL" -P pager=off -c "select (select count(*) from individuals) as individus, (select count(*) from photos) as photos;"
```

`-P pager=off` évite que psql attende une touche (`(END)` : appuyer sur `q`).

## La base sur Clever

| | |
|---|---|
| Add-on | `cetolog-db-dev`, PostgreSQL 18, région Paris |
| Offre | `dev` : 5 connexions, 256 Mo, **pas de sauvegarde** |
| Extensions déjà installées | entre autres `postgis` et `vector` (pgvector) |

- **Pas de sauvegarde** : la base se reconstruit avec `alembic upgrade head` puis `seed_catalog.py`. Quand elle contiendra des données qu'on ne peut pas recharger (validations de Miraceti), il faudra une offre avec sauvegardes.
- **PostGIS crée la table `spatial_ref_sys`.** Elle appartient à Clever : on ne peut pas la supprimer, et on n'en a pas besoin. `env.py` dit à Alembic de l'ignorer.
- **pgvector est déjà là** : les empreintes ML pourront aller en base sans rien installer.

## Dépannage

| Message | Cause | Solution |
|---|---|---|
| `KeyError: 'DATABASE_URL'` | pas de `backend/.env`, ou commande lancée ailleurs | créer `.env` et lancer depuis `backend/` |
| `No module named 'models'` | commande lancée hors de `backend/` | `cd backend` |
| `connection to server on socket "/tmp/.s.PGSQL.5432" failed` | `$DATABASE_URL` vide dans ce terminal | `set -a && source .env && set +a` |
| `too many connections` | l'offre `dev` n'en permet que 5 | fermer les psql et clients ouverts |
| `Target database is not up to date` | une migration n'est pas appliquée | `alembic upgrade head`, puis recommencer |
| La migration générée contient `drop_table('spatial_ref_sys')` | le filtre `include_object` a disparu de `env.py` | le remettre, puis régénérer |
