# Cétolog

Projet Data For Good (saison 15) avec l'association Miraceti : aider à identifier les grands dauphins à partir des photos de leur nageoire dorsale.

## Le dépôt

C'est un mono-repo, avec un seul environnement `uv` à la racine.

| Dossier | Rôle | Documentation |
|---|---|---|
| `pipeline/` | Récupérer, préparer et publier les données | [README](pipeline/README.md) |
| `tests/` | Les tests | Voir [Tester](#tester) |
| `docs/` | Le fonctionnement du projet | Voir ci-dessous |
| `data/` | La réplique locale du bucket S3, jamais commitée | [Bucket S3](docs/s3_bucket.md) |

**Documentation :**
- [Pipeline de données](docs/data_pipeline.md)
- [Bucket S3 et catalogue des données](docs/s3_bucket.md)
- [Fonctionnement du ML](docs/dorsalmatch.md)

## Installer

Il faut [uv](https://docs.astral.sh/uv/). Depuis la racine du dépôt :

```bash
uv sync
```

Pour accéder au bucket, crée ton fichier `.env`, puis remplis-le avec les accès à demander à l'équipe du projet. Il ne doit jamais aller dans Git.

```bash
cp .env.example .env
```

## Lancer

Toutes les commandes se lancent depuis la racine du dépôt, avec `uv run`. Pour les données, suis le [README de la pipeline](pipeline/README.md).

## Tester

```bash
uv run pytest -q
```

Les tests n'utilisent ni `data/` ni le vrai bucket.

## Avant de commiter

Active les contrôles une fois pour toutes :

```bash
uvx pre-commit install
```

À chaque commit, ils lancent `ruff` et refusent les fichiers `.env`, les clés, les données du projet et les fichiers de plus de 5 Mo.

Pour les lancer à la main :

```bash
uvx pre-commit run --all-files
```
