# demo

La démo Gradio, en un fichier : `app.py`. Pour chaque individu d'un best-of, les 10 dauphins du catalogue les plus ressemblants, lus dans le bucket. Ce qu'elle montre, comment elle marche, la mise en ligne et la suite : [docs/cetolog_demo](../docs/cetolog_demo/README.md).

## Lancer

Avec les accès du bucket dans `.env`, depuis la racine du dépôt :

```bash
uv run --group demo python -m demo.app
```

Puis ouvrir http://localhost:7860. Avec `DEMO_PASSWORD` (et `DEMO_USER`, `miraceti` par défaut), elle demande un mot de passe.

## Avec Docker

```bash
docker build -f demo/Dockerfile -t cetolog-demo .
```

```bash
docker run --env-file .env -p 8080:8080 cetolog-demo
```
