# Le frontend sur Clever Cloud

Application Node.js `cetolog-web` (organisation MIRACETI), reliée à ce dépôt et redéployée à chaque merge sur `main` par le job `deploy-frontend` de la [CI](../../.github/workflows/ci.yaml). En ligne : https://app-78d5280a-4316-48dd-90b1-4e61132eb0ab.cleverapps.io/

Variables renseignées dans la console Clever Cloud :

| Variable | Valeur |
|---|---|
| `CC_APP_FOLDER` | `frontend` |
| `CC_NODE_VERSION` | `24` |
| `CC_NODE_DEV_DEPENDENCIES` | `install` (le build a besoin de `typescript`) |
| `CC_POST_BUILD_HOOK` | `cd frontend && npm run build` (Clever Cloud ne lance pas le build seul) |
| `NODE_ENV` | `production` |
| `S3_ENDPOINT_URL` | endpoint Cellar (serveur uniquement) |
| `S3_REGION` | région du bucket |
| `S3_BUCKET` | bucket privé (valeur dans la console) |
| `AWS_ACCESS_KEY_ID` | identifiant de lecture |
| `AWS_SECRET_ACCESS_KEY` | clé de lecture |
| `DEMO_USER` | utilisateur de la démo (par défaut `miraceti`) |
| `DEMO_PASSWORD` | active l’auth basique ; sans valeur, la démo reste ouverte |
| `DEMO_PROPOSITIONS_KEY` | facultatif : figer le CSV dans `derived/propositions/` |

Si l’add-on Cellar est lié à l’app, Clever Cloud injecte `CELLAR_ADDON_HOST`, `CELLAR_ADDON_KEY_ID` et `CELLAR_ADDON_KEY_SECRET` : le frontend les accepte à la place de `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY`. La région Cellar est alors `us-east-1`. `S3_BUCKET` reste à définir, car l’add-on n’injecte pas le nom du bucket.

Ces variables ne sont jamais préfixées `NEXT_PUBLIC_` : elles sont lues uniquement par le serveur Next.js. Les valeurs de production restent dans la console Clever Cloud, pas dans le dépôt.

Secrets GitHub de la CI : `CLEVER_TOKEN`, `CLEVER_SECRET` et `CLEVER_APP_ID_FRONTEND`.

**Après un changement de variable** (surtout `NEXT_PUBLIC_*`, figées au build, ou `CC_NODE_VERSION`) : un simple restart garde l'ancien build. Reconstruire avec le bouton *Re-build and restart* de la console, ou :

```bash
clever restart --without-cache --alias cetolog-web
```

Les nouveaux commits, eux, sont toujours reconstruits en entier.

## Où on en est

**À faire :** une adresse lisible à la place de `app-78d5….cleverapps.io`.
