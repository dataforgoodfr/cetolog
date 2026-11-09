# La démo de Cétolog

La démo montre à Miraceti ce que propose le ML : pour chaque individu d'un best-of, les 10 dauphins du catalogue qui lui ressemblent le plus. **Le ML propose, Miraceti décide.**

C'est un **one-shot** : un seul fichier, [`demo/app.py`](../../demo/app.py), fait avec [Gradio](https://www.gradio.app/). Il montre ce que fera l'outil de matching, avant qu'il soit construit pour de vrai, avec une API, un front et un back.

## Ce qu'on voit

La démo prend le dernier best-of et le compare au dernier catalogue :

1. **Un individu choisi** dans la liste : ses photos dans le best-of, et en face ses 10 candidats du catalogue, avec leur score, leur photo droite et leur photo gauche, et le cosinus de chaque côté. La démo ne dit pas lequel est le bon : c'est à Miraceti de valider.
2. **Le catalogue entier**, à parcourir page par page (12 dauphins par page), avec la photo droite et la photo gauche de chaque dauphin.

Le score est le cosinus entre les empreintes des dorsales, moyenné sur les côtés en commun : plus il est proche de 1, plus les dorsales se ressemblent.

## Comment elle marche

**Tout vient du bucket**, jamais de `data/` en local :

```text
bucket cetolog-data
 ├─ derived/embeddings/   ── au démarrage ─────────▶  les empreintes (quelques Mo)
 └─ curated/<jeu>/photos/ ── à chaque affichage ───▶  seulement les photos montrées
                                                          │
                                   propose() de demo/propositions.py
                                                          │
                                                          ▼
                                              l'interface Gradio
```

- **Le bucket doit être à jour** : la démo y lit les empreintes et les photos de la dernière livraison.
- **Les photos sont téléchargées à la demande** : le catalogue complet pèse plusieurs Go, la démo ne prend que celles qu'elle affiche.
- **Rien n'est gardé** : tout est copié dans un dossier temporaire, effacé à l'arrêt.
- **Les propositions sont calculées au démarrage** par [`propose`](../../demo/propositions.py), à partir des empreintes du bucket.

## La lancer

Il faut les accès du bucket, dans `.env` (à demander à `mandresyandri`, voir [l'accès aux données](../miraceti_data/acces.md)) :

```bash
uv run --group demo python -m demo.app
```

Puis ouvrir http://localhost:7860.

Les photos de Miraceti ne sont pas publiques : avec `DEMO_PASSWORD` (et `DEMO_USER`, `miraceti` par défaut), la démo demande un identifiant et un mot de passe.

## La mettre en ligne sur Clever Cloud

Le [`demo/Dockerfile`](../../demo/Dockerfile) construit une image de la démo : sans PyTorch, sans `data/`, sans `.env`. Elle écoute sur le port 8080, celui qu'attend Clever Cloud. Chaque image a son Dockerfile dans son dossier (la chaîne de données pourra avoir le sien), et toutes se construisent depuis la racine du dépôt, qui a le code et `uv.lock`.

1. **Créer une application Docker** sur Clever Cloud, reliée à ce dépôt.
2. **Renseigner les variables d'environnement** dans la console Clever Cloud, jamais dans l'image :

| Variable | Valeur |
|---|---|
| `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET` | Celles de `.env` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Celles de `.env` |
| `DEMO_PASSWORD` | Obligatoire en ligne |
| `DEMO_USER` | `miraceti` par défaut |
| `CC_DOCKERFILE` | `demo/Dockerfile` : le Dockerfile à construire, puisqu'il n'est pas à la racine |

3. **Déployer** depuis la console, ou avec la CLI Clever Cloud :

```bash
clever deploy
```

Pour tester l'image en local avant :

```bash
docker build -f demo/Dockerfile -t cetolog-demo .
```

```bash
docker run --env-file .env -p 8080:8080 cetolog-demo
```

## Où on en est

**Fait :**

- La démo tourne à partir du bucket, et elle est dockerisée pour Clever Cloud.

**À faire :**

- **Passer de la démo au vrai outil** : un designer pour l'expérience de Miraceti, puis un front et un back (l'API) construits dessus. La démo sert de modèle : ce qu'on montre, dans quel ordre, ce que Miraceti doit pouvoir décider.
- **Enregistrer les décisions** de Miraceti : aujourd'hui, la démo montre les candidats mais ne garde pas le choix. Voir [vers une base de données](../cetolog_pipeline/bdd.md).
