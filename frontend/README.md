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
npm run format        # Formater les fichiers avec Prettier
npm run format:check  # Vérifier le formatage sans modifier les fichiers
```

## Démo option A (données et photos réelles)

La page d’accueil reproduit le parcours de la démo Gradio. Le contrat vient du bucket : `derived/propositions/*.csv` et les deux `photos.csv`. Aucun `.npy`, modèle ou calcul de cosinus n’est lu dans le frontend.

Variables serveur requises, à renseigner hors du dépôt (Clever Cloud en production) : `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. `DEMO_PROPOSITIONS_KEY` permet de figer le CSV de propositions ; sinon le dernier nom de fichier par ordre lexicographique est utilisé. Les livraisons `best_of` et `catalogue` viennent des colonnes du CSV.

Après `npm run dev` :

- `/` : choix d’un individu, photos du best-of, 10 candidats et catalogue paginé par 12 ;
- `/?individu=IND2&page=2` : lien direct vers un individu et une page du catalogue ;
- `/api/demo` : contrat JSON avec `Cache-Control: no-store` ;
- `/api/demo/photos/<imageId>` : photo résolue côté serveur depuis le bucket. Un identifiant inconnu renvoie 404, une photo absente du bucket renvoie 503. Aucun chemin `curated/` n’apparaît dans l’URL ni dans la réponse.

Reproduction manuelle rapide :

1. comparer `/api/demo` avec `derived/propositions/<best_of>.csv` : mêmes individus, mêmes candidats et scores arrondis à 2 décimales ;
2. vérifier que `IND2` arrive avant `IND10`, et que `?page=99` ramène à la dernière page ;
3. vérifier qu’aucun chemin `curated/` ni `fichier_origine` n’apparaît dans le JSON ;
4. retirer une variable S3 : la page affiche un message d’erreur sans endpoint ni bucket ;
5. ouvrir une vignette depuis la page : l’en-tête `Content-Type` est `image/jpeg` ou `image/png`, et `Cache-Control: private, no-store` ;
6. ouvrir `/api/demo/photos/inconnu` : la route renvoie 404.

Le style wireframe est uniquement dans `src/app/globals.css`, importé par `src/app/layout.tsx`. Supprimer cet import suffit à retirer tout le style sans modifier la structure JSX.

### Authentification

Comme la démo Gradio, l’accès est ouvert tant que `DEMO_PASSWORD` est absent. Définir `DEMO_USER` (par défaut `miraceti`) et `DEMO_PASSWORD` côté serveur protège la page et les routes `/api/demo/*` en Basic Auth. Ces variables restent hors du dépôt et ne sont jamais préfixées `NEXT_PUBLIC_`.

Vérification manuelle : avec les variables définies, `curl -i http://localhost:3000/` renvoie `401` et un en-tête `WWW-Authenticate` ; `curl -u miraceti:<mot-de-passe> -i http://localhost:3000/api/demo` renvoie `200` avec `Cache-Control: no-store`.

Limites connues : pas d’explicabilité et aucun calcul ML dans le frontend. Les photos sont streamées via la route API, sans URL signée ni cache public.

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

## Remarques

- Le fichier `.env` local ne doit pas être commité. Les variables de déploiement Clever Cloud se configurent côté Clever Cloud, pas dans le repo.
- En cas de souci de déploiement, vérifier d’abord : `APP_FOLDER`, la commande `start`, la version Node, le hook de build et les logs Clever Cloud.
