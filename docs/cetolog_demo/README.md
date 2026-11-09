# La démo de Cétolog

Pour chaque individu d'un best-of, les 10 dauphins du catalogue les plus ressemblants. **Le ML propose, Miraceti décide.** Tout est dans [`demo/app.py`](../../demo/app.py), et tout vient du bucket.

## La lancer

Il faut les accès du bucket dans `.env` (voir [l'accès aux données](../miraceti_data/acces.md)) :

```bash
uv run --group demo python -m demo.app
```

Puis ouvrir http://localhost:7860.

## La mettre en ligne sur Clever Cloud

Application Docker reliée à ce dépôt, redéployée à chaque merge sur `main`. Variables à renseigner dans la console Clever Cloud :

| Variable | Valeur |
|---|---|
| `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET` | Celles de `.env` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Celles de `.env` |
| `CC_DOCKERFILE` | `demo/Dockerfile` |
| `DEMO_PASSWORD`, `DEMO_USER` | Facultatives : sans `DEMO_PASSWORD`, la démo est ouverte à tous |

## Où on en est

**À faire :** passer de la démo au vrai outil (design, front, API), et enregistrer les décisions de Miraceti : voir [vers une base de données](../cetolog_pipeline/bdd.md).
