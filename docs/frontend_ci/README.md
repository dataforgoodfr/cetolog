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

Secrets GitHub de la CI : `CLEVER_TOKEN`, `CLEVER_SECRET` et `CLEVER_APP_ID_FRONTEND`.

**Après un changement de variable** (surtout `NEXT_PUBLIC_*`, figées au build, ou `CC_NODE_VERSION`) : un simple restart garde l'ancien build. Reconstruire avec le bouton *Re-build and restart* de la console, ou :

```bash
clever restart --without-cache --alias cetolog-frontend
```

Les nouveaux commits, eux, sont toujours reconstruits en entier.

## Où on en est

**À faire :** une adresse lisible à la place de `app-78d5….cleverapps.io`.
