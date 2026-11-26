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

## Démo option A (données fictives)

La page d’accueil reproduit le parcours de la démo Gradio avec des données synthétiques : aucun bucket S3, aucune photo Miraceti et aucun secret ne sont nécessaires.

Après `npm run dev` :

- `/` : choix d’un individu (`IND1`, `IND2`, `IND10`), photos du best-of, 10 candidats et catalogue paginé par 12 ;
- `/?individu=IND10&page=2` : lien direct vers un individu et une page du catalogue ;
- `/api/demo` : contrat JSON consommé par la page ;
- `/api/demo/photos/<imageId>` : vignette SVG fictive. Un identifiant inconnu renvoie 404.

Reproduction manuelle rapide :

1. vérifier que les individus sont triés `IND1`, `IND2`, `IND10` ;
2. sélectionner `IND2` : une photo sans côté est libellée `?`, et `TUTR024` est dans `reponse`, donc absent des candidats ;
3. vérifier les libellés `pas de photo gauche` sur les candidats concernés ;
4. parcourir les 2 pages du catalogue, puis ouvrir `?page=99` : la page est ramenée à `2` ;
5. ouvrir `/api/demo/photos/inconnu` : la route renvoie 404.

Le style wireframe est uniquement dans `src/app/globals.css`, importé par `src/app/layout.tsx`. Supprimer cet import suffit à retirer tout le style sans modifier la structure JSX.

Limites connues : pas de S3, pas d’authentification, pas d’explicabilité et aucun calcul ML dans le frontend. La phase 2 remplacera `src/demo/get-demo.ts` par l’adaptateur de données serveur.

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
