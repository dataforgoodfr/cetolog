# Frontend Cetolog (`frontend/`)

Application web **Next.js** (TypeScript, App Router) du projet Cetolog.

## Prérequis

- [Node.js](https://nodejs.org/) (version LTS recommandée)
- `npm`

## Installation et lancement en local

Depuis le dossier `frontend/` :

```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Ouvrir [http://localhost:3000](http://localhost:3000) dans le navigateur.

## Commandes utiles

```bash
npm run dev           # Serveur de développement (http://localhost:3000)
npm run build         # Build de production
npm run start         # Serveur de production (après build), écoute sur 0.0.0.0:$PORT
npm run lint          # Vérification ESLint
npm test              # Tests de composants (Vitest + Testing Library)
npm run test:watch    # Tests en mode watch
npm run format        # Formater les fichiers avec Prettier
npm run format:check  # Vérifier le formatage sans modifier les fichiers
```

## Variables du catalogue

Toutes les variables sont **serveur uniquement** : aucune ne porte le préfixe `NEXT_PUBLIC_*`, et aucune n'est passée en prop à un Client Component.

| Variable                | Usage                                   |
| ----------------------- | --------------------------------------- |
| `DATABASE_URL`          | Lecture seule du catalogue via `pg`     |
| `S3_ENDPOINT_URL`       | Point d'accès du stockage des vignettes |
| `S3_REGION`             | Région du stockage                      |
| `S3_BUCKET`             | Bucket des vignettes                    |
| `AWS_ACCESS_KEY_ID`     | Identifiants de lecture du stockage     |
| `AWS_SECRET_ACCESS_KEY` | Identifiants de lecture du stockage     |

En local, `.env.local` est un lien symbolique vers le `.env` racine, déjà ignoré par Git. Aucune valeur n'est versionnée : sur Clever Cloud, les variables se posent avec `clever env set NOM valeur`, en dehors du repo.

## Déploiement sur Clever Cloud

### 1) Installer Clever Tools

```bash
# Option recommandée (si npm est installé)
npm install -g clever-tools

# Vérifier l'installation
clever version
```

### 2) Se connecter à Clever Cloud

```bash
clever login
```

La commande ouvre le navigateur pour l’authentification. Pour vérifier le compte connecté :

```bash
clever profile
```

### 3) Lier le repo à l’application Clever Cloud

Informations de l’application **cetolog-web** :

- **Alias** : `cetolog-web`
- **ID** : `app_78d5280a-4316-48dd-90b1-4e61132eb0ab`

Depuis la racine du repo :

```bash
cd /Users/dams/Projects/cetolog
clever link app_78d5280a-4316-48dd-90b1-4e61132eb0ab
```

Vérifier le lien :

```bash
clever status
```

### 6) Déployer une branche

`clever deploy` déploie le **commit Git courant**. Pour déployer une branche, place-toi dessus, commite tes changements, puis déploie :

```bash
# Depuis la racine du repo
git checkout nom-de-ma-branche
git add .
git commit -m "mon message de commit"
clever deploy
```

Suivre les logs de déploiement :

```bash
clever logs
```

### Staging

Le catalogue est déployé sur une application dédiée, **jamais sur `cetolog-web`** (production). Créer `cetolog-web-staging`, lier le même add-on PostgreSQL en lecture, poser les variables ci-dessus, puis déployer la branche d'intégration :

```bash
clever create cetolog-web-staging --type node --org <org> --region par
clever link cetolog-web-staging
clever service link-addon <addon-postgresql>
clever deploy
```

Vérifications après déploiement : `GET /api/catalog/individuals`, une vignette en `200 image/jpeg`, la page `/catalogue` en 200, puis un aller-retour recherche → pagination → retour navigateur sans perte des filtres.

## Remarques

- Le fichier `.env` local ne doit pas être commité. Les variables de déploiement Clever Cloud se configurent côté Clever Cloud, pas dans le repo.
- En cas de souci de déploiement, vérifier d’abord : `APP_FOLDER`, la commande `start`, la version Node, le hook de build et les logs Clever Cloud.
